from django.contrib import admin
from .models import Pedido, ItemPedido, Carrito, ItemCarrito

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('variacion_producto', 'cantidad', 'precio_unitario', 'get_cost') # Para que no se modifiquen fácil
    can_delete = False

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_pedido', 'total_pedido', 'estado', 'pagado', 'metodo_pago')
    list_filter = ('estado', 'pagado', 'metodo_pago', 'fecha_pedido')
    search_fields = ('id', 'usuario__username', 'email_envio', 'nombre_envio')
    inlines = [ItemPedidoInline]
    readonly_fields = ('fecha_pedido', 'total_pedido') # Estos campos no deberían ser editables

    # Campos que solo pueden ser editados si el pedido no está pagado o enviado, por ejemplo
    fieldsets = (
        (None, {
            'fields': ('usuario', 'fecha_pedido', 'total_pedido', 'estado', 'pagado', 'metodo_pago', 'id_transaccion_pago')
        }),
        ('Información de Envío', {
            'fields': ('nombre_envio', 'email_envio', 'direccion_envio_line1', 'direccion_envio_line2', 
                       'ciudad_envio', 'provincia_envio', 'codigo_postal_envio', 'pais_envio')
        }),
    )

    # --- Acción de administración para cancelar pedido y revertir stock ---
    actions = ['cancelar_pedidos_y_revertir_stock']

    def cancelar_pedidos_y_revertir_stock(self, request, queryset):
        for pedido in queryset:
            if pedido.estado not in ['CANCELADO', 'REEMBOLSADO']: # Evitar revertir stock dos veces
                pedido.revertir_stock() # Llama al método del modelo
                pedido.estado = 'CANCELADO'
                pedido.pagado = False # Si se cancela, no está pagado
                pedido.save()
                self.message_user(request, f"Pedido {pedido.id} cancelado y stock revertido.", level='success')
            else:
                self.message_user(request, f"Pedido {pedido.id} ya estaba en estado {pedido.estado}. No se revirtió stock.", level='warning')
    cancelar_pedidos_y_revertir_stock.short_description = "Cancelar pedidos seleccionados y revertir stock"



class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    readonly_fields = ('variacion_producto', 'cantidad', 'precio_unitario', 'subtotal')
    can_delete = False

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_creacion', 'completado', 'total_items', 'total_precio')
    list_filter = ('completado', 'fecha_creacion')
    search_fields = ('usuario__username',)
    inlines = [ItemCarritoInline]