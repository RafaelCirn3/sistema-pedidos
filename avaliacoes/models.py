from django.core.validators import MaxValueValidator
from django.db import models
from pedidos.models import Pedido

class Avaliacao(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.PROTECT, related_name="avaliacao")
    nota = models.PositiveSmallIntegerField(validators=[MaxValueValidator(5)])
    comentario = models.TextField(blank=True, max_length=1000)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "avaliação"
        verbose_name_plural = "avaliações"
        constraints = [models.CheckConstraint(condition=models.Q(nota__gte=0, nota__lte=5), name="nota_entre_zero_e_cinco")]
