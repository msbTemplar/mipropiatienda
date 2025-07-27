# productos/admin.py
from django.contrib import admin
from .models import (
    Categoria, Marca, Producto, TipoVariacion, ValorVariacion,
    VariacionProducto, ImagenProducto
)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

class ImagenProductoInline(admin.TabularInline): # Para añadir imágenes directamente desde el producto
    model = ImagenProducto
    extra = 1 # Número de formularios vacíos para añadir

class VariacionProductoInline(admin.TabularInline): # Para añadir variaciones directamente desde el producto
    model = VariacionProducto
    extra = 1
    filter_horizontal = ('valores',) # Para que el ManyToManyField sea más amigable

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'categoria', 'marca', 'disponible', 'es_destacado')
    list_filter = ('disponible', 'es_destacado', 'categoria', 'marca')
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [ImagenProductoInline, VariacionProductoInline] # Aquí se integran

@admin.register(TipoVariacion)
class TipoVariacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(ValorVariacion)
class ValorVariacionAdmin(admin.ModelAdmin):
    list_display = ('tipo_variacion', 'valor')
    list_filter = ('tipo_variacion',)

# Si no usas Inlines, puedes registrarlos así:
# admin.site.register(VariacionProducto)
# admin.site.register(ImagenProducto)