from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

class CadastroTest(TestCase):
    def test_cadastro_e_login(self):
        dados = {"nome": "Maria da Silva", "email": "Maria@example.com", "whatsapp": "(83) 99999-9999", "senha": "M3sa!senha-forte", "is_superuser": True}
        self.assertEqual(self.client.post(reverse("cadastro"), dados).status_code, 302)
        user = User.objects.get(username="maria@example.com")
        self.assertTrue(user.check_password(dados["senha"]))
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.groups.filter(name="Cliente").exists())
        self.assertEqual(user.perfil_cliente.whatsapp, "+5583999999999")
        self.client.logout()
        self.assertEqual(self.client.post(reverse("cadastro"), dados).status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.client.post(reverse("login"), {"username": "Maria@example.com", "password": dados["senha"]}).status_code, 302)

    def test_validacao(self):
        self.assertEqual(self.client.post(reverse("cadastro"), {"nome": "Maria", "email": "email@example.com", "whatsapp": "123", "senha": "123"}).status_code, 200)
        self.assertFalse(User.objects.exists())
