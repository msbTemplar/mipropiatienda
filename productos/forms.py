# productos/forms.py
from django import forms
from .models import (
    Producto, Categoria, Marca,
    TipoVariacion, ValorVariacion, VariacionProducto, ImagenProducto
)
from django.utils.text import slugify

# --- Formularios para Modelos Principales (Producto, Categoria, Marca) ---

class ProductoForm(forms.ModelForm):
    # El campo 'slug' puede ser de solo lectura o se puede generar automáticamente si no lo quieres editable
    # Si quieres que se genere automáticamente y no lo editen, puedes quitarlo de fields y añadirlo en save()
    # Para este propósito, lo dejaremos editable pero sugeriremos un autogenerado en la vista.
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'categoria', 'marca', 'disponible', 'es_destacado', 'slug']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción detallada'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.Select(attrs={'class': 'form-select'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL amigable (se autogenera si se deja vacío)'}),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'descripcion': 'Descripción',
            'precio': 'Precio Base',
            'categoria': 'Categoría',
            'marca': 'Marca',
            'disponible': 'Disponible para Venta',
            'es_destacado': 'Producto Destacado',
            'slug': 'Slug (URL amigable)',
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'slug']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la categoría (opcional)'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL amigable (se autogenera si se deja vacío)'}),
        }
        labels = {
            'nombre': 'Nombre de la Categoría',
            'descripcion': 'Descripción',
            'slug': 'Slug (URL amigable)',
        }

class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ['nombre', 'descripcion', 'slug']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la marca'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la marca (opcional)'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL amigable (se autogenera si se deja vacío)'}),
        }
        labels = {
            'nombre': 'Nombre de la Marca',
            'descripcion': 'Descripción',
            'slug': 'Slug (URL amigable)',
        }

# --- Formularios para Variaciones y sus Tipos/Valores ---

class TipoVariacionForm(forms.ModelForm):
    class Meta:
        model = TipoVariacion
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Color, Talla, Material'}),
        }
        labels = {
            'nombre': 'Nombre del Tipo de Variación',
        }

class ValorVariacionForm(forms.ModelForm):
    class Meta:
        model = ValorVariacion
        fields = ['tipo_variacion', 'valor']
        widgets = {
            'tipo_variacion': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Rojo, M, Algodón'}),
        }
        labels = {
            'tipo_variacion': 'Tipo de Variación',
            'valor': 'Valor',
        }

class VariacionProductoForm(forms.ModelForm):
    # Nota: El ManyToManyField 'valores' necesita un widget especial si no usas crispy forms
    # Con crispy-forms y filter_horizontal en admin, se maneja bien.
    # Aquí lo preparamos para un uso general, aunque en admin se use Inlines.
    class Meta:
        model = VariacionProducto
        fields = ['producto', 'valores', 'sku', 'stock', 'precio_adicional', 'imagen_variacion', 'activo']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SKU (se autogenera si se deja vacío)'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'precio_adicional': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'imagen_variacion': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # 'valores' no necesita un widget específico aquí si usamos ModelForm,
            # Django lo renderizará como un SelectMultiple por defecto.
            # Para mejor UX, considera django-select2 o similar.
        }
        labels = {
            'producto': 'Producto Principal',
            'valores': 'Valores de Variación',
            'sku': 'SKU (Código de Stock)',
            'stock': 'Stock',
            'precio_adicional': 'Precio Adicional',
            'imagen_variacion': 'Imagen de Variación',
            'activo': 'Activo',
        }

class ImagenProductoForm(forms.ModelForm):
    class Meta:
        model = ImagenProducto
        fields = ['producto', 'imagen', 'es_principal', 'orden']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'es_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
        labels = {
            'producto': 'Producto Asociado',
            'imagen': 'Archivo de Imagen',
            'es_principal': 'Es Imagen Principal',
            'orden': 'Orden de Visualización',
        }
    
    # Añade este método para modificar el campo 'orden'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacemos que el campo 'orden' no sea obligatorio
        self.fields['orden'].required = False
        # Le asignamos un valor por defecto
        self.fields['orden'].initial = 1