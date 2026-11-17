from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Pedido, Status
from .services import registrar, transicao
from refeicoes.models import Refeicao
from avaliacoes.models import Avaliacao

class FluxoTest(TestCase):
    def setUp(self):
        self.cliente = User.objects.create_user("cliente")
        self.outro = User.objects.create_user("outro")
        self.cozinha = User.objects.create_user("cozinha")
        for user in (self.cliente, self.outro):
            user.groups.add(Group.objects.get(name="Cliente"))
        self.cozinha.groups.add(Group.objects.get(name="Cozinha"))
        self.refeicao = Refeicao.objects.create(nome="Almoço")
        self.pedido = registrar(self.cliente, self.refeicao.pk)

    def test_cliente_cria_e_visualiza(self):
        self.client.force_login(self.cliente)
        self.assertContains(self.client.get("/"), "Almoço")
        self.client.post(reverse("novo"), {"refeicao": self.refeicao.pk, "confirmar": "sim"})
        self.assertEqual(Pedido.objects.count(), 2)
        self.assertEqual(self.pedido.historico.count(), 1)

    def test_isolamento_e_permissoes(self):
        self.client.force_login(self.outro)
        self.assertNotContains(self.client.get("/"), f"PEDIDO #{self.pedido.pk}")
        self.assertEqual(self.client.post(reverse("cancelar", args=[self.pedido.pk]), {"confirmar": "sim"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("entregar", args=[self.pedido.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("avaliar", args=[self.pedido.pk])).status_code, 404)

    def test_cancelamento_confirmado_e_estado_final(self):
        self.client.force_login(self.cliente)
        url = reverse("cancelar", args=[self.pedido.pk])
        self.assertContains(self.client.get(url), "Tem certeza")
        self.client.post(url)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.status, Status.PENDENTE)
        self.client.post(url, {"confirmar": "sim"})
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.status, Status.CANCELADO)
        self.assertIsNotNone(self.pedido.cancelado_em)
        with self.assertRaises(ValidationError):
            transicao(self.pedido, self.cozinha, Status.ENTREGUE)

    def test_entrega_avaliacao_zero_e_unicidade(self):
        self.client.force_login(self.cozinha)
        self.assertContains(self.client.get("/"), "Fila de pedidos")
        self.client.post(reverse("entregar", args=[self.pedido.pk]))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.status, Status.ENTREGUE)
        self.assertEqual(self.pedido.historico.count(), 2)
        self.client.force_login(self.cliente)
        url = reverse("avaliar", args=[self.pedido.pk])
        self.client.post(url, {"nota": 6})
        self.assertFalse(Avaliacao.objects.exists())
        self.client.post(url, {"nota": 0, "comentario": "Teste"})
        self.client.post(url, {"nota": 5})
        self.assertEqual(Avaliacao.objects.get().nota, 0)

    def test_refeicao_indisponivel(self):
        self.refeicao.disponivel = False
        self.refeicao.save()
        with self.assertRaises(ValidationError):
            registrar(self.cliente, self.refeicao.pk)

    def test_fifo(self):
        segundo = registrar(self.outro, self.refeicao.pk)
        self.client.force_login(self.cozinha)
        response = self.client.get("/")
        self.assertEqual(list(response.context["pedidos"]), [self.pedido, segundo])
        transicao(self.pedido, self.cozinha, Status.ENTREGUE)
        self.assertEqual(list(self.client.get("/").context["pedidos"]), [segundo])
        self.assertEqual(list(self.client.get(reverse("historico")).context["pedidos"]), [self.pedido])

    def test_historico_filtra_finalizados_e_avaliacoes(self):
        entregue = registrar(self.cliente, self.refeicao.pk)
        cancelado = registrar(self.cliente, self.refeicao.pk)
        avaliado = registrar(self.cliente, self.refeicao.pk)
        alheio = registrar(self.outro, self.refeicao.pk)
        transicao(entregue, self.cozinha, Status.ENTREGUE)
        transicao(cancelado, self.cliente, Status.CANCELADO)
        transicao(avaliado, self.cozinha, Status.ENTREGUE)
        transicao(alheio, self.cozinha, Status.ENTREGUE)
        Avaliacao.objects.create(pedido=avaliado, nota=0, comentario="Minha avaliação")
        url = reverse("historico")
        self.client.force_login(self.cliente)
        for filtro in ("", "ENTREGUE", "CANCELADO", "avaliados"):
            self.assertEqual(list(self.client.get("/", {"status": filtro}).context["pedidos"]), [self.pedido])
        resposta = self.client.get(url)
        self.assertEqual(list(resposta.context["pedidos"]), [avaliado, cancelado, entregue])
        self.assertContains(resposta, "Minha avaliação")
        self.assertContains(resposta, "0/5")
        self.assertContains(resposta, reverse("avaliar", args=[entregue.pk]))
        self.assertEqual(list(self.client.get(url, {"status": "avaliados"}).context["pedidos"]), [avaliado])
        self.assertEqual(list(self.client.get(url, {"status": "sem_avaliacao"}).context["pedidos"]), [entregue])
        self.assertEqual(list(self.client.get(url, {"status": "CANCELADO"}).context["pedidos"]), [cancelado])
        self.assertEqual(list(self.client.get(url, {"status": "PENDENTE"}).context["pedidos"]), [avaliado, cancelado, entregue])
        self.client.force_login(self.cozinha)
        self.assertEqual(list(self.client.get("/").context["pedidos"]), [self.pedido])
        self.assertEqual(list(self.client.get(url).context["pedidos"]), [alheio, avaliado, cancelado, entregue])
        self.assertNotContains(self.client.get(url), reverse("avaliar", args=[entregue.pk]))

    def test_historico_requer_login(self):
        self.assertRedirects(self.client.get(reverse("historico")), "/entrar/?next=/pedidos/historico/")

    def test_admin_registra_e_audita(self):
        admin = User.objects.create_superuser("admin", password="senha-teste")
        self.client.force_login(admin)
        self.assertRedirects(self.client.get("/"), "/admin/")
        response = self.client.post("/admin/pedidos/pedido/add/", {"cliente": self.cliente.pk, "refeicao": self.refeicao.pk, "_save": "Salvar"})
        self.assertEqual(response.status_code, 302)
        novo = Pedido.objects.latest("id")
        self.assertNotEqual(novo.pk, self.pedido.pk)
        self.assertEqual(novo.historico.get().responsavel, admin)
        self.client.force_login(self.cozinha)
        self.assertEqual(self.client.get("/admin/").status_code, 302)
