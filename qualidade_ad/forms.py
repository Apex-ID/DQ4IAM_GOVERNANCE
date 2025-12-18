from django import forms
from .models import DicionarioOrganograma

class UploadOrganogramaForm(forms.Form):
    arquivo_csv = forms.FileField(
        label="Selecione o arquivo CSV do Organograma",
        help_text="Formato esperado: codigo_unidade, sigla, nome, hierarquia"
    )

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

class UploadVinculosForm(forms.Form):
    arquivo_csv = forms.FileField(
        label="Selecione o arquivo CSV de Vínculos (RH/Acadêmico)",
        help_text="Colunas necessárias: matricula, cpf, nome, email, tipo, status, lotacao"
    )