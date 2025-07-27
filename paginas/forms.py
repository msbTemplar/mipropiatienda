# paginas/forms.py
from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone_number', 'subject', 'message'] # <-- ¡Añadido 'phone_number'!
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu Nombre Completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu.email@ejemplo.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Teléfono (Opcional)'}), # <-- ¡Nuevo widget!
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asunto de tu mensaje'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Escribe tu mensaje aquí...', 'rows': 5}),
        }