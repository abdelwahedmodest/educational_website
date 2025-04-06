from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    """Formulaire de contact"""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Votre email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sujet'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Votre message', 'rows': 6}),
        }

class SearchForm(forms.Form):
    """Formulaire de recherche"""
    query = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Rechercher...',
        })
    )
    category = forms.CharField(required=False, widget=forms.HiddenInput())
