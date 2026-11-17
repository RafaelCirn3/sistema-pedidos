from django.contrib import admin
from .models import Avaliacao

@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "nota", "criado_em")
    list_filter = ("nota",)
    readonly_fields = ("pedido", "nota", "comentario", "criado_em")
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
