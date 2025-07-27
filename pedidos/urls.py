# mitienda/pedidos/urls.py
from django.urls import path
from . import views

app_name = 'pedidos' # ¡IMPORTANTE: Define el app_name aquí!

urlpatterns = [
    # URLs del Carrito
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:variacion_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    
    # URLs de Checkout y Pedido
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:pedido_id>/', views.order_confirmation, name='order_confirmation'),
    path('cancelar-pedido/<int:pedido_id>/', views.cancelar_pedido, name='cancelar_pedido'),

]