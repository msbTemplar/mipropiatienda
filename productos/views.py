# productos/views.py
from venv import logger
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test # Para proteger las vistas
from django.contrib import messages
from django.db.models import Sum # Para cálculos de stock si es necesario
import datetime # Añade esta línea
from .models import ( # Asegúrate de importar todos los modelos necesarios
    Producto, Categoria, Marca, TipoVariacion, ValorVariacion,
    VariacionProducto, ImagenProducto
)
from .forms import ( # Importa todos tus formularios
    ProductoForm, CategoriaForm, MarcaForm,
    TipoVariacionForm, ValorVariacionForm, VariacionProductoForm, ImagenProductoForm
)
from .tables import ProductoTableExport, VariacionProductoTableExport 

from django.template.loader import render_to_string # Para plantillas HTML en el correo
# Importaciones para django-tables2 y django-filter
import django_tables2 as tables
from django_tables2.export import TableExport
from .tables import ProductoTable, VariacionProductoTable, ProductoFilter, VariacionProductoFilter # Importa tus tablas y filtros
from django.utils.html import format_html # Importa esto
# Importación para WeasyPrint
from weasyprint import HTML, CSS
import tempfile # Para manejar archivos temporales

from .filters import ProductoFilter, VariacionProductoFilter # Asegúrate de que estos filtros existen
from .tables import ProductoTable, VariacionProductoTable # Asegúrate de que estas tablas existen
import logging # Nueva importación para logs

def productos_listado(request):
    productos = Producto.objects.filter(disponible=True).order_by('nombre')
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    
    # Filtros (esto se puede mejorar, es una base)
    categoria_seleccionada = request.GET.get('categoria')
    marca_seleccionada = request.GET.get('marca')
    search_query = request.GET.get('q')

    if categoria_seleccionada:
        productos = productos.filter(categoria__slug=categoria_seleccionada)
    if marca_seleccionada:
        productos = productos.filter(marca__slug=marca_seleccionada)
    if search_query:
        productos = productos.filter(nombre__icontains=search_query) # Búsqueda básica

    context = {
        'productos': productos,
        'categorias': categorias,
        'marcas': marcas,
        'categoria_seleccionada': categoria_seleccionada,
        'marca_seleccionada': marca_seleccionada,
        'search_query': search_query,
    }
    return render(request, 'productos/productos_listado.html', context)

def producto_detalle(request, slug):
    producto = get_object_or_404(Producto, slug=slug, disponible=True)
    # Aquí podrías obtener las variaciones relacionadas
    variaciones = producto.variaciones.filter(stock__gt=0) # Solo mostrar variaciones con stock
    
    # Obtener imágenes del producto
    imagenes = producto.imagenes.all().order_by('orden')

    context = {
        'producto': producto,
        'variaciones': variaciones,
        'imagenes': imagenes,
    }
    return render(request, 'productos/producto_detalle.html', context)


# --- Función auxiliar para proteger vistas de administración ---
def is_staff_check(user):
    return user.is_staff

# --------------------------------------------------------------------------
# Vistas de Administración para PRODUCTOS (CRUD)
# --------------------------------------------------------------------------

@login_required # Requiere que el usuario esté logueado
@user_passes_test(is_staff_check) # Requiere que el usuario sea staff
def admin_productos_list_conerror(request):
    productos = Producto.objects.all().order_by('-fecha_creacion')
    
    # Calcular stock total si existen variaciones
    for p in productos:
        if hasattr(p, 'variaciones'): # Verifica si el related_name existe
            # Filtra por variaciones activas para el cálculo del stock mostrado
            p.total_stock = p.variaciones.filter(activo=True).aggregate(Sum('stock'))['stock__sum'] or 0
        else:
            p.total_stock = 0 # O puedes usar p.stock directamente si el producto no tiene variaciones
                               # Esta lógica asume que el stock real está en las variaciones.
    
    return render(request, 'productos/admin/productos_list.html', {'productos': productos})

@login_required 
@user_passes_test(is_staff_check) 
def admin_productos_list(request):
    # Obtienes todos los productos
    productos = Producto.objects.all().order_by('-fecha_creacion')
    
    # ¡Eso es todo! La propiedad 'total_stock' ya está disponible en cada objeto 'p'
    # en la plantilla. No necesitas calcularla aquí.
    
    return render(request, 'productos/admin/productos_list.html', {'productos': productos})

@login_required
@user_passes_test(is_staff_check)
def admin_producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('productos:admin_productos_list') # Redirige al listado de admin
        else:
            messages.error(request, 'Error al crear el producto. Revisa los campos.')
    else:
        form = ProductoForm()
    return render(request, 'productos/admin/producto_form.html', {'form': form, 'action': 'create'})

