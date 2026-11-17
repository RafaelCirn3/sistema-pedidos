from django.contrib import admin
from .models import Refeicao, OpcaoRefeicao
from .forms import RefeicaoForm

class OpcaoInline(admin.TabularInline):
    model = OpcaoRefeicao
    extra = 0
    max_num = 30

@admin.register(Refeicao)
class RefeicaoAdmin(admin.ModelAdmin):
    form = RefeicaoForm
    inlines = [OpcaoInline]
    list_display = ("nome", "disponivel")
    list_filter = ("disponivel",)
    search_fields = ("nome",)

@admin.register(OpcaoRefeicao)
class OpcaoRefeicaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "refeicao")
    list_filter = ("refeicao",)
    search_fields = ("nome", "refeicao__nome")
