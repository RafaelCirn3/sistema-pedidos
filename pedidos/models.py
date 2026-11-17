from django.conf import settings
from django.db import models
from refeicoes.models import Refeicao

class Status(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    ENTREGUE = "ENTREGUE", "Entregue"
    CANCELADO = "CANCELADO", "Cancelado"

class Pedido(models.Model):
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pedidos")
    refeicao = models.ForeignKey(Refeicao, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)
    entregue_em = models.DateTimeField(null=True, blank=True)
    cancelado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "criado_em", "id"])]
        constraints = [models.CheckConstraint(condition=(
            models.Q(status=Status.PENDENTE, entregue_em__isnull=True, cancelado_em__isnull=True)
            | models.Q(status=Status.ENTREGUE, entregue_em__isnull=False, cancelado_em__isnull=True)
            | models.Q(status=Status.CANCELADO, entregue_em__isnull=True, cancelado_em__isnull=False)
        ), name="pedido_status_timestamps_validos")]

    def __str__(self):
        return f"#{self.pk} — {self.refeicao}"

class HistoricoStatus(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, related_name="historico")
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status_anterior = models.CharField(max_length=10, choices=Status.choices, null=True)
    status_novo = models.CharField(max_length=10, choices=Status.choices)
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "históricos de status"
        ordering = ["-registrado_em"]
