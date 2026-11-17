from django.contrib import admin
from .models import Refeicao

@admin.register(Refeicao)
class RefeicaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "disponivel")
    list_filter = ("disponivel",)
    search_fields = ("nome",)
