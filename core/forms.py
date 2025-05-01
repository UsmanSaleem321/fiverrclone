from django import forms
from .models import Gig, CustomUser

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

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['bio', 'location', 'skills', 'profile_image']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['bio', 'location', 'skills', 'profile_image']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Bio'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Skills'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }