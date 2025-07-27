# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario personalizado para la creación de usuarios, basado en UserCreationForm.
    Añade el campo 'telefono' de nuestro CustomUser.
    """
    class Meta:
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('telefono',) # Añade 'telefono'

class CustomUserChangeForm(UserChangeForm):
    """
    Formulario personalizado para la edición de usuarios en el admin, basado en UserChangeForm.
    Este formulario es típicamente usado en el panel de administración de Django.
    """
    class Meta:
        model = CustomUser
        # Para el admin, querrás que se puedan editar todos los campos relevantes, incluyendo email
        fields = ('username', 'email', 'first_name', 'last_name', 'telefono', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

# --- ¡NUEVO FORMULARIO PARA EL PERFIL DEL USUARIO FINAL! ---
class UserProfileForm(forms.ModelForm):
    """
    Formulario para que el usuario final edite su propio perfil.
    """
    class Meta:
        model = CustomUser
        # Campos que el usuario puede editar directamente en su página de perfil
        fields = ('first_name', 'last_name', 'email', 'telefono') 
        # Si tu CustomUser tiene más campos que el usuario final deba editar, añádelos aquí.
        # Por ejemplo, si CustomUser tuviera 'direccion', lo añadirías:
        # fields = ('first_name', 'last_name', 'email', 'telefono', 'direccion')