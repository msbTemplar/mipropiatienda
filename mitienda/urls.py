"""
URL configuration for mitienda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# mitienda/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home # Importa la vista home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'), # La URL de inicio
    # Incluye las URLs de autenticación de Django
    path('accounts/', include('django.contrib.auth.urls')), # Esto proporciona URLs como /accounts/login/, /accounts/logout/, etc.
    
    # Aquí puedes añadir include para otras apps cuando sea necesario
    path('productos/', include('productos.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('paginas/', include('paginas.urls')),
    # ¡IMPORTANTE! Añade esta URL de PayPal en la raíz del proyecto
    path('paypal-ipn/', include('paypal.standard.ipn.urls')), 
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)