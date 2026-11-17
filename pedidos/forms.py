from django import forms
from avaliacoes.models import Avaliacao

class AvaliacaoForm(forms.ModelForm):
    nota = forms.TypedChoiceField(choices=[(i, f"{i} estrela{'s' if i != 1 else ''}") for i in range(6)], coerce=int, widget=forms.RadioSelect)
    class Meta:
        model = Avaliacao
        fields = ["nota", "comentario"]
        widgets = {"comentario": forms.Textarea(attrs={"rows": 4, "placeholder": "Conte como foi sua refeição (opcional)"})}
