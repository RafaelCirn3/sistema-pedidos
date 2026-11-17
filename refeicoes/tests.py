from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from pedidos.models import Pedido
from .models import Refeicao, OpcaoRefeicao

class CardapioTest(TestCase):
    def setUp(self):
        self.cozinha = User.objects.create_user("cozinha")
        self.cozinha.groups.add(Group.objects.get(name="Cozinha"))
        self.cliente = User.objects.create_user("cliente")
        self.cliente.groups.add(Group.objects.get(name="Cliente"))
        self.prato = Refeicao.objects.create(nome="Prato")
        self.opcao = OpcaoRefeicao.objects.create(refeicao=self.prato, nome="Salada")

    def test_permissoes(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("cardapio")).status_code, 403)
        self.assertEqual(self.client.post(reverse("prato_novo")).status_code, 403)
        self.assertEqual(self.client.post(reverse("prato_editar", args=[self.prato.pk])).status_code, 403)

    def test_editar_opcoes(self):
        self.client.force_login(self.cozinha)
        url = reverse("prato_editar", args=[self.prato.pk])
        self.assertContains(self.client.get(url), "Salada")
        data = {"nome": "Almoço", "disponivel": "on", "opcoes-TOTAL_FORMS": 2, "opcoes-INITIAL_FORMS": 1,
                "opcoes-0-id": self.opcao.pk, "opcoes-0-nome": "Salada verde", "opcoes-1-nome": "Molho"}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.opcao.refresh_from_db()
        self.assertEqual(self.opcao.nome, "Salada verde")
        molho = self.prato.opcoes.get(nome="Molho")
        data.update({"opcoes-INITIAL_FORMS": 2, "opcoes-0-DELETE": "on", "opcoes-1-id": molho.pk})
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertFalse(self.prato.opcoes.filter(pk=self.opcao.pk).exists())

    def test_pedido_preserva_escolhas_e_rejeita_opcao_alheia(self):
        outro = Refeicao.objects.create(nome="Outro")
        opcao_alheia = OpcaoRefeicao.objects.create(refeicao=outro, nome="Arroz")
        self.client.force_login(self.cliente)
        self.assertContains(self.client.get("/"), "Salada")
        self.client.post(reverse("novo"), {"refeicao": self.prato.pk, "opcoes": [opcao_alheia.pk]})
        self.assertEqual(Pedido.objects.count(), 0)
        self.client.post(reverse("novo"), {"refeicao": self.prato.pk, "opcoes": [self.opcao.pk]})
        self.opcao.delete()
        self.assertEqual(Pedido.objects.get().opcoes_selecionadas, ["Salada"])
        self.client.force_login(self.cozinha)
        self.assertContains(self.client.get("/"), "Salada")

    def test_upload_foto(self):
        self.client.force_login(self.cozinha)
        buffer = BytesIO()
        Image.new("RGB", (20, 20)).save(buffer, "PNG")
        with TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            response = self.client.post(reverse("prato_novo"), {
                "nome": "Prato com foto", "disponivel": "on", "opcoes-TOTAL_FORMS": 1, "opcoes-INITIAL_FORMS": 0,
                "opcoes-0-nome": "Feijão", "imagem": SimpleUploadedFile("prato.png", buffer.getvalue(), "image/png")})
            self.assertEqual(response.status_code, 302)
            prato = Refeicao.objects.get(nome="Prato com foto")
            self.assertTrue(prato.imagem.name.endswith(".png"))
            foto = self.client.get(reverse("prato_imagem", args=[prato.pk]))
            self.assertEqual(foto.status_code, 200)
            self.assertEqual(foto["Content-Type"], "image/png")
            foto.close()
