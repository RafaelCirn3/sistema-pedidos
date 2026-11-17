from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Refeicao, OpcaoRefeicao

class RefeicaoForm(forms.ModelForm):
    class Meta:
        model = Refeicao
        fields = ("nome", "descricao", "imagem", "disponivel")
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3}), "imagem": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"})}

    def clean_imagem(self):
        imagem = self.cleaned_data.get("imagem")
        if imagem and hasattr(imagem, "image"):
            if imagem.size > 5 * 1024 * 1024:
                raise ValidationError("A imagem deve ter no máximo 5 MB.")
            formato = imagem.image.format
            extensoes = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
            if formato not in extensoes:
                raise ValidationError("Envie uma imagem JPG, PNG ou WebP.")
            imagem.name = "prato" + extensoes[formato]
        return imagem

OpcaoFormSet = inlineformset_factory(Refeicao, OpcaoRefeicao, fields=("nome",), extra=0, can_delete=True, max_num=30, validate_max=True)
