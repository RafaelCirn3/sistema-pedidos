from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from refeicoes.models import Refeicao
from refeicoes.management.commands.seed import PRATOS
from usuarios.permissions import perfil


def foto_fake(_):
    buffer = BytesIO()
    Image.new("RGB", (20, 20)).save(buffer, "JPEG")
    return ContentFile(buffer.getvalue())


class SeedTest(TestCase):
    def test_seed_cria_perfis_pratos_e_imagens_sem_duplicar(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media), patch("refeicoes.management.commands.seed.baixar_foto", side_effect=foto_fake) as download:
            from io import StringIO
            saida = StringIO()
            call_command("seed", stdout=saida)
            self.assertEqual(User.objects.count(), 3)
            self.assertEqual(perfil(User.objects.get(username="demo-admin")), "admin")
            self.assertEqual(perfil(User.objects.get(username="demo-cozinha")), "cozinha")
            cliente = User.objects.get(username="cliente.demo@example.test")
            self.assertEqual(perfil(cliente), "cliente")
            self.assertTrue(cliente.perfil_cliente.whatsapp)
            senha = cliente.password
            self.assertEqual(Refeicao.objects.count(), 5)
            for nome, _, opcoes, _ in PRATOS:
                prato = Refeicao.objects.get(nome=nome)
                self.assertTrue(prato.imagem.storage.exists(prato.imagem.name))
                self.assertEqual(set(prato.opcoes.values_list("nome", flat=True)), set(opcoes))
            call_command("seed", stdout=StringIO())
            cliente.refresh_from_db()
            self.assertEqual(cliente.password, senha)
            self.assertEqual(User.objects.count(), 3)
            self.assertEqual(Refeicao.objects.count(), 5)
            self.assertEqual(download.call_count, 5)

    def test_seed_sem_imagens(self):
        from io import StringIO
        call_command("seed", sem_imagens=True, stdout=StringIO())
        self.assertEqual(Refeicao.objects.count(), 5)
        self.assertFalse(Refeicao.objects.exclude(imagem="").exists())

    def test_fotos_originais_disponiveis_offline(self):
        from refeicoes.management.commands.seed import baixar_foto
        with patch("refeicoes.management.commands.seed.urlopen", side_effect=AssertionError("Não deve acessar a rede")):
            for _, _, _, arquivo in PRATOS:
                with Image.open(baixar_foto(arquivo)) as foto:
                    self.assertEqual(foto.format, "JPEG")
                    self.assertLessEqual(max(foto.size), 960)