@login_required
@user_passes_test(is_staff_check)
def admin_producto_edit(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('productos:admin_productos_list')
        else:
            messages.error(request, 'Error al actualizar el producto. Revisa los campos.')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/admin/producto_form.html', {'form': form, 'producto': producto, 'action': 'edit'})

@login_required
@user_passes_test(is_staff_check)
def admin_producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto_nombre = producto.nombre # Guarda el nombre antes de eliminar
        producto.delete()
        messages.success(request, f'Producto "{producto_nombre}" eliminado exitosamente.')
        return redirect('productos:admin_productos_list')
    messages.error(request, 'Método no permitido para eliminar. Se requiere una solicitud POST.')
    return redirect('productos:admin_productos_list')


# --------------------------------------------------------------------------
# Vistas de Administración para CATEGORIAS (CRUD)
# --------------------------------------------------------------------------

@login_required
@user_passes_test(is_staff_check)
def admin_categorias_list(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'productos/admin/categorias_list.html', {'categorias': categorias})

@login_required
@user_passes_test(is_staff_check)
def admin_categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('productos:admin_categorias_list')
        else:
            messages.error(request, 'Error al crear la categoría. Revisa los campos.')
    else:
        form = CategoriaForm()
    return render(request, 'productos/admin/categoria_form.html', {'form': form, 'action': 'create'})

@login_required
@user_passes_test(is_staff_check)
def admin_categoria_edit(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('productos:admin_categorias_list')
        else:
            messages.error(request, 'Error al actualizar la categoría. Revisa los campos.')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'productos/admin/categoria_form.html', {'form': form, 'categoria': categoria, 'action': 'edit'})

@login_required
@user_passes_test(is_staff_check)
def admin_categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria_nombre = categoria.nombre
        categoria.delete()
        messages.success(request, f'Categoría "{categoria_nombre}" eliminada exitosamente.')
        return redirect('productos:admin_categorias_list')
    messages.error(request, 'Método no permitido para eliminar. Se requiere una solicitud POST.')
    return redirect('productos:admin_categorias_list')

# --------------------------------------------------------------------------
# Vistas de Administración para MARCAS (CRUD) - NUEVAS
# --------------------------------------------------------------------------

@login_required
@user_passes_test(is_staff_check)
def admin_marcas_list(request):
    marcas = Marca.objects.all().order_by('nombre')
    return render(request, 'productos/admin/marcas_list.html', {'marcas': marcas})

@login_required
@user_passes_test(is_staff_check)
def admin_marca_create(request):
    if request.method == 'POST':
        form = MarcaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca creada exitosamente.')
            return redirect('productos:admin_marcas_list')
        else:
            messages.error(request, 'Error al crear la marca. Revisa los campos.')
    else:
        form = MarcaForm()
    return render(request, 'productos/admin/marca_form.html', {'form': form, 'action': 'create'})

@login_required
@user_passes_test(is_staff_check)
def admin_marca_edit(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == 'POST':
        form = MarcaForm(request.POST, instance=marca)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca actualizada exitosamente.')
            return redirect('productos:admin_marcas_list')
        else:
            messages.error(request, 'Error al actualizar la marca. Revisa los campos.')
    else:
        form = MarcaForm(instance=marca)
    return render(request, 'productos/admin/marca_form.html', {'form': form, 'marca': marca, 'action': 'edit'})

@login_required
@user_passes_test(is_staff_check)
def admin_marca_delete(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == 'POST':
        marca_nombre = marca.nombre
        marca.delete()
        messages.success(request, f'Marca "{marca_nombre}" eliminada exitosamente.')
        return redirect('productos:admin_marcas_list')
    messages.error(request, 'Método no permitido para eliminar. Se requiere una solicitud POST.')
    return redirect('productos:admin_marcas_list')


# --------------------------------------------------------------------------
# Vistas de Administración para TIPOS DE VARIACION (CRUD) - NUEVAS
# --------------------------------------------------------------------------

@login_required
@user_passes_test(is_staff_check)
def admin_tipos_variacion_list(request):
    tipos = TipoVariacion.objects.all().order_by('nombre')
    return render(request, 'productos/admin/tipos_variacion_list.html', {'tipos': tipos})

@login_required
@user_passes_test(is_staff_check)
def admin_tipo_variacion_create(request):
    if request.method == 'POST':
        form = TipoVariacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de variación creado exitosamente.')
            return redirect('productos:admin_tipos_variacion_list')
        else:
            messages.error(request, 'Error al crear el tipo de variación. Revisa los campos.')
    else:
        form = TipoVariacionForm()
    return render(request, 'productos/admin/tipo_variacion_form.html', {'form': form, 'action': 'create'})

@login_required
@user_passes_test(is_staff_check)
def admin_tipo_variacion_edit(request, pk):
    tipo = get_object_or_404(TipoVariacion, pk=pk)
    if request.method == 'POST':
        form = TipoVariacionForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de variación actualizado exitosamente.')
            return redirect('productos:admin_tipos_variacion_list')
        else:
            messages.error(request, 'Error al actualizar el tipo de variación. Revisa los campos.')
    else:
        form = TipoVariacionForm(instance=tipo)
    return render(request, 'productos/admin/tipo_variacion_form.html', {'form': form, 'tipo': tipo, 'action': 'edit'})

@login_required
@user_passes_test(is_staff_check)
def admin_tipo_variacion_delete(request, pk):
    tipo = get_object_or_404(TipoVariacion, pk=pk)
    if request.method == 'POST':
        tipo_nombre = tipo.nombre
        tipo.delete()
        messages.success(request, f'Tipo de variación "{tipo_nombre}" eliminado exitosamente.')
        return redirect('productos:admin_tipos_variacion_list')
    messages.error(request, 'Método no permitido para eliminar. Se requiere una solicitud POST.')
    return redirect('productos:admin_tipos_variacion_list')


# --------------------------------------------------------------------------
# Vistas de Administración para VALORES DE VARIACION (CRUD) - NUEVAS
# --------------------------------------------------------------------------

@login_required
@user_passes_test(is_staff_check)
def admin_valores_variacion_list(request):
    valores = ValorVariacion.objects.all().order_by('tipo_variacion__nombre', 'valor')
    return render(request, 'productos/admin/valores_variacion_list.html', {'valores': valores})

@login_required
@user_passes_test(is_staff_check)
def admin_valor_variacion_create(request):
    if request.method == 'POST':
        form = ValorVariacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Valor de variación creado exitosamente.')
            return redirect('productos:admin_valores_variacion_list')
        else:
            messages.error(request, 'Error al crear el valor de variación. Revisa los campos.')
    else:
        form = ValorVariacionForm()
    return render(request, 'productos/admin/valor_variacion_form.html', {'form': form, 'action': 'create'})

@login_required
@user_passes_test(is_staff_check)
def admin_valor_variacion_edit(request, pk):
    valor = get_object_or_404(ValorVariacion, pk=pk)
    if request.method == 'POST':
        form = ValorVariacionForm(request.POST, instance=valor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Valor de variación actualizado exitosamente.')
            return redirect('productos:admin_valores_variacion_list')
        else:
            messages.error(request, 'Error al actualizar el valor de variación. Revisa los campos.')
    else:
        form = ValorVariacionForm(instance=valor)
    return render(request, 'productos/admin/valor_variacion_form.html', {'form': form, 'valor': valor, 'action': 'edit'})

@login_required
@user_passes_test(is_staff_check)
def admin_valor_variacion_delete(request, pk):
    valor = get_object_or_404(ValorVariacion, pk=pk)
    if request.method == 'POST':
        valor_nombre = str(valor) # Convertir a string antes de eliminar
        valor.delete()
        messages.success(request, f'Valor de variación "{valor_nombre}" eliminado exitosamente.')
        return redirect('productos:admin_valores_variacion_list')
    messages.error(request, 'Método no permitido para eliminar. Se requiere una solicitud POST.')
    return redirect('productos:admin_valores_variacion_list')


# --------------------------------------------------------------------------
# Vistas de Administración para VARIACIONES DE PRODUCTO (CRUD) - NUEVAS
# --------------------------------------------------------------------------

@login_required
@user_passes_test(is_staff_check)
def admin_variaciones_producto_list(request, producto_pk=None):
    if producto_pk:
        producto = get_object_or_404(Producto, pk=producto_pk)
        variaciones = producto.variaciones.all().order_by('sku')
        return render(request, 'productos/admin/variaciones_producto_list.html', {
            'variaciones': variaciones,
            'producto': producto
        })
    else:
        variaciones = VariacionProducto.objects.all().order_by('producto__nombre', 'sku')
        return render(request, 'productos/admin/variaciones_producto_list.html', {
            'variaciones': variaciones
        })


@login_required
@user_passes_test(is_staff_check)
def admin_variacion_producto_create(request, producto_pk=None):
    initial_data = {}
    producto_instance = None
    if producto_pk:
        producto_instance = get_object_or_404(Producto, pk=producto_pk)
        initial_data['producto'] = producto_instance

    if request.method == 'POST':
        form = VariacionProductoForm(request.POST, request.FILES, initial=initial_data)
        if form.is_valid():
            variacion = form.save()
            messages.success(request, f'Variación de producto "{variacion}" creada exitosamente.')
            if producto_pk:
                return redirect('productos:admin_variaciones_producto_list_by_product', producto_pk=producto_pk)
            return redirect('productos:admin_productos_list') # O a una lista general de variaciones si se crea sin producto_pk
        else:
            messages.error(request, 'Error al crear la variación de producto. Revisa los campos.')
    else:
        form = VariacionProductoForm(initial=initial_data)

    return render(request, 'productos/admin/variacion_producto_form.html', {
        'form': form,
        'action': 'create',
        'producto': producto_instance # Pasar el producto para el contexto de la plantilla
    })

@login_required
@user_passes_test(is_staff_check)
def admin_variacion_producto_edit(request, pk):
    variacion = get_object_or_404(VariacionProducto, pk=pk)
    if request.method == 'POST':
        form = VariacionProductoForm(request.POST, request.FILES, instance=variacion)
        if form.is_valid():
            variacion = form.save()
            messages.success(request, f'Variación de producto "{variacion}" actualizada exitosamente.')
            if variacion.producto: # Redirigir al listado de variaciones de ese producto
                return redirect('productos:admin_variaciones_producto_list_by_product', producto_pk=variacion.producto.pk)
            return redirect('productos:admin_productos_list') # Fallback si no hay producto
        else:
            messages.error(request, 'Error al actualizar la variación de producto. Revisa los campos.')
            print("Errores del formulario:", form.errors) # <-- Asegúrate de que esta línea está aquí
    else:
        form = VariacionProductoForm(instance=variacion)
    return render(request, 'productos/admin/variacion_producto_form.html', {
        'form': form,
        'variacion': variacion,
        'action': 'edit'
    })

@login_required
@user_passes_test(is_staff_check)
def admin_variacion_producto_delete(request, pk):
    variacion = get_object_or_404(VariacionProducto, pk=pk)
    producto_pk = variacion.producto.pk if variacion.producto else None
    if request.method == 'POST':
        variacion_nombre = str(variacion)
        variacion.delete()
        messages.success(request, f'Variación de producto "{variacion_nombre}" eliminada exitosamente.')
        if producto_pk:
            return redirect('productos:admin_variaciones_producto_list_by_product', producto_pk=producto_pk)
        return redirect('productos:admin_productos_list') # Fallback
    messages.error(request, 'Método no permitido para eliminar. Se requiere una solicitud POST.')
    if producto_pk:
        return redirect('productos:admin_variaciones_producto_list', producto_pk=producto_pk)
    return redirect('productos:admin_productos_list') # Fallback


# --------------------------------------------------------------------------
# Vistas de Administración para IMAGENES DE PRODUCTO (CRUD) - NUEVAS
# --------------------------------------------------------------------------

@login_required
@user_passes_test(is_staff_check)
def admin_imagenes_producto_list(request, producto_pk=None):
    if producto_pk:
        producto = get_object_or_404(Producto, pk=producto_pk)
        imagenes = producto.imagenes.all().order_by('orden')
        return render(request, 'productos/admin/imagenes_producto_list.html', {
            'imagenes': imagenes,
            'producto': producto
        })
    else:
        imagenes = ImagenProducto.objects.all().order_by('producto__nombre', 'orden')
        return render(request, 'productos/admin/imagenes_producto_list.html', {
            'imagenes': imagenes
        })

@login_required
@user_passes_test(is_staff_check)
def admin_imagen_producto_create(request, producto_pk=None):
    initial_data = {}
    producto_instance = None
    if producto_pk:
        producto_instance = get_object_or_404(Producto, pk=producto_pk)
        initial_data['producto'] = producto_instance

    if request.method == 'POST':
        form = ImagenProductoForm(request.POST, request.FILES, initial=initial_data)
        if form.is_valid():
            imagen_producto = form.save()
            messages.success(request, f'Imagen para "{imagen_producto.producto.nombre}" creada exitosamente.')
            if producto_pk:
                return redirect('productos:admin_imagenes_producto_list_by_product', producto_pk=producto_pk)
            return redirect('productos:admin_productos_list') # O a una lista general de imágenes
        else:
            messages.error(request, 'Error al crear la imagen de producto. Revisa los campos.')
            print("Errores del formulario:", form.errors) # <-- Asegúrate de que esta línea está aquí
    
    else:
        form = ImagenProductoForm(initial=initial_data)

    return render(request, 'productos/admin/imagen_producto_form.html', {
        'form': form,
        'action': 'create',
        'producto': producto_instance
    })

@login_required
@user_passes_test(is_staff_check)
def admin_imagen_producto_edit(request, pk):
    imagen = get_object_or_404(ImagenProducto, pk=pk)
    if request.method == 'POST':
        form = ImagenProductoForm(request.POST, request.FILES, instance=imagen)
        if form.is_valid():
            imagen = form.save()
            messages.success(request, f'Imagen para "{imagen.producto.nombre}" actualizada exitosamente.')
            if imagen.producto:
                return redirect('productos:admin_imagenes_producto_list_by_product', producto_pk=imagen.producto.pk)
            return redirect('productos:admin_productos_list') # Fallback
        else:
            messages.error(request, 'Error al actualizar la imagen de producto. Revisa los campos.')
    else:
        form = ImagenProductoForm(instance=imagen)
    return render(request, 'productos/admin/imagen_producto_form.html', {
        'form': form,
        'imagen': imagen,
        'action': 'edit'
    })

@login_required
@user_passes_test(is_staff_check)
def admin_imagen_producto_delete(request, pk):
    imagen = get_object_or_404(ImagenProducto, pk=pk)
    producto_pk = imagen.producto.pk if imagen.producto else None
    if request.method == 'POST':
        imagen_producto_nombre = str(imagen)
        imagen.delete()
        messages.success(request, f'Imagen "{imagen_producto_nombre}" eliminada exitosamente.')
        if producto_pk:
            return redirect('productos:admin_imagenes_producto_list_by_product', producto_pk=producto_pk)
        return redirect('productos:admin_productos_list') # Fallback
    messages.error(request, 'Método no permitido para eliminar. Se requiere una solicitud POST.')
    if producto_pk:
        return redirect('productos:admin_imagenes_producto_list', producto_pk=producto_pk)
    return redirect('productos:admin_productos_list') # Fallback



# --------------------------------------------------------------------------
# Vistas para Reportes (Excel y PDF)
# --------------------------------------------------------------------------

@login_required
@user_passes_test(is_staff_check)
def reportes_productos1(request):
    productos = Producto.objects.all()
    variaciones = VariacionProducto.objects.all()

    productos_filtrados = ProductoFilter(request.GET, queryset=productos).qs
    variaciones_filtradas = VariacionProductoFilter(request.GET, queryset=variaciones).qs

    # Tablas para la vista web o para exportaciones generales (Excel/CSV)
    productos_table_web = ProductoTable(productos_filtrados)
    variaciones_table_web = VariacionProductoTable(variaciones_filtradas)

    export_format = request.GET.get('_export', None)
    
    # --- DEFINICIÓN DE CSS_STRING (Accesible para todas las exportaciones de PDF) ---
    css_string = f"""
    @font-face {{
        font-family: 'bootstrap-icons';
        src: url('{settings.STATIC_URL}fonts/bootstrap-icons.woff2') format('woff2');
        font-weight: normal;
        font-style: normal;
    }}

    body {{ 
        font-family: sans-serif; 
        margin: 10mm; /* Márgenes uniformes de 10mm */
        font-size: 7pt; /* Tamaño de fuente aún más pequeño */
    }}
    h1 {{ text-align: center; color: #333; margin-bottom: 15px; font-size: 14pt; }}
    table {{ 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 10px; 
        table-layout: fixed; /* Fuerza el diseño de tabla fijo */
    }}
    th, td {{ 
        border: 1px solid #ddd; 
        padding: 3px; 
        text-align: left; 
        vertical-align: middle;
        word-wrap: break-word; 
        box-sizing: border-box; 
    }}
    th {{ 
        background-color: #f2f2f2; 
        font-weight: bold; 
        text-align: center; 
        padding: 5px 3px; 
    }}

    /* --- ANCHOS EXPLÍCITOS PARA CADA COLUMNA (8 COLUMNAS) --- */
    th:nth-child(1), td:nth-child(1) {{ width: 5%; }}  /* ID */
    th:nth-child(2), td:nth-child(2) {{ width: 20%; }} /* Nombre */
    th:nth-child(3), td:nth-child(3) {{ width: 14%; }} /* Categoria */
    th:nth-child(4), td:nth-child(4) {{ width: 14%; }} /* Marca */
    th:nth-child(5), td:nth-child(5) {{ width: 9%; }}  /* Precio */
    th:nth-child(6), td:nth-child(6) {{ width: 9%; }}  /* Stock Total */
    th:nth-child(7), td:nth-child(7) {{ width: 9%; }}  /* Disponible */
    th:nth-child(8), td:nth-child(8) {{ width: 20%; }} /* Es destacado (para acomodar el header) */

    /* Estilos para badges (etiquetas de stock) */
    .badge {{
        display: inline-block;
        padding: .15em .3em; 
        font-size: .6em; 
        font-weight: 700;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: middle;
        border-radius: .2rem;
    }}
    .bg-success {{ background-color: #28a745 !important; }}
    .bg-warning {{ background-color: #ffc107 !important; color: #212529 !important; }} 
    .bg-danger {{ background-color: #dc3545 !important; }}

    /* Estilos para iconos */
    .bi {{
        font-family: 'bootstrap-icons' !important;
        font-style: normal;
        font-weight: normal;
        font-variant: normal;
        text-transform: none;
        line-height: 1;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-size: 1em; 
        vertical-align: middle;
    }}
    .bi-check-circle-fill::before {{ content: "\\F26A"; }} 
    .bi-x-circle-fill::before {{ content: "\\F4A9"; }}   
    .bi-star-fill::before {{ content: "\\F586"; }}      
    .bi-star::before {{ content: "\\F585"; }}          
    
    .text-success {{ color: #28a745 !important; }}
    .text-danger {{ color: #dc3545 !important; }}
    .text-warning {{ color: #ffc107 !important; }}

    /* Si tienes imágenes en las variaciones */
    img.img-thumbnail {{
        width: 30px; 
        height: 30px; 
        object-fit: cover;
        border-radius: 3px;
    }}
    """
    # --- FIN DE LA DEFINICIÓN DE CSS_STRING ---

    if export_format:
        if export_format == 'excel_productos':
            exporter = TableExport('xlsx', productos_table_web) 
            return exporter.response('listado_productos.xlsx')
        elif export_format == 'csv_productos':
            exporter = TableExport('csv', productos_table_web) 
            return exporter.response('listado_productos.csv')
        elif export_format == 'excel_variaciones':
            exporter = TableExport('xlsx', variaciones_table_web) 
            return exporter.response('listado_variaciones.xlsx')
        elif export_format == 'csv_variaciones':
            exporter = TableExport('csv', variaciones_table_web) 
            return exporter.response('listado_variaciones.csv')
        elif export_format == 'pdf_productos':
            # DEFINICIÓN DE TABLA ESPECÍFICA PARA PDF SIN COLUMNA DE ACCIONES
            class ProductoTablePDF(ProductoTable):
                class Meta(ProductoTable.Meta):
                    model = Producto
                    exclude = ('acciones',) 
                    fields = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')
                    sequence = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')

            productos_table_for_pdf = ProductoTablePDF(productos_filtrados) 
            context = {'table': productos_table_for_pdf} 

            html_string = render_to_string('productos/admin/reporte_productos_pdf.html', context, request=request)
            
            response = HttpResponse(content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="listado_productos.pdf"'
            
            HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
            return response

        elif export_format == 'pdf_variaciones':
            # DEFINICIÓN DE TABLA ESPECÍFICA PARA PDF SIN COLUMNA DE ACCIONES
            class VariacionProductoTablePDF(VariacionProductoTable):
                class Meta(VariacionProductoTable.Meta):
                    model = VariacionProducto
                    exclude = ('acciones',) 
                    fields = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')
                    sequence = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')

            variaciones_table_for_pdf = VariacionProductoTablePDF(variaciones_filtradas) 
            context = {'table': variaciones_table_for_pdf} 

            html_string = render_to_string('productos/admin/reporte_variaciones_pdf.html', context, request=request)
            
            response = HttpResponse(content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="listado_variaciones.pdf"'
            
            HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
            return response

    # Renderizar la plantilla HTML si no es una solicitud de exportación
    context = {
        'productos_table': productos_table_web,
        'variaciones_table': variaciones_table_web,
        'filter_productos': ProductoFilter(request.GET, queryset=productos),
        'filter_variaciones': VariacionProductoFilter(request.GET, queryset=variaciones),
    }
    return render(request, 'productos/admin/reportes.html', context)



@login_required
@user_passes_test(is_staff_check)
def reportes_productos_anterior(request):
    
    current_datetime_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Nueva línea: Formato YYYYMMDD_HHMMSS
    
    # --- CONSOLIDACIÓN DEL CSS_STRING PARA WEASYPRINT (definido una sola vez) ---
    css_string = f"""
    @font-face {{
        font-family: 'bootstrap-icons';
        src: url('{settings.STATIC_URL}fonts/bootstrap-icons.woff2') format('woff2');
        font-weight: normal;
        font-style: normal;
    }}
    body {{
        font-family: sans-serif;
        margin: 8mm 5mm;
        font-size: 7pt;
    }}
    h1 {{ text-align: center; color: #333; margin-bottom: 15px; font-size: 14pt; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        table-layout: fixed;
    }}
    th, td {{
        border: 1px solid #ddd;
        padding: 3px;
        text-align: left;
        vertical-align: middle;
        word-wrap: break-word;
        box-sizing: border-box;
    }}
    th {{
        background-color: #f2f2f2;
        font-weight: bold;
        text-align: center;
        padding: 5px 3px;
    }}

    /* Anchos para la tabla de Productos PDF (sin 'Acciones') */
    .table-productos-pdf th:nth-child(1), .table-productos-pdf td:nth-child(1) {{ width: 5%; }}  /* ID */
    .table-productos-pdf th:nth-child(2), .table-productos-pdf td:nth-child(2) {{ width: 20%; }} /* Nombre */
    .table-productos-pdf th:nth-child(3), .table-productos-pdf td:nth-child(3) {{ width: 14%; }} /* Categoria */
    .table-productos-pdf th:nth-child(4), .table-productos-pdf td:nth-child(4) {{ width: 14%; }} /* Marca */
    .table-productos-pdf th:nth-child(5), .table-productos-pdf td:nth-child(5) {{ width: 9%; }}  /* Precio */
    .table-productos-pdf th:nth-child(6), .table-productos-pdf td:nth-child(6) {{ width: 9%; }}  /* Stock Total */
    .table-productos-pdf th:nth-child(7), .table-productos-pdf td:nth-child(7) {{ width: 9%; }}  /* Disponible */
    .table-productos-pdf th:nth-child(8), .table-productos-pdf td:nth-child(8) {{ width: 20%; }} /* Es destacado */

    /* Anchos para la tabla de Variaciones PDF (sin 'Acciones') */
    .table-variaciones-pdf th:nth-child(1), .table-variaciones-pdf td:nth-child(1) {{ width: 5%; }}  /* ID */
    .table-variaciones-pdf th:nth-child(2), .table-variaciones-pdf td:nth-child(2) {{ width: 18%; }} /* Producto */
    .table-variaciones-pdf th:nth-child(3), .table-variaciones-pdf td:nth-child(3) {{ width: 20%; }} /* Valores Display */
    .table-variaciones-pdf th:nth-child(4), .table-variaciones-pdf td:nth-child(4) {{ width: 12%; }} /* SKU */
    .table-variaciones-pdf th:nth-child(5), .table-variaciones-pdf td:nth-child(5) {{ width: 8%; }}  /* Stock */
    .table-variaciones-pdf th:nth-child(6), .table-variaciones-pdf td:nth-child(6) {{ width: 10%; }} /* Precio Adicional */
    .table-variaciones-pdf th:nth-child(7), .table-variaciones-pdf td:nth-child(7) {{ width: 12%; }} /* Imagen */
    .table-variaciones-pdf th:nth-child(8), .table-variaciones-pdf td:nth-child(8) {{ width: 10%; }} /* Activo */

    /* Estilos para badges (etiquetas de stock) */
    .badge {{
        display: inline-block;
        padding: .15em .3em;
        font-size: .6em;
        font-weight: 700;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: middle;
        border-radius: .2rem;
    }}
    .bg-success {{ background-color: #28a745 !important; }}
    .bg-warning {{ background-color: #ffc107 !important; color: #212529 !important; }}
    .bg-danger {{ background-color: #dc3545 !important; }}

    /* Estilos para iconos */
    .bi {{
        font-family: 'bootstrap-icons' !important;
        font-style: normal;
        font-weight: normal;
        font-variant: normal;
        text-transform: none;
        line-height: 1;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-size: 1em;
        vertical-align: middle;
    }}
    .bi-check-circle-fill::before {{ content: "\\F26A"; }}
    .bi-x-circle-fill::before {{ content: "\\F4A9"; }}
    .bi-star-fill::before {{ content: "\\F586"; }}
    .bi-star::before {{ content: "\\F585"; }}

    .text-success {{ color: #28a745 !important; }}
    .text-danger {{ color: #dc3545 !important; }}
    .text-warning {{ color: #ffc107 !important; }}

    /* Si tienes imágenes en las variaciones */
    img.img-thumbnail {{
        width: 30px;
        height: 30px;
        object-fit: cover;
        border-radius: 3px;
    }}
    """
    # --- FIN DE LA CONSOLIDACIÓN DEL CSS_STRING ---

    # Obtener todos los productos y variaciones
    productos_queryset = Producto.objects.all()
    variaciones_queryset = VariacionProducto.objects.all()

    # Aplicar filtros
    producto_filter = ProductoFilter(request.GET, queryset=productos_queryset)
    variacion_filter = VariacionProductoFilter(request.GET, queryset=variaciones_queryset)

    # Crear instancias de las tablas para la VISTA WEB (con paginación y acciones)
    productos_table_web = ProductoTable(producto_filter.qs)
    variaciones_table_web = VariacionProductoTable(variacion_filter.qs)

    # Habilitar paginación SOLO para la vista web
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(productos_table_web)
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(variaciones_table_web)

    export_format = request.GET.get('_export', None)
    
    # Manejar la exportación
    if export_format:
        try:
            # Exportación de Productos (Excel/CSV)
            if export_format == 'xlsx_productos':
                exporter = TableExport('xlsx', productos_table_web)
                #return exporter.response('listado_productos.xlsx')
                return exporter.response(f'listado_productos_{current_datetime_str}.xlsx')
            
            elif export_format == 'csv_productos':
                exporter = TableExport('csv', productos_table_web)
                #return exporter.response('listado_productos.csv')
                return exporter.response(f'listado_productos_{current_datetime_str}.csv')
            
            elif export_format == 'pdf_productos':
                # Definición de la tabla específica para PDF de Productos (sin columna 'acciones')
                class ProductoTablePDF(ProductoTable):
                    class Meta(ProductoTable.Meta):
                        model = Producto
                        exclude = ('acciones',) # Excluir la columna de acciones para el PDF
                        # Asegúrate de que los campos aquí coincidan con el orden de tu CSS
                        fields = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')
                        sequence = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')
                
                # Crear una instancia de la tabla PDF con el queryset filtrado (sin paginar)
                productos_table_for_pdf = ProductoTablePDF(producto_filter.qs) 
                # Pasar contexto adicional para el PDF (como un título)
                context_pdf = {'table': productos_table_for_pdf, 'table_class': 'table-productos-pdf', 'title': 'Listado de Productos'}

                html_string = render_to_string('productos/admin/reporte_productos_pdf.html', context_pdf, request=request)
                
                response = HttpResponse(content_type="application/pdf")
                #response['Content-Disposition'] = 'attachment; filename="listado_productos.pdf"'
                response['Content-Disposition'] = f'attachment; filename="listado_productos_{current_datetime_str}.pdf"'
                
                HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
                return response

            # Exportación de Variaciones de Producto (Excel/CSV)
            elif export_format == 'xlsx_variaciones':
                exporter = TableExport('xlsx', variaciones_table_web)
                #return exporter.response('listado_variaciones.xlsx')
                return exporter.response(f'listado_variaciones_{current_datetime_str}.xlsx')
            
            elif export_format == 'csv_variaciones':
                exporter = TableExport('csv', variaciones_table_web)
                #return exporter.response('listado_variaciones.csv')
                return exporter.response(f'listado_variaciones_{current_datetime_str}.csv')
            
            elif export_format == 'pdf_variaciones':
                # Definición de la tabla específica para PDF de Variaciones (sin columna 'acciones')
                class VariacionProductoTablePDF(VariacionProductoTable):
                    class Meta(VariacionProductoTable.Meta):
                        model = VariacionProducto
                        exclude = ('acciones',) # Excluir la columna de acciones para el PDF
                        # Asegúrate de que los campos aquí coincidan con el orden de tu CSS
                        fields = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')
                        sequence = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')
                
                # Crear una instancia de la tabla PDF con el queryset filtrado (sin paginar)
                variaciones_table_for_pdf = VariacionProductoTablePDF(variacion_filter.qs) 
                # Pasar contexto adicional para el PDF (como un título)
                context_pdf = {'table': variaciones_table_for_pdf, 'table_class': 'table-variaciones-pdf', 'title': 'Listado de Variaciones de Producto'}
                
                html_string = render_to_string('productos/admin/reporte_variaciones_pdf.html', context_pdf, request=request)
                
                response = HttpResponse(content_type="application/pdf")
                #response['Content-Disposition'] = 'attachment; filename="listado_variaciones.pdf"'
                response['Content-Disposition'] = f'attachment; filename="listado_variaciones_{current_datetime_str}.pdf"'
                
                HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
                return response
            
        except Exception as e:
            # Captura cualquier error durante la exportación y lo loguea
            logger.error(f"Error durante la exportación en reportes_productos: {e}", exc_info=True)
            # Retorna una respuesta de error al usuario
            return HttpResponse(f"Hubo un error al intentar generar el archivo. Por favor, revisa los logs del servidor para más detalles. Error: {e}", status=500)

    # Renderizar la plantilla HTML si no es una solicitud de exportación
    context = {
        'productos_table': productos_table_web, # Pasar la tabla paginada para la web
        'variaciones_table': variaciones_table_web, # Pasar la tabla paginada para la web
        'producto_filter': producto_filter, # Pasar los filtros al contexto para el formulario HTML
        'variacion_filter': variacion_filter,
    }
    return render(request, 'productos/admin/reportes.html', context)




@login_required
@user_passes_test(is_staff_check)
def reportes_productos4(request):
    # Obtener todos los productos y variaciones
    productos_queryset = Producto.objects.all()
    variaciones_queryset = VariacionProducto.objects.all()

    # Aplicar filtros si existen (opcional, si quieres filtros en la página de reportes)
    producto_filter = ProductoFilter(request.GET, queryset=productos_queryset)
    variacion_filter = VariacionProductoFilter(request.GET, queryset=variaciones_queryset)

    # Crear instancias de las tablas
    productos_table = ProductoTable(producto_filter.qs)
    variaciones_table = VariacionProductoTable(variacion_filter.qs)

    # Habilitar paginación (opcional)
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(productos_table)
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(variaciones_table)

    # Manejar la exportación
    export_format = request.GET.get('_export', None)
    if export_format:
        # Aquí se crea un exportador para cada tabla.
        # Puedes decidir si quieres un solo archivo con varias hojas, o archivos separados.
        # Por simplicidad, haremos archivos separados por ahora.
        # Si quieres un solo archivo Excel con múltiples hojas, necesitarías un enfoque más manual.
        
        # Exportación de Productos
        if export_format == 'xlsx_productos':
            exporter = TableExport('xlsx', productos_table)
            return exporter.response('listado_productos.xlsx')
        elif export_format == 'csv_productos':
            exporter = TableExport('csv', productos_table)
            return exporter.response('listado_productos.csv')
        elif export_format == 'pdf_productos':
            # Renderizar la tabla a HTML
            context = {'table': productos_table}
            #html_string = render_to_string('productos/admin/reporte_productos_pdf.html', context)
            html_string = render_to_string('productos/admin/reporte_productos_pdf.html', context, request=request) # <-- Añade 'request=request'
            
            # Generar PDF con WeasyPrint
            response = HttpResponse(content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="listado_productos.pdf"'
            
            # Puedes añadir estilos CSS directamente aquí o desde un archivo estático
            # Para estilos, lo ideal es tener un archivo CSS para impresión
            # --- CSS MEJORADO PARA WEASYPRINT (CON ANCHOS FIJOS Y SIN COLUMNA DE ACCIONES) ---
            css_string = f"""
            @font-face {{
                font-family: 'bootstrap-icons';
                src: url('{settings.STATIC_URL}fonts/bootstrap-icons.woff2') format('woff2');
                font-weight: normal;
                font-style: normal;
            }}

            body {{ 
                font-family: sans-serif; 
                margin: 8mm 5mm; /* Márgenes ajustados: 8mm arriba/abajo, 5mm izquierda/derecha */
                font-size: 7pt; /* Tamaño de fuente aún más pequeño */
            }}
            h1 {{ text-align: center; color: #333; margin-bottom: 15px; font-size: 14pt; }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 10px; 
                table-layout: fixed; /* Fuerza el diseño de tabla fijo */
            }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 3px; 
                text-align: left; 
                vertical-align: middle;
                word-wrap: break-word; 
                box-sizing: border-box; 
            }}
            th {{ 
                background-color: #f2f2f2; 
                font-weight: bold; 
                text-align: center; 
                padding: 5px 3px; 
            }}

            /* --- ANCHOS EXPLÍCITOS PARA CADA COLUMNA (8 COLUMNAS DESPUÉS DE EXCLUIR 'Acciones') --- */
            th:nth-child(1), td:nth-child(1) {{ width: 5%; }}  /* ID */
            th:nth-child(2), td:nth-child(2) {{ width: 20%; }} /* Nombre */
            th:nth-child(3), td:nth-child(3) {{ width: 14%; }} /* Categoria */
            th:nth-child(4), td:nth-child(4) {{ width: 14%; }} /* Marca */
            th:nth-child(5), td:nth-child(5) {{ width: 9%; }}  /* Precio */
            th:nth-child(6), td:nth-child(6) {{ width: 9%; }}  /* Stock Total */
            th:nth-child(7), td:nth-child(7) {{ width: 9%; }}  /* Disponible */
            th:nth-child(8), td:nth-child(8) {{ width: 20%; }} /* Es destacado (dado que el header es largo) */

            /* Estilos para badges (etiquetas de stock) */
            .badge {{
                display: inline-block;
                padding: .15em .3em; 
                font-size: .6em; 
                font-weight: 700;
                line-height: 1;
                color: #fff;
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
                border-radius: .2rem;
            }}
            .bg-success {{ background-color: #28a745 !important; }}
            .bg-warning {{ background-color: #ffc107 !important; color: #212529 !important; }} 
            .bg-danger {{ background-color: #dc3545 !important; }}
            
            /* Estilos para iconos */
            .bi {{
                font-family: 'bootstrap-icons' !important;
                font-style: normal;
                font-weight: normal;
                font-variant: normal;
                text-transform: none;
                line-height: 1;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                font-size: 1em; 
                vertical-align: middle;
            }}
            .bi-check-circle-fill::before {{ content: "\\F26A"; }} 
            .bi-x-circle-fill::before {{ content: "\\F4A9"; }}   
            .bi-star-fill::before {{ content: "\\F586"; }}      
            .bi-star::before {{ content: "\\F585"; }}          
            
            .text-success {{ color: #28a745 !important; }}
            .text-danger {{ color: #dc3545 !important; }}
            .text-warning {{ color: #ffc107 !important; }}

            /* Si tienes imágenes en las variaciones */
            img.img-thumbnail {{
                width: 30px; 
                height: 30px; 
                object-fit: cover;
                border-radius: 3px;
            }}
            """
            HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
            return response

        # Exportación de Variaciones de Producto
        elif export_format == 'xlsx_variaciones':
            exporter = TableExport('xlsx', variaciones_table)
            return exporter.response('listado_variaciones.xlsx')
        elif export_format == 'csv_variaciones':
            exporter = TableExport('csv', variaciones_table)
            return exporter.response('listado_variaciones.csv')
        elif export_format == 'pdf_variaciones':
            context = {'table': variaciones_table}
            #html_string = render_to_string('productos/admin/reporte_variaciones_pdf.html', context)
            html_string = render_to_string('productos/admin/reporte_variaciones_pdf.html', context, request=request) # <-- Añade 'request=request'
            
            response = HttpResponse(content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="listado_variaciones.pdf"'
            # --- CSS MEJORADO PARA WEASYPRINT (CON ANCHOS FIJOS Y SIN COLUMNA DE ACCIONES) ---
            css_string = f"""
            @font-face {{
                font-family: 'bootstrap-icons';
                src: url('{settings.STATIC_URL}fonts/bootstrap-icons.woff2') format('woff2');
                font-weight: normal;
                font-style: normal;
            }}
            
            body {{ 
                font-family: sans-serif; 
                margin: 8mm 5mm; /* Márgenes ajustados: 8mm arriba/abajo, 5mm izquierda/derecha */
                font-size: 7pt; /* Tamaño de fuente aún más pequeño */
            }}
            h1 {{ text-align: center; color: #333; margin-bottom: 15px; font-size: 14pt; }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 10px; 
                table-layout: fixed; /* Fuerza el diseño de tabla fijo */
            }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 3px; 
                text-align: left; 
                vertical-align: middle;
                word-wrap: break-word; 
                box-sizing: border-box; 
            }}
            th {{ 
                background-color: #f2f2f2; 
                font-weight: bold; 
                text-align: center; 
                padding: 5px 3px; 
            }}

            /* --- ANCHOS EXPLÍCITOS PARA CADA COLUMNA (8 COLUMNAS DESPUÉS DE EXCLUIR 'Acciones') --- */
            th:nth-child(1), td:nth-child(1) {{ width: 5%; }}  /* ID */
            th:nth-child(2), td:nth-child(2) {{ width: 20%; }} /* Nombre */
            th:nth-child(3), td:nth-child(3) {{ width: 14%; }} /* Categoria */
            th:nth-child(4), td:nth-child(4) {{ width: 14%; }} /* Marca */
            th:nth-child(5), td:nth-child(5) {{ width: 9%; }}  /* Precio */
            th:nth-child(6), td:nth-child(6) {{ width: 9%; }}  /* Stock Total */
            th:nth-child(7), td:nth-child(7) {{ width: 9%; }}  /* Disponible */
            th:nth-child(8), td:nth-child(8) {{ width: 20%; }} /* Es destacado (dado que el header es largo) */
            
            /* Estilos para badges (etiquetas de stock) */
            .badge {{
                display: inline-block;
                padding: .15em .3em; 
                font-size: .6em; 
                font-weight: 700;
                line-height: 1;
                color: #fff;
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
                border-radius: .2rem;
            }}
            .bg-success {{ background-color: #28a745 !important; }}
            .bg-warning {{ background-color: #ffc107 !important; color: #212529 !important; }} 
            .bg-danger {{ background-color: #dc3545 !important; }}

            /* Estilos para iconos */
            .bi {{
                font-family: 'bootstrap-icons' !important;
                font-style: normal;
                font-weight: normal;
                font-variant: normal;
                text-transform: none;
                line-height: 1;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                font-size: 1em; 
                vertical-align: middle;
            }}
            .bi-check-circle-fill::before {{ content: "\\F26A"; }} 
            .bi-x-circle-fill::before {{ content: "\\F4A9"; }}   
            .bi-star-fill::before {{ content: "\\F586"; }}      
            .bi-star::before {{ content: "\\F585"; }}          
            
            .text-success {{ color: #28a745 !important; }}
            .text-danger {{ color: #dc3545 !important; }}
            .text-warning {{ color: #ffc107 !important; }}

            /* Si tienes imágenes en las variaciones */
            img.img-thumbnail {{
                width: 30px; 
                height: 30px; 
                object-fit: cover;
                border-radius: 3px;
            }}
            """
            HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
            return response
    

    context = {
        'productos_table': productos_table,
        'variaciones_table': variaciones_table,
        'producto_filter': producto_filter, # Pasar los filtros al contexto
        'variacion_filter': variacion_filter,
    }
    return render(request, 'productos/admin/reportes.html', context)



@login_required
@user_passes_test(is_staff_check)
def reportes_productos3(request):
    # Obtener todos los productos y variaciones
    productos_queryset = Producto.objects.all()
    variaciones_queryset = VariacionProducto.objects.all()

    # Aplicar filtros
    producto_filter = ProductoFilter(request.GET, queryset=productos_queryset)
    variacion_filter = VariacionProductoFilter(request.GET, queryset=variaciones_queryset)

    # Crear instancias de las tablas para la VISTA WEB (con paginación y acciones)
    productos_table_web = ProductoTable(producto_filter.qs)
    variaciones_table_web = VariacionProductoTable(variacion_filter.qs)

    # Habilitar paginación SOLO para la vista web
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(productos_table_web)
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(variaciones_table_web)

    export_format = request.GET.get('_export', None)
    
    # --- DEFINICIÓN DE CSS_STRING (Movido al principio de la función para ser global) ---
    css_string = f"""
    @font-face {{
        font-family: 'bootstrap-icons';
        src: url('{settings.STATIC_URL}fonts/bootstrap-icons.woff2') format('woff2');
        font-weight: normal;
        font-style: normal;
    }}

    body {{ 
        font-family: sans-serif; 
        margin: 8mm 5mm; /* Márgenes ajustados: 8mm arriba/abajo, 5mm izquierda/derecha */
        font-size: 7pt; /* Tamaño de fuente aún más pequeño */
    }}
    h1 {{ text-align: center; color: #333; margin-bottom: 15px; font-size: 14pt; }}
    table {{ 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 10px; 
        table-layout: fixed; /* Fuerza el diseño de tabla fijo */
    }}
    th, td {{ 
        border: 1px solid #ddd; 
        padding: 3px; 
        text-align: left; 
        vertical-align: middle;
        word-wrap: break-word; 
        box-sizing: border-box; 
    }}
    th {{ 
        background-color: #f2f2f2; 
        font-weight: bold; 
        text-align: center; 
        padding: 5px 3px; 
    }}

    /* --- ANCHOS EXPLÍCITOS PARA CADA COLUMNA (Para PDFs sin 'Acciones') --- */
    /* Anchos para la tabla de Productos (8 columnas: ID, Nombre, Categoria, Marca, Precio, Stock Total, Disponible, Es destacado) */
    .table-productos-pdf th:nth-child(1), .table-productos-pdf td:nth-child(1) {{ width: 5%; }}  /* ID */
    .table-productos-pdf th:nth-child(2), .table-productos-pdf td:nth-child(2) {{ width: 20%; }} /* Nombre */
    .table-productos-pdf th:nth-child(3), .table-productos-pdf td:nth-child(3) {{ width: 14%; }} /* Categoria */
    .table-productos-pdf th:nth-child(4), .table-productos-pdf td:nth-child(4) {{ width: 14%; }} /* Marca */
    .table-productos-pdf th:nth-child(5), .table-productos-pdf td:nth-child(5) {{ width: 9%; }}  /* Precio */
    .table-productos-pdf th:nth-child(6), .table-productos-pdf td:nth-child(6) {{ width: 9%; }}  /* Stock Total */
    .table-productos-pdf th:nth-child(7), .table-productos-pdf td:nth-child(7) {{ width: 9%; }}  /* Disponible */
    .table-productos-pdf th:nth-child(8), .table-productos-pdf td:nth-child(8) {{ width: 20%; }} /* Es destacado */

    /* Anchos para la tabla de Variaciones (8 columnas: ID, Producto, Valores, SKU, Stock, Precio Adicional, Imagen, Activo) */
    .table-variaciones-pdf th:nth-child(1), .table-variaciones-pdf td:nth-child(1) {{ width: 5%; }}  /* ID */
    .table-variaciones-pdf th:nth-child(2), .table-variaciones-pdf td:nth-child(2) {{ width: 18%; }} /* Producto */
    .table-variaciones-pdf th:nth-child(3), .table-variaciones-pdf td:nth-child(3) {{ width: 20%; }} /* Valores Display */
    .table-variaciones-pdf th:nth-child(4), .table-variaciones-pdf td:nth-child(4) {{ width: 12%; }} /* SKU */
    .table-variaciones-pdf th:nth-child(5), .table-variaciones-pdf td:nth-child(5) {{ width: 8%; }}  /* Stock */
    .table-variaciones-pdf th:nth-child(6), .table-variaciones-pdf td:nth-child(6) {{ width: 10%; }} /* Precio Adicional */
    .table-variaciones-pdf th:nth-child(7), .table-variaciones-pdf td:nth-child(7) {{ width: 12%; }} /* Imagen */
    .table-variaciones-pdf th:nth-child(8), .table-variaciones-pdf td:nth-child(8) {{ width: 10%; }} /* Activo */

    /* Estilos para badges (etiquetas de stock) */
    .badge {{
        display: inline-block;
        padding: .15em .3em; 
        font-size: .6em; 
        font-weight: 700;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: middle;
        border-radius: .2rem;
    }}
    .bg-success {{ background-color: #28a745 !important; }}
    .bg-warning {{ background-color: #ffc107 !important; color: #212529 !important; }} 
    .bg-danger {{ background-color: #dc3545 !important; }}

    /* Estilos para iconos */
    .bi {{
        font-family: 'bootstrap-icons' !important;
        font-style: normal;
        font-weight: normal;
        font-variant: normal;
        text-transform: none;
        line-height: 1;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-size: 1em; 
        vertical-align: middle;
    }}
    .bi-check-circle-fill::before {{ content: "\\F26A"; }} 
    .bi-x-circle-fill::before {{ content: "\\F4A9"; }}   
    .bi-star-fill::before {{ content: "\\F586"; }}      
    .bi-star::before {{ content: "\\F585"; }}          
    
    .text-success {{ color: #28a745 !important; }}
    .text-danger {{ color: #dc3545 !important; }}
    .text-warning {{ color: #ffc107 !important; }}

    /* Si tienes imágenes en las variaciones */
    img.img-thumbnail {{
        width: 30px; 
        height: 30px; 
        object-fit: cover;
        border-radius: 3px;
    }}
    """
    # --- FIN DE LA DEFINICIÓN DE CSS_STRING ---

    # Manejar la exportación
    if export_format:
        # Exportación de Productos (Excel/CSV)
        if export_format == 'xlsx_productos':
            exporter = TableExport('xlsx', productos_table_web)
            return exporter.response('listado_productos.xlsx')
        elif export_format == 'csv_productos':
            exporter = TableExport('csv', productos_table_web)
            return exporter.response('listado_productos.csv')
        elif export_format == 'pdf_productos':
            # Definición de la tabla específica para PDF de Productos (sin columna 'acciones')
            class ProductoTablePDF(ProductoTable):
                class Meta(ProductoTable.Meta):
                    model = Producto
                    exclude = ('acciones',) # Excluir la columna de acciones para el PDF
                    # Asegúrate de que los campos aquí coincidan con el orden de tu CSS
                    fields = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')
                    sequence = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')
            
            # Crear una instancia de la tabla PDF con el queryset filtrado (sin paginar)
            productos_table_for_pdf = ProductoTablePDF(producto_filter.qs) 
            context = {'table': productos_table_for_pdf, 'table_class': 'table-productos-pdf'} # Añadir clase para CSS específico

            html_string = render_to_string('productos/admin/reporte_productos_pdf.html', context, request=request)
            
            response = HttpResponse(content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="listado_productos.pdf"'
            
            HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
            return response

        # Exportación de Variaciones de Producto (Excel/CSV)
        elif export_format == 'xlsx_variaciones':
            exporter = TableExport('xlsx', variaciones_table_web)
            return exporter.response('listado_variaciones.xlsx')
        elif export_format == 'csv_variaciones':
            exporter = TableExport('csv', variaciones_table_web)
            return exporter.response('listado_variaciones.csv')
        elif export_format == 'pdf_variaciones':
            # Definición de la tabla específica para PDF de Variaciones (sin columna 'acciones')
            class VariacionProductoTablePDF(VariacionProductoTable):
                class Meta(VariacionProductoTable.Meta):
                    model = VariacionProducto
                    exclude = ('acciones',) # Excluir la columna de acciones para el PDF
                    # Asegúrate de que los campos aquí coincidan con el orden de tu CSS
                    fields = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')
                    sequence = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')
            
            # Crear una instancia de la tabla PDF con el queryset filtrado (sin paginar)
            variaciones_table_for_pdf = VariacionProductoTablePDF(variacion_filter.qs) 
            context = {'table': variaciones_table_for_pdf, 'table_class': 'table-variaciones-pdf'} # Añadir clase para CSS específico
            
            html_string = render_to_string('productos/admin/reporte_variaciones_pdf.html', context, request=request)
            
            response = HttpResponse(content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="listado_variaciones.pdf"'
            
            HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
            return response

    # Renderizar la plantilla HTML si no es una solicitud de exportación
    context = {
        'productos_table': productos_table_web, # Pasar la tabla paginada para la web
        'variaciones_table': variaciones_table_web, # Pasar la tabla paginada para la web
        'filter_productos': producto_filter, # Pasar los filtros al contexto para el formulario HTML
        'filter_variaciones': variacion_filter,
    }
    return render(request, 'productos/admin/reportes.html', context)



@login_required
@user_passes_test(is_staff_check)
def reportes_productos(request):
    
    current_datetime_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Nueva línea: Formato YYYYMMDD_HHMMSS
    
    # --- CONSOLIDACIÓN DEL CSS_STRING PARA WEASYPRINT (definido una sola vez) ---
    css_string = f"""
    @font-face {{
        font-family: 'bootstrap-icons';
        src: url('{settings.STATIC_URL}fonts/bootstrap-icons.woff2') format('woff2');
        font-weight: normal;
        font-style: normal;
    }}
    body {{
        font-family: sans-serif;
        margin: 8mm 5mm;
        font-size: 7pt;
    }}
    h1 {{ text-align: center; color: #333; margin-bottom: 15px; font-size: 14pt; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        table-layout: fixed;
    }}
    th, td {{
        border: 1px solid #ddd;
        padding: 3px;
        text-align: left;
        vertical-align: middle;
        word-wrap: break-word;
        box-sizing: border-box;
    }}
    th {{
        background-color: #f2f2f2;
        font-weight: bold;
        text-align: center;
        padding: 5px 3px;
    }}

    /* Anchos para la tabla de Productos PDF (sin 'Acciones') */
    .table-productos-pdf th:nth-child(1), .table-productos-pdf td:nth-child(1) {{ width: 5%; }}  /* ID */
    .table-productos-pdf th:nth-child(2), .table-productos-pdf td:nth-child(2) {{ width: 20%; }} /* Nombre */
    .table-productos-pdf th:nth-child(3), .table-productos-pdf td:nth-child(3) {{ width: 14%; }} /* Categoria */
    .table-productos-pdf th:nth-child(4), .table-productos-pdf td:nth-child(4) {{ width: 14%; }} /* Marca */
    .table-productos-pdf th:nth-child(5), .table-productos-pdf td:nth-child(5) {{ width: 9%; }}  /* Precio */
    .table-productos-pdf th:nth-child(6), .table-productos-pdf td:nth-child(6) {{ width: 9%; }}  /* Stock Total */
    .table-productos-pdf th:nth-child(7), .table-productos-pdf td:nth-child(7) {{ width: 9%; }}  /* Disponible */
    .table-productos-pdf th:nth-child(8), .table-productos-pdf td:nth-child(8) {{ width: 20%; }} /* Es destacado */

    /* Anchos para la tabla de Variaciones PDF (sin 'Acciones') */
    .table-variaciones-pdf th:nth-child(1), .table-variaciones-pdf td:nth-child(1) {{ width: 5%; }}  /* ID */
    .table-variaciones-pdf th:nth-child(2), .table-variaciones-pdf td:nth-child(2) {{ width: 18%; }} /* Producto */
    .table-variaciones-pdf th:nth-child(3), .table-variaciones-pdf td:nth-child(3) {{ width: 20%; }} /* Valores Display */
    .table-variaciones-pdf th:nth-child(4), .table-variaciones-pdf td:nth-child(4) {{ width: 12%; }} /* SKU */
    .table-variaciones-pdf th:nth-child(5), .table-variaciones-pdf td:nth-child(5) {{ width: 8%; }}  /* Stock */
    .table-variaciones-pdf th:nth-child(6), .table-variaciones-pdf td:nth-child(6) {{ width: 10%; }} /* Precio Adicional */
    .table-variaciones-pdf th:nth-child(7), .table-variaciones-pdf td:nth-child(7) {{ width: 12%; }} /* Imagen */
    .table-variaciones-pdf th:nth-child(8), .table-variaciones-pdf td:nth-child(8) {{ width: 10%; }} /* Activo */

    /* Estilos para badges (etiquetas de stock) */
    .badge {{
        display: inline-block;
        padding: .15em .3em;
        font-size: .6em;
        font-weight: 700;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: middle;
        border-radius: .2rem;
    }}
    .bg-success {{ background-color: #28a745 !important; }}
    .bg-warning {{ background-color: #ffc107 !important; color: #212529 !important; }}
    .bg-danger {{ background-color: #dc3545 !important; }}

    /* Estilos para iconos */
    .bi {{
        font-family: 'bootstrap-icons' !important;
        font-style: normal;
        font-weight: normal;
        font-variant: normal;
        text-transform: none;
        line-height: 1;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-size: 1em;
        vertical-align: middle;
    }}
    .bi-check-circle-fill::before {{ content: "\\F26A"; }}
    .bi-x-circle-fill::before {{ content: "\\F4A9"; }}
    .bi-star-fill::before {{ content: "\\F586"; }}
    .bi-star::before {{ content: "\\F585"; }}

    .text-success {{ color: #28a745 !important; }}
    .text-danger {{ color: #dc3545 !important; }}
    .text-warning {{ color: #ffc107 !important; }}

    /* Si tienes imágenes en las variaciones */
    img.img-thumbnail {{
        width: 30px;
        height: 30px;
        object-fit: cover;
        border-radius: 3px;
    }}
    """
    # --- FIN DE LA CONSOLIDACIÓN DEL CSS_STRING ---

    # Obtener todos los productos y variaciones
    productos_queryset = Producto.objects.all()
    variaciones_queryset = VariacionProducto.objects.all()

    # Aplicar filtros
    producto_filter = ProductoFilter(request.GET, queryset=productos_queryset)
    variacion_filter = VariacionProductoFilter(request.GET, queryset=variaciones_queryset)

    # Crear instancias de las tablas para la VISTA WEB (con paginación y acciones)
    productos_table_web = ProductoTable(producto_filter.qs)
    variaciones_table_web = VariacionProductoTable(variacion_filter.qs)

    # Habilitar paginación SOLO para la vista web
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(productos_table_web)
    tables.RequestConfig(request, paginate={'per_page': 10}).configure(variaciones_table_web)

    export_format = request.GET.get('_export', None)
    
    # Manejar la exportación
    # Manejar la exportación
    if export_format:
        try:
            # Exportación de Productos (Excel/CSV)
            if export_format == 'xlsx_productos':
                # <--- Usa ProductoTableExport aquí
                exporter = TableExport('xlsx', ProductoTableExport(producto_filter.qs))
                return exporter.response(f'listado_productos_{current_datetime_str}.xlsx')
            elif export_format == 'csv_productos':
                # <--- Usa ProductoTableExport aquí
                exporter = TableExport('csv', ProductoTableExport(producto_filter.qs))
                return exporter.response(f'listado_productos_{current_datetime_str}.csv')
            elif export_format == 'pdf_productos':
                # Este ya usa ProductoTablePDF, lo cual es correcto
                class ProductoTablePDF(ProductoTable):
                    class Meta(ProductoTable.Meta):
                        model = Producto
                        exclude = ('acciones',)
                        fields = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')
                        sequence = ('id', 'nombre', 'categoria', 'marca', 'precio', 'total_stock', 'disponible', 'es_destacado')
                
                productos_table_for_pdf = ProductoTablePDF(producto_filter.qs) 
                context_pdf = {'table': productos_table_for_pdf, 'table_class': 'table-productos-pdf', 'title': 'Listado de Productos'}

                html_string = render_to_string('productos/admin/reporte_productos_pdf.html', context_pdf, request=request)
                
                response = HttpResponse(content_type="application/pdf")
                response['Content-Disposition'] = f'attachment; filename="listado_productos_{current_datetime_str}.pdf"'
                
                HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
                return response

            # Exportación de Variaciones de Producto (Excel/CSV)
            elif export_format == 'xlsx_variaciones':
                # <--- Usa VariacionProductoTableExport aquí
                exporter = TableExport('xlsx', VariacionProductoTableExport(variacion_filter.qs))
                return exporter.response(f'listado_variaciones_{current_datetime_str}.xlsx')
            elif export_format == 'csv_variaciones':
                # <--- Usa VariacionProductoTableExport aquí
                exporter = TableExport('csv', VariacionProductoTableExport(variacion_filter.qs))
                return exporter.response(f'listado_variaciones_{current_datetime_str}.csv')
            elif export_format == 'pdf_variaciones':
                # Este ya usa VariacionProductoTablePDF, lo cual es correcto
                class VariacionProductoTablePDF(VariacionProductoTable):
                    class Meta(VariacionProductoTable.Meta):
                        model = VariacionProducto
                        exclude = ('acciones',)
                        fields = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')
                        sequence = ('id', 'producto', 'valores_display', 'sku', 'stock', 'precio_adicional', 'imagen', 'activo')
                
                variaciones_table_for_pdf = VariacionProductoTablePDF(variacion_filter.qs) 
                context_pdf = {'table': variaciones_table_for_pdf, 'table_class': 'table-variaciones-pdf', 'title': 'Listado de Variaciones de Producto'}
                
                html_string = render_to_string('productos/admin/reporte_variaciones_pdf.html', context_pdf, request=request)
                
                response = HttpResponse(content_type="application/pdf")
                response['Content-Disposition'] = f'attachment; filename="listado_variaciones_{current_datetime_str}.pdf"'
                
                HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[CSS(string=css_string)])
                return response
            
        except Exception as e:
            logger.error(f"Error durante la exportación en reportes_productos: {e}", exc_info=True)
            return HttpResponse(f"Hubo un error al intentar generar el archivo. Por favor, revisa los logs del servidor para más detalles. Error: {e}", status=500)

    # Renderizar la plantilla HTML si no es una solicitud de exportación
    context = {
        'productos_table': productos_table_web, # Pasar la tabla paginada para la web
        'variaciones_table': variaciones_table_web, # Pasar la tabla paginada para la web
        'producto_filter': producto_filter, # Pasar los filtros al contexto para el formulario HTML
        'variacion_filter': variacion_filter,
    }
    return render(request, 'productos/admin/reportes.html', context)

