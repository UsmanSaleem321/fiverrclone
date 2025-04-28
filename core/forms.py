from django import forms
from .models import Gig

class GigForm(forms.ModelForm):
    class Meta:
        model = Gig
        fields = ['title', 'description', 'price', 'seller']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Gig Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Gig Description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price'}),
            'seller': forms.Select(attrs={'class': 'form-control'}),
        }