from django.contrib import admin
from .models import PerfilCliente

@admin.register(PerfilCliente)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "whatsapp")
    search_fields = ("usuario__first_name", "usuario__email", "whatsapp")
