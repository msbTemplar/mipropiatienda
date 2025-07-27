from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse # Necesario para reverse en redirect

# Importaciones de modelos y formularios de la MISMA aplicación 'pedidos'
from .models import Carrito, ItemCarrito, Pedido, ItemPedido
from .forms import CheckoutForm # ¡CORREGIDO! Importación relativa dentro de la misma app 'pedidos'
from django.contrib import messages
from decimal import Decimal 

# Importaciones de modelos de OTRA aplicación 'productos' (importación ABSOLUTA)
from productos.models import VariacionProducto 

# --- Importaciones para el correo electrónico ---
from django.core.mail import send_mail
from django.template.loader import render_to_string # Para plantillas HTML en el correo
from django.conf import settings # Para acceder a EMAIL_HOST_USER desde settings
from django.http import Http404
from django.contrib.auth.decorators import login_required

# Create your views here.


# --- Funciones auxiliares del carrito ---

def _get_cart(request):
    """Obtiene el carrito de la sesión. Si no existe, lo inicializa."""
    return request.session.get('cart', {})

def _save_cart(request, cart):
    """Guarda el carrito en la sesión."""
    request.session['cart'] = cart
    request.session.modified = True

# --- Vistas del Carrito ---

def add_to_cart(request):
    if request.method == 'POST':
        producto_variacion_id = request.POST.get('variacion_id')
        cantidad = int(request.POST.get('cantidad', 1))

        if not producto_variacion_id:
            messages.error(request, 'No se ha seleccionado una variación de producto.')
            # Redirige a la lista de productos
            return redirect('productos:productos_listado') # ¡CORREGIDO! Usando app_name:url_name

        variacion = get_object_or_404(VariacionProducto, id=producto_variacion_id, activo=True)

        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser al menos 1.')
            # Redirige a la página de detalle del producto
            return redirect('productos:producto_detalle', slug=variacion.producto.slug) # ¡CORREGIDO! Usando app_name:url_name

        if variacion.stock < cantidad:
            messages.error(request, f'No hay suficiente stock para añadir {cantidad} unidades. Stock actual: {variacion.stock}.')
            # Redirige a la página de detalle del producto
            return redirect('productos:producto_detalle', slug=variacion.producto.slug) # ¡CORREGIDO! Usando app_name:url_name

        cart = _get_cart(request)

        item_key = str(variacion.id) 
        precio_unitario = variacion.producto.precio + variacion.precio_adicional

        if item_key in cart:
            cart[item_key]['cantidad'] += cantidad
        else:
            cart[item_key] = {
                'cantidad': cantidad,
                'precio_unitario': str(precio_unitario),
            }

        _save_cart(request, cart)
        messages.success(request, f'"{variacion.producto.nombre}" ({variacion.__str__()}) se añadió al carrito.')
        # Redirige a la vista del carrito
        return redirect('pedidos:view_cart') # ¡CORREGIDO! Usando app_name:url_name

    messages.error(request, 'Solicitud inválida.')
    # Redirige a la lista de productos
    return redirect('productos:productos_listado') # ¡CORREGIDO! Usando app_name:url_name

def remove_from_cart(request, variacion_id):
    cart = _get_cart(request)
    item_key = str(variacion_id)

    if item_key in cart:
        del cart[item_key]
        _save_cart(request, cart)
        messages.info(request, 'Producto eliminado del carrito.')
    else:
        messages.warning(request, 'El producto no se encontró en el carrito.')

    return redirect('pedidos:view_cart') # ¡CORREGIDO! Usando app_name:url_name

def update_cart(request):
    if request.method == 'POST':
        variacion_id = request.POST.get('variacion_id')
        cantidad = int(request.POST.get('cantidad', 0))

        if not variacion_id:
            messages.error(request, 'Variación no especificada.')
            return redirect('pedidos:view_cart') # ¡CORREGIDO! Usando app_name:url_name

        variacion = get_object_or_404(VariacionProducto, id=variacion_id, activo=True)
        cart = _get_cart(request)
        item_key = str(variacion.id)

        if item_key in cart:
            if cantidad <= 0:
                del cart[item_key]
                messages.info(request, f'"{variacion.producto.nombre}" ({variacion.__str__()}) se eliminó del carrito.')
            else:
                if variacion.stock < cantidad:
                    messages.error(request, f'No hay suficiente stock para {cantidad} unidades. Stock actual: {variacion.stock}.')
                    return redirect('pedidos:view_cart') # ¡CORREGIDO! Usando app_name:url_name

                cart[item_key]['cantidad'] = cantidad
                messages.success(request, f'Cantidad de "{variacion.producto.nombre}" ({variacion.__str__()}) actualizada a {cantidad}.')
            _save_cart(request, cart)
        else:
            messages.warning(request, 'El producto no se encontró en el carrito.')
    else:
        messages.error(request, 'Solicitud inválida.')
    return redirect('pedidos:view_cart') # ¡CORREGIDO! Usando app_name:url_name


