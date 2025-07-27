# core/views.py
from django.shortcuts import render
from productos.models import Producto # Importa tu modelo Producto

def home(request):
    # Obtener algunos productos destacados para mostrar en la página de inicio
    productos_destacados = Producto.objects.filter(es_destacado=True, disponible=True)[:8] # Limita a 8 productos por ejemplo
    context = {
        'productos_destacados': productos_destacados
    }
    return render(request, 'home.html', context)