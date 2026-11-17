from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from avaliacoes.models import Avaliacao
from refeicoes.models import Refeicao
from usuarios.permissions import exigir, perfil
from .models import Pedido, Status
from .services import registrar, transicao
from .forms import AvaliacaoForm

def consulta(user):
    qs = Pedido.objects.select_related("cliente", "refeicao", "avaliacao")
    if perfil(user) == "cliente":
        qs = qs.filter(cliente=user)
    return qs

@login_required
def home(request):
    papel = perfil(request.user)
    if papel == "admin":
        return redirect("admin:index")
    qs = consulta(request.user).filter(status=Status.PENDENTE)
    if papel == "cozinha":
        qs = qs.order_by("criado_em", "id")
    else:
        qs = qs.order_by("-criado_em", "-id")
    pagina = Paginator(qs, 30)
    return render(request, "home.html", {"papel": papel, "pedidos": pagina.get_page(request.GET.get("page")), "refeicoes": Refeicao.objects.filter(disponivel=True).prefetch_related("opcoes"), "pendentes": pagina.count})

@login_required
def historico(request):
    exigir(request.user, "cliente", "cozinha")
    papel = perfil(request.user)
    qs = consulta(request.user).filter(status__in=[Status.ENTREGUE, Status.CANCELADO])
    contagens = {
        "entregues": qs.filter(status=Status.ENTREGUE).count(),
        "cancelados": qs.filter(status=Status.CANCELADO).count(),
        "avaliados": qs.filter(status=Status.ENTREGUE, avaliacao__isnull=False).count(),
    }
    filtros = [
        ("", "Todos"),
        ("ENTREGUE", "Entregues"),
        ("CANCELADO", "Cancelados"),
        ("avaliados", "Avaliados"),
        ("sem_avaliacao", "Sem avaliação"),
    ]
    filtro = request.GET.get("status", "")
    if filtro not in dict(filtros):
        filtro = ""
    if filtro in (Status.ENTREGUE, Status.CANCELADO):
        qs = qs.filter(status=filtro)
    elif filtro in ("avaliados", "sem_avaliacao"):
        qs = qs.filter(status=Status.ENTREGUE, avaliacao__isnull=(filtro == "sem_avaliacao"))
    qs = qs.order_by("-criado_em", "-id")
    return render(request, "historico.html", {"papel": papel, "pedidos": Paginator(qs, 30).get_page(request.GET.get("page")), "contagens": contagens, "filtro": filtro, "filtros": filtros})

@login_required
@require_POST
def novo(request):
    exigir(request.user, "cliente")
    try:
        refeicao_id = int(request.POST.get("refeicao", ""))
        opcoes_ids = set(int(i) for i in request.POST.getlist("opcoes"))
        if request.POST.get("confirmar") != "sim":
            refeicao = Refeicao.objects.filter(pk=refeicao_id, disponivel=True).first()
            if not refeicao:
                raise ValidationError("Esta refeição não está mais disponível.")
            opcoes = list(refeicao.opcoes.filter(pk__in=opcoes_ids))
            if len(opcoes) != len(opcoes_ids):
                raise ValidationError("Alguma opção não pertence a este prato ou foi removida. Atualize o cardápio.")
            return render(request, "confirmar_pedido.html", {"refeicao": refeicao, "opcoes": opcoes})
        registrar(request.user, refeicao_id, opcoes_ids=opcoes_ids)
        messages.success(request, "Pedido registrado! A cozinha já pode visualizá-lo.")
    except ValidationError as exc:
        messages.error(request, exc.message)
    except ValueError:
        messages.error(request, "Selecione uma refeição disponível.")
    return redirect("home")

@login_required
def cancelar(request, pk):
    exigir(request.user, "cliente", "cozinha")
    pedido = get_object_or_404(consulta(request.user), pk=pk)
    if request.method == "POST" and request.POST.get("confirmar") == "sim":
        try:
            transicao(pedido, request.user, Status.CANCELADO)
            messages.success(request, "Pedido cancelado.")
        except ValidationError as exc:
            messages.error(request, exc.message)
        return redirect("home")
    return render(request, "cancelar.html", {"pedido": pedido})

@login_required
@require_POST
def entregar(request, pk):
    exigir(request.user, "cozinha")
    pedido = get_object_or_404(consulta(request.user), pk=pk)
    try:
        transicao(pedido, request.user, Status.ENTREGUE)
        messages.success(request, "Entrega confirmada.")
    except ValidationError as exc:
        messages.error(request, exc.message)
    return redirect("home")

@login_required
@transaction.atomic
def avaliar(request, pk):
    exigir(request.user, "cliente")
    pedido = get_object_or_404(Pedido.objects.select_for_update(), pk=pk, cliente=request.user, status=Status.ENTREGUE)
    if Avaliacao.objects.filter(pedido=pedido).exists():
        messages.info(request, "Este pedido já foi avaliado.")
        return redirect("historico")
    form = AvaliacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        avaliacao = form.save(commit=False)
        avaliacao.pedido = pedido
        avaliacao.save()
        messages.success(request, "Obrigado pela sua avaliação!")
        return redirect("historico")
    return render(request, "avaliar.html", {"pedido": pedido, "form": form})
