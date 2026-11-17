from django.conf import settings
from django.db import models

class PerfilCliente(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_cliente")
    whatsapp = models.CharField(max_length=16)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username
