# productos/tables.py
import django_tables2 as tables
from .models import Producto, VariacionProducto, Categoria, Marca
from django_filters import FilterSet, CharFilter
from django.db.models import Sum
from django.utils.safestring import mark_safe # <--- ¡IMPORTANTE: Añade esta importación!
from django.utils.html import format_html, strip_tags # <--- Asegúrate de importar strip_tags

class ProductoTable(tables.Table):
    # Definir una columna personalizada para las acciones
    acciones = tables.TemplateColumn(
        template_name='productos/admin/includes/producto_acciones_col.html',
        verbose_name='Acciones',
        orderable=False,
        attrs={"td": {"class": "text-center align-middle"}} # Para centrar y alinear verticalmente
    )
    
    # Columna para el stock total, calculada
    # QUITA safe=True de aquí
    total_stock = tables.Column(
        verbose_name="Stock Total", 
        empty_values=(), 
        orderable=False, 
        attrs={"td": {"class": "text-center align-middle"}}
    ) 

    class Meta:
        model = Producto
        template_name = "django_tables2/bootstrap5.html" # Plantilla para el renderizado
        fields = (
            'id', 'nombre', 'categoria', 'marca', 'precio', 'disponible', 'es_destacado', 'total_stock'
        )
        sequence = (
            'id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado', 'acciones'
        )
        attrs = {"class": "table table-striped table-hover"}

    def render_total_stock(self, record):
        stock_sum = record.variaciones.filter(activo=True).aggregate(Sum('stock'))['stock__sum'] or 0
        if stock_sum == 0:
            return mark_safe('<span class="badge bg-danger">Agotado</span>') # <--- ¡Envuelve con mark_safe!
        elif stock_sum < 10:
            return mark_safe(f'<span class="badge bg-warning">Poco Stock ({stock_sum})</span>') # <--- ¡Envuelve con mark_safe!
        else:
            return mark_safe(f'<span class="badge bg-success">{stock_sum}</span>') # <--- ¡Envuelve con mark_safe!
    
    def render_precio(self, value):
        return f"{value:.2f} €"

    def render_disponible(self, value):
        # QUITA safe=True de la columna y ENVOLVE con mark_safe
        return mark_safe('<i class="bi bi-check-circle-fill text-success"></i>' if value else '<i class="bi bi-x-circle-fill text-danger"></i>')

    def render_es_destacado(self, value):
        # QUITA safe=True de la columna y ENVOLVE con mark_safe
        return mark_safe('<i class="bi bi-star-fill text-warning"></i>' if value else '<i class="bi bi-star"></i>')


# --- NUEVA CLASE: Tabla para exportación a Excel/CSV (sin HTML) ---
class ProductoTableExport(ProductoTable):
    # Anula los métodos render_ para devolver texto plano
    # --- MODIFICACIÓN AQUÍ PARA 'total_stock' ---
    def render_total_stock(self, value):
        # Simplemente devuelve el valor numérico como una cadena.
        # Esto evita cualquier generación de HTML y garantiza que el número se exporte.
        return str(value) if value is not None else '0' 
    # --- FIN MODIFICACIÓN ---

    def render_disponible(self, value):
        return "Sí" if value else "No" # Devuelve "Sí" o "No"

    def render_es_destacado(self, value):
        return "Sí" if value else "No" # Devuelve "Sí" o "No"
    
    # Si tienes otras columnas personalizadas que generan HTML, anúlalas aquí
    # def render_mi_columna_html(self, value):
    #     return strip_tags(super().render_mi_columna_html(value)) # O simplemente devuelve el valor original

    class Meta(ProductoTable.Meta):
        # Hereda la configuración de ProductoTable, pero excluye la columna de acciones
        exclude = ('acciones',)
        # Puedes mantener 'fields' y 'sequence' igual si ya están bien para la exportación






class VariacionProductoTable(tables.Table):
    # Columna para los valores de variación (ManyToManyField)
    valores_display = tables.Column(verbose_name="Valores", empty_values=(), orderable=False)
    # Columna para la imagen
    imagen = tables.TemplateColumn(
        template_name='productos/admin/includes/variacion_imagen_col.html',
        verbose_name='Imagen',
        orderable=False,
        attrs={"td": {"class": "text-center align-middle"}}
    )
    # Acciones (editar, eliminar)
    acciones = tables.TemplateColumn(
        template_name='productos/admin/includes/variacion_acciones_col.html',
        verbose_name='Acciones',
        orderable=False,
        attrs={"td": {"class": "text-center align-middle"}}
    )

    # QUITA safe=True de aquí
    stock = tables.Column(
        verbose_name="Stock", 
        attrs={"td": {"class": "text-center align-middle"}}
    ) 
    # QUITA safe=True de aquí
    activo = tables.Column(
        verbose_name="Activo", 
        attrs={"td": {"class": "text-center align-middle"}}
    ) 


    class Meta:
        model = VariacionProducto
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            'id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo'
        )
        sequence = (
            'id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo', 'acciones'
        )
        attrs = {"class": "table table-striped table-hover"}

    def render_valores_display(self, record):
        return ', '.join([f"{v.tipo_variacion.nombre}: {v.valor}" for v in record.valores.all()]) or 'N/A'

    def render_precio_adicional(self, value):
        return f"{value:.2f} €"

    def render_stock(self, value):
        # QUITA safe=True de la columna y ENVOLVE con mark_safe
        if value == 0:
            return mark_safe('<span class="badge bg-danger">Agotado</span>')
        elif value < 5:
            return mark_safe(f'<span class="badge bg-warning">Bajo ({value})</span>')
        else:
            return mark_safe(f'<span class="badge bg-success">{value}</span>')

    def render_activo(self, value):
        # QUITA safe=True de la columna y ENVOLVE con mark_safe
        return mark_safe('<i class="bi bi-check-circle-fill text-success"></i>' if value else '<i class="bi bi-x-circle-fill text-danger"></i>')


# --- NUEVA CLASE: Tabla para exportación a Excel/CSV (sin HTML) ---
class VariacionProductoTableExport(VariacionProductoTable):
    # Anula los métodos render_ para devolver texto plano
    def render_imagen(self, record):
        if record.imagen_variacion and hasattr(record.imagen_variacion, 'url'):
            return record.imagen_variacion.url # Devuelve la URL de la imagen
        return '-'

    def render_activo(self, value):
        return "Sí" if value else "No" # Devuelve "Sí" o "No"
    
    # --- NUEVO MÉTODO PARA STOCK ---
    def render_stock(self, value):
        # Asume que 'value' es el stock entero. Devuélvelo como string.
        # Esto elimina cualquier etiqueta HTML o formato de badge.
        return str(value)
    # --- FIN NUEVO MÉTODO PARA STOCK ---

    class Meta(VariacionProductoTable.Meta):
        # Hereda la configuración de VariacionProductoTable, pero excluye la columna de acciones
        exclude = ('acciones',)


# --- Filtros (Opcional, pero útil para los listados) ---
class ProductoFilter(FilterSet):
    nombre = CharFilter(lookup_expr='icontains', label='Buscar por Nombre')
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'marca', 'disponible', 'es_destacado']

class VariacionProductoFilter(FilterSet):
    sku = CharFilter(lookup_expr='icontains', label='Buscar por SKU')
    class Meta:
        model = VariacionProducto
        fields = ['producto', 'sku', 'activo']