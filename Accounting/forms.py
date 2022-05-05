from django import forms
from .models import GAE


class GaeForm(forms.ModelForm):

    sigla_gae = forms.CharField(label="GAE on SIGLA", widget=forms.Select(), required=False)

    class Meta:
        model = GAE
        fields = ['project', 'name', 'description']
        widgets = {
            'name': forms.HiddenInput(),
            'description': forms.HiddenInput(),
        }
