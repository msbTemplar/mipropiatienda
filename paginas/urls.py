# paginas/urls.py
from django.urls import path
from .views import contacto_view # Importa tu vista

app_name = 'paginas' # Define el namespace para esta app

urlpatterns = [
    path('contacto/', contacto_view, name='contacto'),
]