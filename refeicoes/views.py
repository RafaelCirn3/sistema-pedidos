from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from usuarios.permissions import exigir
from .models import Refeicao
from .forms import RefeicaoForm, OpcaoFormSet

@login_required
def cardapio(request):
    exigir(request.user, "cozinha", "admin")
    return render(request, "refeicoes/cardapio.html", {"refeicoes": Refeicao.objects.prefetch_related("opcoes")})

@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar(request, pk=None):
    exigir(request.user, "cozinha", "admin")
    refeicao = get_object_or_404(Refeicao.objects.select_for_update(), pk=pk) if pk else Refeicao()
    data = request.POST if request.method == "POST" else None
    form = RefeicaoForm(data, request.FILES or None, instance=refeicao)
    opcoes = OpcaoFormSet(data, instance=refeicao, prefix="opcoes")
    if request.method == "POST" and form.is_valid() and opcoes.is_valid():
        refeicao = form.save()
        opcoes.instance = refeicao
        # Excluir primeiro para permitir reutilizar nomes de opções removidas.
        alteradas = opcoes.save(commit=False)
        for obj in opcoes.deleted_objects:
            obj.delete()
        for obj in alteradas:
            obj.save()
        messages.success(request, "Prato e opções salvos.")
        return redirect("cardapio")
    return render(request, "refeicoes/editar.html", {"form": form, "opcoes": opcoes, "refeicao": refeicao})

def imagem(request, pk):
    prato = get_object_or_404(Refeicao, pk=pk)
    if not prato.imagem:
        raise Http404
    try:
        arquivo = prato.imagem.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404
    tipo = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    from pathlib import Path
    content_type = tipo.get(Path(prato.imagem.name).suffix)
    if not content_type:
        arquivo.close()
        raise Http404
    return FileResponse(arquivo, content_type=content_type)
