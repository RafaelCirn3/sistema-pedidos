from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from .forms import CadastroClienteForm
from .models import PerfilCliente

def cadastro(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = CadastroClienteForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=data["email"], email=data["email"], first_name=data["nome"], password=data["senha"])
                user.groups.add(Group.objects.get(name="Cliente"))
                PerfilCliente.objects.create(usuario=user, whatsapp=data["whatsapp"])
        except IntegrityError:
            form.add_error("email", "Este e-mail já está em uso.")
        else:
            login(request, user)
            messages.success(request, "Conta criada! Escolha sua refeição.")
            return redirect("home")
    return render(request, "registration/cadastro.html", {"form": form})
