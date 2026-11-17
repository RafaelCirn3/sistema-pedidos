from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
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
    qs = consulta(request.user)
    contagens = {s.lower(): qs.filter(status=s).count() for s in Status.values}
    filtro = request.GET.get("status", "")
    if filtro in Status.values:
        qs = qs.filter(status=filtro)
    if papel == "cozinha":
        qs = qs.annotate(prioridade=Case(When(status=Status.PENDENTE, then=Value(0)), When(status=Status.ENTREGUE, then=Value(1)), default=Value(2), output_field=IntegerField())).order_by("prioridade", "criado_em", "id")
    else:
        qs = qs.order_by("-criado_em", "-id")
    from django.core.paginator import Paginator
    return render(request, "home.html", {"papel": papel, "pedidos": Paginator(qs, 30).get_page(request.GET.get("page")), "refeicoes": Refeicao.objects.filter(disponivel=True).prefetch_related("opcoes"), "contagens": contagens, "filtro": filtro, "status_choices": Status.choices})

@login_required
@require_POST
def novo(request):
    exigir(request.user, "cliente")
    try:
        registrar(request.user, int(request.POST.get("refeicao", "")), opcoes_ids=[int(i) for i in request.POST.getlist("opcoes")])
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
        return redirect("home")
    form = AvaliacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        avaliacao = form.save(commit=False)
        avaliacao.pedido = pedido
        avaliacao.save()
        messages.success(request, "Obrigado pela sua avaliação!")
        return redirect("home")
    return render(request, "avaliar.html", {"pedido": pedido, "form": form})