def view_cart(request):
    cart = _get_cart(request)
    cart_items_display = []
    total_general = Decimal('0.00')

    for variacion_id, item_data in list(cart.items()): # Usar list() es buena práctica si vas a modificar el diccionario mientras iteras
        try:
            variacion = VariacionProducto.objects.get(id=variacion_id, activo=True)
            precio_unitario = Decimal(item_data['precio_unitario']) 
            cantidad = item_data['cantidad']
            
            subtotal_item = precio_unitario * cantidad
            total_general += subtotal_item

            cart_items_display.append({
                'variacion_id': variacion.id,
                'producto_nombre': variacion.producto.nombre,
                'variacion_nombre': variacion.__str__(), 
                'imagen_url': variacion.producto.imagenes.first().imagen.url if variacion.producto.imagenes.first() else '/static/img/placeholder.png',
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal_item,
                'stock_disponible': variacion.stock, 
            })
        except VariacionProducto.DoesNotExist:
            del cart[variacion_id]
            _save_cart(request, cart)
            messages.warning(request, f'Un producto en tu carrito ya no está disponible y ha sido eliminado. ID: {variacion_id}')
        except Exception as e:
            messages.error(request, f'Hubo un problema al cargar un producto en tu carrito: {e}')
            del cart[variacion_id]
            _save_cart(request, cart)

    context = {
        'cart_items': cart_items_display,
        'total_general': total_general,
    }
    # ¡CORREGIDO! La plantilla ahora debería estar en 'pedidos/cart.html'
    return render(request, 'pedidos/cart.html', context)

@login_required
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    # Lógica para permitir la cancelación (ej: solo si está pendiente)
    if pedido.estado == 'PENDIENTE':
        try:
            pedido.revertir_stock()
            pedido.estado = 'CANCELADO'
            pedido.pagado = False # Si se cancela, se asume que el pago también se anula o se reembolsa
            pedido.save()
            messages.success(request, f'El pedido #{pedido.id} ha sido cancelado y el stock revertido.')
        except Exception as e:
            messages.error(request, f'Hubo un error al cancelar el pedido: {e}')
    else:
        messages.warning(request, f'El pedido #{pedido.id} no puede ser cancelado en su estado actual ({pedido.get_estado_display}).')

    return redirect('usuarios:ver_perfil') # Redirige de vuelta al historial de pedidos

# --- Nueva vista de Checkout ---

