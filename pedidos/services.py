from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from refeicoes.models import Refeicao
from usuarios.permissions import exigir, perfil
from .models import Pedido, HistoricoStatus, Status

@transaction.atomic
def registrar(cliente, refeicao_id, responsavel=None):
    exigir(cliente, "cliente")
    refeicao = Refeicao.objects.select_for_update().filter(pk=refeicao_id, disponivel=True).first()
    if not refeicao:
        raise ValidationError("Esta refeição não está mais disponível.")
    pedido = Pedido.objects.create(cliente=cliente, refeicao=refeicao)
    HistoricoStatus.objects.create(pedido=pedido, responsavel=responsavel or cliente, status_novo=Status.PENDENTE)
    return pedido

@transaction.atomic
def transicao(pedido, responsavel, destino):
    papel = perfil(responsavel)
    if destino == Status.ENTREGUE:
        exigir(responsavel, "cozinha", "admin")
    elif destino == Status.CANCELADO:
        exigir(responsavel, "cliente", "cozinha", "admin")
        if papel == "cliente" and pedido.cliente_id != responsavel.pk:
            raise ValidationError("Pedido não pertence ao cliente.")
    else:
        raise ValidationError("Transição inválida.")
    campo = "entregue_em" if destino == Status.ENTREGUE else "cancelado_em"
    alterados = Pedido.objects.filter(pk=pedido.pk, status=Status.PENDENTE).update(status=destino, **{campo: timezone.now()})
    if not alterados:
        raise ValidationError("Este pedido já foi finalizado.")
    HistoricoStatus.objects.create(pedido=pedido, responsavel=responsavel, status_anterior=Status.PENDENTE, status_novo=destino)
