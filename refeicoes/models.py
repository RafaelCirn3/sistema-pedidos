from django.db import models

class Refeicao(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    disponivel = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "refeição"
        verbose_name_plural = "refeições"

    def __str__(self):
        return self.nome