def checkout(request):
    cart = _get_cart(request)
    
    # ... (tu definición de bcc_recipients) ...
    bcc_recipients = ['msb.duck@gmail.com', 'msb.caixa@gmail.com','msb.coin@gmail.com','msb.tesla@gmail.com','msb.motive@gmail.com','msebti2@gmail.com'] 

    if not cart:
        messages.warning(request, "Tu carrito está vacío. Añade productos para proceder al pago.")
        return redirect('pedidos:view_cart')

    cart_items_display = []
    total_general = Decimal('0.00')

    for variacion_id, item_data in list(cart.items()): 
        try:
            variacion = VariacionProducto.objects.get(id=variacion_id, activo=True)
            precio_unitario = Decimal(item_data['precio_unitario']) # Este es el precio guardado en el carrito
            cantidad = item_data['cantidad']
            
            # Verificación final de stock antes de proceder
            if variacion.stock < cantidad:
                messages.error(request, f'No hay suficiente stock para "{variacion.producto.nombre}" ({variacion.__str__()}). Stock disponible: {variacion.stock}. Por favor, ajusta la cantidad en tu carrito.')
                # Si no hay suficiente stock, no permitimos el checkout y redirigimos
                return redirect('pedidos:view_cart') # O a la misma página de checkout con el error
                # Considera aquí ajustar la cantidad en el carrito a variacion.stock y mostrar un mensaje
                # Pero para un proceso de checkout, es mejor ser estricto y que el usuario corrija.

            subtotal_item = precio_unitario * cantidad
            total_general += subtotal_item

            cart_items_display.append({
                'variacion': variacion, 
                'cantidad': cantidad,
                'precio_unitario': precio_unitario, # Precio del carrito
                'subtotal': subtotal_item,
                'imagen_url': variacion.producto.imagenes.first().imagen.url if variacion.producto.imagenes.first() else '/static/img/placeholder.png',
            })
        except VariacionProducto.DoesNotExist:
            del cart[variacion_id]
            _save_cart(request, cart)
            messages.warning(request, f'Un producto en tu carrito ya no está disponible y ha sido eliminado. (ID: {variacion_id})')
            # Redirigir para que el carrito se recargue limpio
            return redirect('pedidos:view_cart') 
        except Exception as e:
            messages.error(request, f'Hubo un problema al cargar un producto en tu carrito. Por favor, revisa tu carrito. Error: {e}')
            del cart[variacion_id]
            _save_cart(request, cart)
            return redirect('pedidos:view_cart')
            
    if not cart_items_display:
        return redirect('pedidos:view_cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # 1. Crear el Pedido
            pedido = form.save(commit=False)
            pedido.usuario = request.user if request.user.is_authenticated else None
            # Los campos 'pagado' y 'metodo_pago' se gestionarán más adelante con la pasarela de pago.
            # Por ahora, los dejamos como están, pero en un entorno real, 'pagado' sería False inicialmente.
            pedido.pagado = False # Asumimos que aún no está pagado hasta que la pasarela lo confirme
            pedido.metodo_pago = 'TRANSFERENCIA' # O el método predeterminado antes de la integración
            pedido.total_pedido = total_general # Ya calculado

            # Copiar datos del CustomUser si está logueado y no se han proporcionado en el formulario
            if request.user.is_authenticated:
                if not pedido.nombre_envio:
                    pedido.nombre_envio = request.user.get_full_name() or request.user.username
                if not pedido.email_envio:
                    pedido.email_envio = request.user.email
                # Aquí puedes copiar otros campos del CustomUser si los tienes y no los recoges en el form
                # Por ejemplo, si CustomUser tiene campos de dirección predeterminados:
                # if not pedido.telefono_envio and hasattr(request.user, 'telefono'):
                #     pedido.telefono_envio = request.user.telefono
                # if not pedido.direccion_envio_line1 and hasattr(request.user, 'direccion'):
                #     pedido.direccion_envio_line1 = request.user.direccion
                # etc.
            
            pedido.save() 

            # 2. Crear los Ítems del Pedido y Actualizar Stock
            for item_data in cart_items_display:
                variacion = item_data['variacion']
                cantidad = item_data['cantidad']
                precio_unitario_guardado = item_data['precio_unitario'] # El precio al que se añadió al carrito

                # Crear ItemPedido
                ItemPedido.objects.create(
                    pedido=pedido,
                    variacion_producto=variacion,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario_guardado # Usamos el precio que estaba en el carrito
                )
                
                # Descontar stock (solo si el pedido se está creando por primera vez)
                # Esta lógica ya la tienes, la reforzamos aquí.
                if variacion.stock >= cantidad: # Doble verificación, aunque ya se hizo arriba
                    variacion.stock -= cantidad
                    variacion.save()
                else:
                    # Esto no debería ocurrir si la verificación inicial es estricta
                    messages.error(request, f'Error crítico: Stock insuficiente para {variacion.producto.nombre}. Contacte con el administrador.')
                    # Considera revertir el pedido y/o el stock ya descontado
                    # o marcar el pedido con un estado especial.
                    return redirect('pedidos:view_cart') # Redirige con un error grave

            # 3. Vaciar el carrito de la sesión
            _save_cart(request, {}) 
            
            # --- ENVÍO DE CORREOS ELECTRÓNICOS ---
            email_context = {
                'pedido': pedido,
                'items_pedido': pedido.items.all(), 
                'total_pedido': pedido.get_total_cost(), 
                'dominio': request.META['HTTP_HOST'], 
                'protocolo': 'https' if request.is_secure() else 'http',
            }

            # Correo para el Cliente (CORREGIDO: Eliminado el argumento 'bcc')
            subject_cliente = f'Confirmación de Pedido #{pedido.id} - Mi Tienda Online'
            message_cliente = render_to_string('pedidos/emails/order_confirmation_cliente.html', email_context)
            recipient_list_cliente = [pedido.email_envio] 

            try:
                send_mail(
                    subject_cliente,
                    '', 
                    settings.DEFAULT_FROM_EMAIL, 
                    recipient_list_cliente,
                    html_message=message_cliente,
                    fail_silently=False,
                )
                messages.success(request, 'Se ha enviado un correo de confirmación a tu dirección.')
            except Exception as e:
                messages.error(request, f'No se pudo enviar el correo de confirmación al cliente: {e}')

            # Correo para el Dueño de la Tienda (Aquí SÍ lleva BCC)
            subject_dueno = f'Nuevo Pedido Recibido: #{pedido.id} - Mi Tienda Online'
            message_dueno = render_to_string('pedidos/emails/order_notification_dueno.html', email_context)
            recipient_list_dueno = [settings.DEFAULT_FROM_EMAIL] 

            try:
                send_mail(
                    subject_dueno,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list_dueno,
                    bcc=bcc_recipients,    
                    html_message=message_dueno,
                    fail_silently=False,
                )
                messages.success(request, 'Se ha notificado al dueño de la tienda y a los BCCs.')
            except Exception as e:
                messages.error(request, f'No se pudo enviar el correo de notificación al dueño: {e}')

            messages.success(request, f'Tu pedido #{pedido.id} ha sido realizado con éxito. ¡Gracias por tu compra!')
            return redirect('pedidos:order_confirmation', pedido_id=pedido.id)
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            # Rellenar los datos iniciales del formulario de checkout desde CustomUser
            initial_data = {
                'nombre_envio': f"{request.user.first_name or ''} {request.user.last_name or ''}".strip(),
                'email_envio': request.user.email,
                'telefono_envio': request.user.telefono, # Usar el campo de CustomUser
                # Aquí puedes añadir más campos de CustomUser si los usas para dirección predeterminada
                # 'direccion_envio_line1': request.user.direccion_line1,
                # 'ciudad_envio': request.user.ciudad,
                # etc.
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items_display,
        'total_general': total_general,
    }
    return render(request, 'pedidos/checkout.html', context)

def checkout2(request):
    cart = _get_cart(request)
    # --- NUEVO: Define la lista de direcciones BCC ---
    # Puedes añadir tantas direcciones como necesites.
    # Por ejemplo: ['admin2@tutienda.com', 'contabilidad@tutienda.com']
    bcc_recipients = ['msb.duck@gmail.com', 'msb.caixa@gmail.com','msb.coin@gmail.com','msb.tesla@gmail.com','msb.motive@gmail.com','msebti2@gmail.com'] 
    
    if not cart:
        messages.warning(request, "Tu carrito está vacío. Añade productos para proceder al pago.")
        return redirect('pedidos:view_cart')

    cart_items_display = []
    total_general = Decimal('0.00')

    for variacion_id, item_data in list(cart.items()): 
        try:
            variacion = VariacionProducto.objects.get(id=variacion_id, activo=True)
            precio_unitario = Decimal(item_data['precio_unitario'])
            cantidad = item_data['cantidad']
            
            if variacion.stock < cantidad:
                messages.error(request, f'No hay suficiente stock para "{variacion.producto.nombre}" ({variacion.__str__()}). Stock disponible: {variacion.stock}. Se ajustó la cantidad en el carrito.')
                cantidad = variacion.stock 
                if cantidad == 0:
                    del cart[variacion_id] 
                    _save_cart(request, cart)
                    continue 
                else:
                    cart[variacion_id]['cantidad'] = cantidad
                    _save_cart(request, cart)

            subtotal_item = precio_unitario * cantidad
            total_general += subtotal_item

            cart_items_display.append({
                'variacion': variacion, 
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal_item,
                'imagen_url': variacion.producto.imagenes.first().imagen.url if variacion.producto.imagenes.first() else '/static/img/placeholder.png',
            })
        except VariacionProducto.DoesNotExist:
            del cart[variacion_id]
            _save_cart(request, cart)
            messages.warning(request, f'Un producto en tu carrito ya no está disponible y ha sido eliminado. (ID: {variacion_id})')
        except Exception as e:
            messages.error(request, f'Hubo un problema al cargar un producto en tu carrito. Por favor, revisa tu carrito. Error: {e}')
            del cart[variacion_id]
            _save_cart(request, cart)
            
    if not cart_items_display:
        return redirect('pedidos:view_cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # 1. Crear el Pedido
            pedido = form.save(commit=False)
            pedido.usuario = request.user if request.user.is_authenticated else None
            pedido.pagado = True 
            pedido.metodo_pago = 'Simulado' 
            pedido.total_pedido = total_general
            pedido.save() 

            # 2. Crear los Ítems del Pedido y Actualizar Stock
            for item_data in cart_items_display:
                variacion = item_data['variacion']
                cantidad = item_data['cantidad']
                precio_unitario_guardado = item_data['precio_unitario'] 
                
                ItemPedido.objects.create(
                    pedido=pedido,
                    variacion_producto=variacion,
                    # Asegúrate que el campo de precio en ItemPedido sea 'precio'
                    # si ese fue el fix del error anterior.
                    precio_unitario=precio_unitario_guardado, 
                    cantidad=cantidad
                )
                
                # Descontar stock
                variacion.stock -= cantidad
                variacion.save()

            # 3. Vaciar el carrito de la sesión
            _save_cart(request, {}) 
            
            # --- ENVÍO DE CORREOS ELECTRÓNICOS ---
            # Confeccionar el contexto para las plantillas de correo
            email_context = {
                'pedido': pedido,
                'items_pedido': pedido.items.all(), # Accede a los ítems del pedido
                'total_pedido': pedido.get_total_cost(), # Usa el método que definiste
                'dominio': request.META['HTTP_HOST'], # Para enlaces absolutos si los necesitas
                'protocolo': 'https' if request.is_secure() else 'http',
            }

            # Correo para el Cliente
            subject_cliente = f'Confirmación de Pedido #{pedido.id} - Mi Tienda Online'
            message_cliente = render_to_string('pedidos/emails/order_confirmation_cliente.html', email_context)
            recipient_list_cliente = [pedido.email_envio] # Asumiendo que email_envio es el campo del cliente

            try:
                send_mail(
                    subject_cliente,
                    '', # El mensaje plano se deja vacío si usas html_message
                    settings.DEFAULT_FROM_EMAIL, # Remitente desde settings
                    recipient_list_cliente,
                    html_message=message_cliente,
                    fail_silently=False,
                )
                messages.success(request, 'Se ha enviado un correo de confirmación a tu dirección.')
            except Exception as e:
                messages.error(request, f'No se pudo enviar el correo de confirmación al cliente: {e}')

            # Correo para el Dueño de la Tienda
            subject_dueno = f'Nuevo Pedido Recibido: #{pedido.id} - Mi Tienda Online'
            message_dueno = render_to_string('pedidos/emails/order_notification_dueno.html', email_context)
            recipient_list_dueno = [settings.DEFAULT_FROM_EMAIL] # O el email específico del dueño

            try:
                send_mail(
                    subject_dueno,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list_dueno,
                    bcc=bcc_recipients,   # Destinatarios BCC (ocultos)
                    html_message=message_dueno,
                    fail_silently=False,
                )
                messages.success(request, 'Se ha notificado al dueño de la tienda.')
            except Exception as e:
                messages.error(request, f'No se pudo enviar el correo de notificación al dueño: {e}')

            messages.success(request, f'Tu pedido #{pedido.id} ha sido realizado con éxito. ¡Gracias por tu compra!')
            return redirect('pedidos:order_confirmation', pedido_id=pedido.id)
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'nombre_envio': f"{request.user.first_name or ''} {request.user.last_name or ''}".strip(),
                'email_envio': request.user.email,
                # ... (otros campos de envío si los tienes en el perfil del usuario)
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items_display,
        'total_general': total_general,
    }
    return render(request, 'pedidos/checkout.html', context)




def checkout1(request):
    cart = _get_cart(request)
    
    if not cart:
        messages.warning(request, "Tu carrito está vacío. Añade productos para proceder al pago.")
        return redirect('pedidos:view_cart') # ¡CORREGIDO! Usando app_name:url_name

    cart_items_display = []
    total_general = Decimal('0.00')

    for variacion_id, item_data in list(cart.items()): 
        try:
            variacion = VariacionProducto.objects.get(id=variacion_id, activo=True)
            precio_unitario = Decimal(item_data['precio_unitario'])
            cantidad = item_data['cantidad']
            
            if variacion.stock < cantidad:
                messages.error(request, f'No hay suficiente stock para "{variacion.producto.nombre}" ({variacion.__str__()}). Stock disponible: {variacion.stock}. Se ajustó la cantidad en el carrito.')
                cantidad = variacion.stock 
                if cantidad == 0:
                    del cart[variacion_id] 
                    _save_cart(request, cart)
                    continue 
                else:
                    cart[variacion_id]['cantidad'] = cantidad
                    _save_cart(request, cart)

            subtotal_item = precio_unitario * cantidad
            total_general += subtotal_item

            cart_items_display.append({
                'variacion': variacion, 
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal_item,
                'imagen_url': variacion.producto.imagenes.first().imagen.url if variacion.producto.imagenes.first() else '/static/img/placeholder.png',
            })
        except VariacionProducto.DoesNotExist:
            del cart[variacion_id]
            _save_cart(request, cart)
            messages.warning(request, f'Un producto en tu carrito ya no está disponible y ha sido eliminado. (ID: {variacion_id})')
        except Exception as e:
            messages.error(request, f'Hubo un problema al cargar un producto en tu carrito. Por favor, revisa tu carrito. Error: {e}')
            del cart[variacion_id]
            _save_cart(request, cart)
            
    if not cart_items_display:
        return redirect('pedidos:view_cart') # ¡CORREGIDO! Usando app_name:url_name

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # 1. Crear el Pedido
            pedido = form.save(commit=False)
            pedido.usuario = request.user if request.user.is_authenticated else None
            pedido.pagado = True 
            pedido.metodo_pago = 'Simulado' 
            # Asegúrate de que total_general esté calculado antes de guardar
            pedido.total_pedido = total_general # ¡IMPORTANTE! Asegurar que este campo existe en Pedido
            pedido.save() 

            # 2. Crear los Ítems del Pedido y Actualizar Stock
            for item_data in cart_items_display:
                variacion = item_data['variacion']
                cantidad = item_data['cantidad']
                precio_unitario_guardado = item_data['precio_unitario'] 
                
                ItemPedido.objects.create(
                    pedido=pedido,
                    variacion_producto=variacion,
                    precio_unitario=precio_unitario_guardado,
                    cantidad=cantidad
                )
                
                # Descontar stock
                variacion.stock -= cantidad
                variacion.save()

            # 3. Vaciar el carrito de la sesión
            _save_cart(request, {}) 
            
            messages.success(request, f'Tu pedido #{pedido.id} ha sido realizado con éxito. ¡Gracias por tu compra!')
            return redirect('pedidos:order_confirmation', pedido_id=pedido.id) # ¡CORREGIDO! Usando app_name:url_name
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                # Asegúrate de que los nombres de los campos coincidan con los de tu CheckoutForm
                'nombre_envio': f"{request.user.first_name or ''} {request.user.last_name or ''}".strip(),
                'email_envio': request.user.email,
                # 'direccion_envio_line1': request.user.profile.direccion, # Si tuvieras un modelo Profile
                # 'ciudad_envio': request.user.profile.ciudad,
                # 'provincia_envio': request.user.profile.provincia,
                # 'codigo_postal_envio': request.user.profile.codigo_postal,
                # 'pais_envio': request.user.profile.pais,
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items_display,
        'total_general': total_general,
    }
    # ¡CORREGIDO! La plantilla ahora debería estar en 'pedidos/checkout.html'
    return render(request, 'pedidos/checkout.html', context)

# --- Nueva vista de Confirmación de Pedido ---
def order_confirmation(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    # Aquí puedes añadir lógica para verificar que el usuario sea el dueño del pedido
    # if request.user.is_authenticated and pedido.usuario != request.user:
    #    messages.error(request, "No tienes permiso para ver este pedido.")
    #    return redirect('home') # O a una vista de "mis pedidos"

    context = {
        'pedido': pedido,
        'items_pedido': pedido.items.all(),
        # Asumiendo que get_total_cost() es un método de tu modelo Pedido
        'total_pedido': pedido.get_total_cost(), 
    }
    # ¡CORREGIDO! La plantilla ahora debería estar en 'pedidos/order_confirmation.html'
    return render(request, 'pedidos/order_confirmation.html', context)