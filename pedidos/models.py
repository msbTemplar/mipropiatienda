# pedidos/models.py
from django.db import models
from usuarios.models import CustomUser  # Importa tu modelo de usuario
from productos.models import VariacionProducto # Importa el modelo de variación

class Carrito(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False) # Para indicar si el carrito ya se convirtió en pedido
    
    class Meta:
        verbose_name_plural = "Carritos"

    def __str__(self):
        return f"Carrito de {self.usuario.username if self.usuario else 'Anónimo'}"
    
    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('cantidad'))['total'] or 0

    @property
    def total_precio(self):
        return sum(item.subtotal for item in self.items.all())

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    variacion_producto = models.ForeignKey(VariacionProducto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) # El precio al momento de añadirlo al carrito

    class Meta:
        unique_together = ('carrito', 'variacion_producto') # Un producto solo puede estar una vez en un carrito

    def __str__(self):
        return f"{self.cantidad} x {self.variacion_producto.producto.nombre} ({self.variacion_producto})"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

class Pedido(models.Model):
    ESTADOS_PEDIDO = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
        ('REEMBOLSADO', 'Reembolsado'),
    ]
    METODOS_PAGO = [
        ('TARJETA', 'Tarjeta de Crédito/Débito'),
        ('PAYPAL', 'PayPal'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
    ]

    usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='pedidos')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='PENDIENTE')
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    # Datos de envío (se pueden copiar del usuario o pedir en el checkout)
    direccion_envio_line1 = models.CharField(max_length=255)
    direccion_envio_line2 = models.CharField(max_length=255, blank=True)
    ciudad_envio = models.CharField(max_length=100)
    provincia_envio = models.CharField(max_length=100)
    codigo_postal_envio = models.CharField(max_length=10)
    pais_envio = models.CharField(max_length=100)
    email_envio = models.EmailField()
    nombre_envio = models.CharField(max_length=255)

    metodo_pago = models.CharField(max_length=50, choices=METODOS_PAGO)
    id_transaccion_pago = models.CharField(max_length=255, blank=True, null=True)
    pagado = models.BooleanField(default=False) # Para confirmar el pago

    class Meta:
        ordering = ['-fecha_pedido']
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"Pedido #{self.pk} de {self.usuario.username if self.usuario else 'Anónimo'}"
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    
    # --- Nuevo método para revertir stock ---
    def revertir_stock(self):
        for item_pedido in self.items.all():
            variacion = item_pedido.variacion_producto
            if variacion: # Asegurarse de que la variación aún existe
                variacion.stock += item_pedido.cantidad
                variacion.save()
                print(f"Stock de {variacion} revertido. Cantidad: {item_pedido.cantidad}. Nuevo stock: {variacion.stock}") # Para depuración
        # Opcional: Después de revertir stock, puedes cambiar el estado del pedido a 'CANCELADO'
        # if self.estado != 'CANCELADO': # Para evitar bucles o dobles reversiones
        #    self.estado = 'CANCELADO'
        #    self.save()
        
    # --- Nuevo método para actualizar stock (al crear o pagar) ---
    def descontar_stock(self):
        for item_pedido in self.items.all():
            variacion = item_pedido.variacion_producto
            if variacion and variacion.stock >= item_pedido.cantidad:
                variacion.stock -= item_pedido.cantidad
                variacion.save()
                print(f"Stock de {variacion} descontado. Cantidad: {item_pedido.cantidad}. Nuevo stock: {variacion.stock}") # Para depuración
            else:
                # Esto es un caso de error si el stock no se verificó antes de crear el pedido
                print(f"Error: Stock insuficiente para descontar {item_pedido.cantidad} de {variacion}")
                # Podrías lanzar una excepción o manejarlo de otra forma

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    variacion_producto = models.ForeignKey(VariacionProducto, on_delete=models.SET_NULL, null=True) # SET_NULL si el producto se elimina
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) # Precio pagado en el momento del pedido

    def __str__(self):
        return f"{self.cantidad} x {self.variacion_producto.producto.nombre if self.variacion_producto else 'Producto Eliminado'} ({self.variacion_producto})"
    
    def get_cost(self):
        return self.precio_unitario * self.cantidad

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario