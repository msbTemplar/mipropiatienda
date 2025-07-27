# productos/filters.py
import django_filters
from .models import Producto, VariacionProducto, Categoria, Marca # Asegúrate de importar tus modelos

class ProductoFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(field_name='nombre', lookup_expr='icontains', label='Buscar por Nombre')
    categoria = django_filters.ModelChoiceFilter(queryset=Categoria.objects.all(), label='Categoría')
    marca = django_filters.ModelChoiceFilter(queryset=Marca.objects.all(), label='Marca')
    disponible = django_filters.BooleanFilter(field_name='disponible', label='Disponible')
    es_destacado = django_filters.BooleanFilter(field_name='es_destacado', label='Es destacado')

    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'marca', 'disponible', 'es_destacado']


class VariacionProductoFilter(django_filters.FilterSet):
    # Asume que quieres filtrar por el nombre del producto relacionado
    producto__nombre = django_filters.CharFilter(field_name='producto__nombre', lookup_expr='icontains', label='Buscar por Producto')
    sku = django_filters.CharFilter(field_name='sku', lookup_expr='icontains', label='Buscar por SKU')
    activo = django_filters.BooleanFilter(field_name='activo', label='Activo')

    # Si quieres filtrar por los valores de las variaciones, sería más complejo
    # valores = django_filters.ModelMultipleChoiceFilter(queryset=ValorVariacion.objects.all(),
    #                                                  widget=forms.CheckboxSelectMultiple,
    #                                                  label='Valores de Variación')

    class Meta:
        model = VariacionProducto
        fields = ['producto__nombre', 'sku', 'activo'] # Puedes añadir más campos aquí para filtrar