from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from avaliacoes.models import Avaliacao
from refeicoes.models import OpcaoRefeicao, Refeicao
from usuarios.models import PerfilCliente
from .models import HistoricoStatus, Pedido, Status
from .services import registrar, transicao


class ExclusoesAdminTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin")
        self.cliente = User.objects.create_user("cliente")
        self.cliente.groups.add(Group.objects.get(name="Cliente"))
        PerfilCliente.objects.create(usuario=self.cliente, whatsapp="+5583999990000")
        self.cozinha = User.objects.create_user("cozinha")
        self.cozinha.groups.add(Group.objects.get(name="Cozinha"))
        self.prato = Refeicao.objects.create(nome="Almoço")
        self.opcao = OpcaoRefeicao.objects.create(refeicao=self.prato, nome="Salada")
        self.pedido = registrar(self.cliente, self.prato.pk, opcoes_ids=[self.opcao.pk])
        transicao(self.pedido, self.cozinha, Status.ENTREGUE)
        self.avaliacao = Avaliacao.objects.create(pedido=self.pedido, nota=5)
        self.client.force_login(self.admin)

    def excluir_admin(self, nome_url, pk):
        url = reverse(nome_url, args=[pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 302)

    def verificar_pedido_excluido(self):
        self.assertFalse(Pedido.objects.filter(pk=self.pedido.pk).exists())
        self.assertFalse(Avaliacao.objects.filter(pedido_id=self.pedido.pk).exists())
        self.assertFalse(HistoricoStatus.objects.filter(pedido_id=self.pedido.pk).exists())

    def test_excluir_pedido_cascata(self):
        self.excluir_admin("admin:pedidos_pedido_delete", self.pedido.pk)
        self.verificar_pedido_excluido()
        self.assertTrue(Refeicao.objects.filter(pk=self.prato.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.cliente.pk).exists())

    def test_excluir_cliente_cascata(self):
        self.excluir_admin("admin:auth_user_delete", self.cliente.pk)
        self.verificar_pedido_excluido()
        self.assertFalse(PerfilCliente.objects.filter(usuario_id=self.cliente.pk).exists())
        self.assertTrue(Refeicao.objects.filter(pk=self.prato.pk).exists())

    def test_excluir_prato_cascata(self):
        self.excluir_admin("admin:refeicoes_refeicao_delete", self.prato.pk)
        self.verificar_pedido_excluido()
        self.assertFalse(OpcaoRefeicao.objects.filter(refeicao_id=self.prato.pk).exists())

    def test_excluir_cozinha_preserva_historico(self):
        self.excluir_admin("admin:auth_user_delete", self.cozinha.pk)
        self.assertTrue(Pedido.objects.filter(pk=self.pedido.pk).exists())
        self.assertTrue(Avaliacao.objects.filter(pk=self.avaliacao.pk).exists())
        self.assertIsNone(HistoricoStatus.objects.get(pedido=self.pedido, status_novo=Status.ENTREGUE).responsavel)

    def test_excluir_opcao_avaliacao_e_historico_individualmente(self):
        self.excluir_admin("admin:refeicoes_opcaorefeicao_delete", self.opcao.pk)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.opcoes_selecionadas, ["Salada"])
        self.excluir_admin("admin:avaliacoes_avaliacao_delete", self.avaliacao.pk)
        registro = self.pedido.historico.first()
        self.excluir_admin("admin:pedidos_historicostatus_delete", registro.pk)
        self.assertFalse(Avaliacao.objects.filter(pk=self.avaliacao.pk).exists())
        self.assertFalse(HistoricoStatus.objects.filter(pk=registro.pk).exists())
        self.assertTrue(Pedido.objects.filter(pk=self.pedido.pk).exists())

    def test_exclusao_em_lote(self):
        url = reverse("admin:pedidos_pedido_changelist")
        dados = {"action": "delete_selected", "_selected_action": [self.pedido.pk]}
        self.assertContains(self.client.post(url, dados), "Almoço")
        self.assertTrue(Pedido.objects.filter(pk=self.pedido.pk).exists())
        self.assertEqual(self.client.post(url, {**dados, "post": "yes"}).status_code, 302)
        self.verificar_pedido_excluido()

    def test_perfis_operacionais_nao_excluem_pedidos_pelo_admin(self):
        for user in (self.cliente, self.cozinha):
            self.client.force_login(user)
            self.assertEqual(self.client.post(reverse("admin:pedidos_pedido_delete", args=[self.pedido.pk]), {"post": "yes"}).status_code, 302)
            self.assertTrue(Pedido.objects.filter(pk=self.pedido.pk).exists())
