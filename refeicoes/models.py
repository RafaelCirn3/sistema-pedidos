from django.db import models
from uuid import uuid4
from pathlib import Path

def caminho_imagem(instance, filename):
    return f"pratos/{uuid4().hex}{Path(filename).suffix.lower()}"

class Refeicao(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    disponivel = models.BooleanField(default=True)
    imagem = models.ImageField(upload_to=caminho_imagem, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "refeição"
        verbose_name_plural = "refeições"

    def __str__(self):
        return self.nome

class OpcaoRefeicao(models.Model):
    refeicao = models.ForeignKey(Refeicao, on_delete=models.CASCADE, related_name="opcoes")
    nome = models.CharField(max_length=100)

    class Meta:
        ordering = ["id"]
        verbose_name = "opção"
        verbose_name_plural = "opções"
        constraints = [models.UniqueConstraint(fields=["refeicao", "nome"], name="opcao_nome_unico_por_prato")]

    def __str__(self):
        return self.nome
