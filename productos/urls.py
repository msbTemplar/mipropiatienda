# mitienda/productos/urls.py
from django.urls import path
from . import views

app_name = 'productos' # ¡IMPORTANTE: Define el app_name aquí!

urlpatterns = [
    # URLs de Listado y Detalle de Productos (Públicas)
    path('', views.productos_listado, name='productos_listado'),
    # Tu URL de detalle de producto es por slug, no por id/slug. La mantengo así:
    path('<slug:slug>/', views.producto_detalle, name='producto_detalle'), #

    # --- URLs de Administración de Productos (CRUD) ---
    path('admin/productos/', views.admin_productos_list, name='admin_productos_list'),
    path('admin/productos/crear/', views.admin_producto_create, name='admin_producto_create'),
    path('admin/productos/editar/<int:pk>/', views.admin_producto_edit, name='admin_producto_edit'),
    path('admin/productos/eliminar/<int:pk>/', views.admin_producto_delete, name='admin_producto_delete'),

    # --- URLs de Administración de Categorías (CRUD) ---
    path('admin/categorias/', views.admin_categorias_list, name='admin_categorias_list'),
    path('admin/categorias/crear/', views.admin_categoria_create, name='admin_categoria_create'),
    path('admin/categorias/editar/<int:pk>/', views.admin_categoria_edit, name='admin_categoria_edit'),
    path('admin/categorias/eliminar/<int:pk>/', views.admin_categoria_delete, name='admin_categoria_delete'),

    # --- URLs de Administración de Marcas (CRUD) ---
    path('admin/marcas/', views.admin_marcas_list, name='admin_marcas_list'),
    path('admin/marcas/crear/', views.admin_marca_create, name='admin_marca_create'),
    path('admin/marcas/editar/<int:pk>/', views.admin_marca_edit, name='admin_marca_edit'),
    path('admin/marcas/eliminar/<int:pk>/', views.admin_marca_delete, name='admin_marca_delete'),

    # --- URLs de Administración de Tipos de Variación (CRUD) ---
    path('admin/tipos-variacion/', views.admin_tipos_variacion_list, name='admin_tipos_variacion_list'),
    path('admin/tipos-variacion/crear/', views.admin_tipo_variacion_create, name='admin_tipo_variacion_create'),
    path('admin/tipos-variacion/editar/<int:pk>/', views.admin_tipo_variacion_edit, name='admin_tipo_variacion_edit'),
    path('admin/tipos-variacion/eliminar/<int:pk>/', views.admin_tipo_variacion_delete, name='admin_tipo_variacion_delete'),

    # --- URLs de Administración de Valores de Variación (CRUD) ---
    path('admin/valores-variacion/', views.admin_valores_variacion_list, name='admin_valores_variacion_list'),
    path('admin/valores-variacion/crear/', views.admin_valor_variacion_create, name='admin_valor_variacion_create'),
    path('admin/valores-variacion/editar/<int:pk>/', views.admin_valor_variacion_edit, name='admin_valor_variacion_edit'),
    path('admin/valores-variacion/eliminar/<int:pk>/', views.admin_valor_variacion_delete, name='admin_valor_variacion_delete'),

    # --- URLs de Administración de Variaciones de Producto (CRUD) ---
    path('admin/variaciones/', views.admin_variaciones_producto_list, name='admin_variaciones_producto_list'),
    path('admin/variaciones/producto/<int:producto_pk>/', views.admin_variaciones_producto_list, name='admin_variaciones_producto_list_by_product'),
    path('admin/variaciones/crear/', views.admin_variacion_producto_create, name='admin_variacion_producto_create'),
    path('admin/variaciones/crear/producto/<int:producto_pk>/', views.admin_variacion_producto_create, name='admin_variacion_producto_create_for_product'),
    path('admin/variaciones/editar/<int:pk>/', views.admin_variacion_producto_edit, name='admin_variacion_producto_edit'),
    path('admin/variaciones/eliminar/<int:pk>/', views.admin_variacion_producto_delete, name='admin_variacion_producto_delete'),

    # --- URLs de Administración de Imágenes de Producto (CRUD) ---
    path('admin/imagenes/', views.admin_imagenes_producto_list, name='admin_imagenes_producto_list'),
    path('admin/imagenes/producto/<int:producto_pk>/', views.admin_imagenes_producto_list, name='admin_imagenes_producto_list_by_product'),
    path('admin/imagenes/crear/', views.admin_imagen_producto_create, name='admin_imagen_producto_create'),
    path('admin/imagenes/crear/producto/<int:producto_pk>/', views.admin_imagen_producto_create, name='admin_imagen_producto_create_for_product'),
    path('admin/imagenes/editar/<int:pk>/', views.admin_imagen_producto_edit, name='admin_imagen_producto_edit'),
    path('admin/imagenes/eliminar/<int:pk>/', views.admin_imagen_producto_delete, name='admin_imagen_producto_delete'),
    
    # URL para la página de reportes
    path('admin/reportes/', views.reportes_productos, name='admin_reportes_productos'),


]