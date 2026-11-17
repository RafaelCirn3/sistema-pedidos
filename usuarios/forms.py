import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="E-mail", widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        return username.lower() if "@" in username else username

class CadastroClienteForm(forms.Form):
    nome = forms.CharField(max_length=150, label="Nome completo")
    email = forms.EmailField(max_length=150, label="E-mail")
    whatsapp = forms.CharField(max_length=25, label="WhatsApp", widget=forms.TextInput(attrs={"type": "tel", "placeholder": "(83) 99999-9999"}))
    senha = forms.CharField(label="Senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise ValidationError("Este e-mail já está em uso.")
        return email

    def clean_whatsapp(self):
        numero = re.sub(r"\D", "", self.cleaned_data["whatsapp"])
        if len(numero) in (10, 11):
            numero = "55" + numero
        if len(numero) not in (12, 13) or not numero.startswith("55"):
            raise ValidationError("Informe um WhatsApp brasileiro com DDD.")
        return "+" + numero

    def clean(self):
        data = super().clean()
        if data.get("senha") and data.get("email"):
            user = User(username=data["email"], email=data["email"], first_name=data.get("nome", ""))
            try:
                validate_password(data["senha"], user=user)
            except ValidationError as exc:
                self.add_error("senha", exc)
        return data
