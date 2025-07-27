# mitienda/pedidos/forms.py
from django import forms
from .models import Pedido # ¡IMPORTANTE! Importamos Pedido de la MISMA aplicación (pedidos)

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Pedido
        # Asegúrate de que estos campos coincidan exactamente con los campos de tu modelo Pedido
        # que quieres que el usuario rellene en el formulario.
        # En tu traceback anterior, los campos del modelo Pedido que se intentaban rellenar eran:
        # 'nombre_envio', 'email_envio', 'direccion_envio_line1', 'ciudad_envio', 'provincia_envio', 'codigo_postal_envio', 'pais_envio'
        # ¡DEBEN COINCIDIR CON TU MODELO PEDIDO!
        fields = [
            'nombre_envio', 'email_envio', 'direccion_envio_line1', 
            'ciudad_envio', 'provincia_envio', 'codigo_postal_envio',
            'pais_envio'
        ]
        widgets = {
            'nombre_envio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
            'email_envio': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu_email@ejemplo.com'}),
            'direccion_envio_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle, número, piso'}),
            'ciudad_envio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'provincia_envio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Provincia'}), # Agregado
            'codigo_postal_envio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código Postal'}),
            'pais_envio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País'}), # Agregado
        }
    
    # Puedes añadir un campo para el método de pago aquí si quieres que sea una selección
    # metodo_pago = forms.ChoiceField(choices=[('transferencia', 'Transferencia Bancaria'), ('tarjeta_simulada', 'Tarjeta de Crédito (Simulado)')], 
    #                                  widget=forms.Select(attrs={'class': 'form-select'}))