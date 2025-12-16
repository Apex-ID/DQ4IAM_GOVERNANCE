from django import forms
from .models import DicionarioOrganograma

class OrganogramaForm(forms.ModelForm):
    class Meta:
        model = DicionarioOrganograma
        fields = ['codigo_unidade', 'sigla', 'nome', 'hierarquia']
        widgets = {
            'codigo_unidade': forms.TextInput(attrs={'class': 'form-control'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'hierarquia': forms.TextInput(attrs={'class': 'form-control'}),
        }