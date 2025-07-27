# usuarios/urls.py
from django.urls import path
from .views import RegisterView, ver_perfil, editar_perfil # Importa las nuevas vistas

app_name = 'usuarios' # ¡Asegúrate de que esta línea está aquí!

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    
    # --- Nuevas URLs para el perfil de usuario ---
    path('perfil/', ver_perfil, name='ver_perfil'),
    path('perfil/editar/', editar_perfil, name='editar_perfil'),
]