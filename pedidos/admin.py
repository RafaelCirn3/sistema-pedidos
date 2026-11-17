from django.contrib import admin, messages
from django.core.exceptions import ValidationError, PermissionDenied
from django import forms
from django.contrib.auth import get_user_model
from refeicoes.models import Refeicao
from .models import Pedido, HistoricoStatus, Status
from .services import transicao, registrar

class PedidoAdminForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ("cliente", "refeicao")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "cliente" in self.fields:
            self.fields["cliente"].queryset = get_user_model().objects.filter(is_active=True, is_superuser=False, groups__name="Cliente").exclude(groups__name="Cozinha")
        if "refeicao" in self.fields:
            self.fields["refeicao"].queryset = Refeicao.objects.filter(disponivel=True)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    form = PedidoAdminForm
    list_display = ("id", "cliente", "refeicao", "status", "criado_em")
    list_filter = ("status", "criado_em")
    search_fields = ("cliente__username", "cliente__first_name", "refeicao__nome")
    actions = ["confirmar_entrega", "cancelar_pedidos"]
    def get_readonly_fields(self, request, obj=None):
        return ("status", "criado_em", "entregue_em", "cancelado_em") + (("cliente", "refeicao") if obj else ())
    def has_add_permission(self, request):
        return request.user.is_superuser
    def save_model(self, request, obj, form, change):
        if not change:
            pedido = registrar(obj.cliente, obj.refeicao_id, request.user)
            obj.pk = pedido.pk
            obj.criado_em = pedido.criado_em
            obj._state.adding = False
    def has_delete_permission(self, request, obj=None):
        return False
    def executar(self, request, queryset, destino):
        for pedido in queryset:
            try:
                transicao(pedido, request.user, destino)
            except (ValidationError, PermissionDenied):
                self.message_user(request, f"Pedido #{pedido.pk} não alterado.", messages.WARNING)
    @admin.action(description="Confirmar entrega dos pedidos selecionados")
    def confirmar_entrega(self, request, queryset):
        self.executar(request, queryset, Status.ENTREGUE)
    @admin.action(description="Cancelar pedidos selecionados")
    def cancelar_pedidos(self, request, queryset):
        self.executar(request, queryset, Status.CANCELADO)

@admin.register(HistoricoStatus)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "responsavel", "status_anterior", "status_novo", "registrado_em")
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
