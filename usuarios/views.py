# usuarios/views.py
from django.shortcuts import render, redirect # Asegúrate de que redirect esté importado
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required # ¡Importa esto!
from django.contrib import messages # ¡Importa esto para los mensajes!
from pedidos.models import Pedido # ¡Importa el modelo Pedido!

from django import forms # Importa forms para crear el UserProfileForm
from .forms import CustomUserCreationForm, UserProfileForm # ¡Importa UserProfileForm!
from .models import CustomUser # ¡Importa tu modelo de usuario personalizado!

# Formulario para editar el perfil del usuario (NUEVO)
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Define qué campos de CustomUser se pueden editar desde el perfil
        fields = ('first_name', 'last_name', 'email', 'telefono') 
        # Asegúrate de que 'telefono' exista en tu CustomUser y añade cualquier otro campo que desees que el usuario pueda editar.


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login') 
    template_name = 'registration/register.html' 

    def form_valid(self, form):
        response = super().form_valid(form)
        return response



@login_required # Esto asegura que solo usuarios logueados accedan
def ver_perfil(request):
    # request.user ya es una instancia de tu CustomUser
    user_obj = request.user 
    
    # Obtener los pedidos asociados a este usuario
    # Asegúrate de que tu modelo Pedido tiene un ForeignKey 'usuario' a CustomUser
    pedidos_usuario = Pedido.objects.filter(usuario=user_obj).order_by('-fecha_pedido') # Usamos fecha_pedido

    context = {
        'user_obj': user_obj, # Pasamos el objeto CustomUser al contexto
        'pedidos_usuario': pedidos_usuario,
        'nombre_usuario': user_obj.get_full_name() or user_obj.username,
    }
    return render(request, 'usuarios/ver_perfil.html', context)



@login_required # Esto asegura que solo usuarios logueados accedan
def editar_perfil(request):
    user_obj = request.user # Obtenemos la instancia de CustomUser del usuario logueado
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('usuarios:ver_perfil')
    else:
        form = UserProfileForm(instance=user_obj) # Pre-rellena el formulario con los datos actuales del usuario
    
    context = {
        'form': form,
        'nombre_usuario': user_obj.get_full_name() or user_obj.username,
    }
    return render(request, 'usuarios/editar_perfil.html', context)