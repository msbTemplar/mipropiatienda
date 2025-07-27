# productos/models.py
from django.db import models
from django.utils.text import slugify
import os
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum # <--- ¡Asegúrate de importar Sum!


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Marcas"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    disponible = models.BooleanField(default=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    es_destacado = models.BooleanField(default=False)
    
    # --- ¡AÑADE ESTA PROPIEDAD AQUÍ! ---
    @property
    def total_stock(self):
        # Suma el stock de todas las variaciones activas relacionadas con este producto.
        # Usa .filter(activo=True) si solo quieres contar variaciones activas.
        # 'variaciones' es el related_name del ForeignKey en VariacionProducto
        # El 'or 0' asegura que si no hay variaciones o la suma es None, devuelva 0.
        return self.variaciones.aggregate(total=Sum('stock'))['total'] or 0
    # --- FIN DE LA PROPIEDAD ---

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = "Productos"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class TipoVariacion(models.Model): # Para manejar 'Color', 'Talla', 'Material'
    nombre = models.CharField(max_length=50, unique=True) # ej. "Color", "Talla"

    def __str__(self):
        return self.nombre

class ValorVariacion(models.Model): # Para manejar 'Rojo', 'M', 'Algodón'
    tipo_variacion = models.ForeignKey(TipoVariacion, on_delete=models.CASCADE, related_name='valores')
    valor = models.CharField(max_length=100) # ej. "Rojo", "M"

    class Meta:
        unique_together = ('tipo_variacion', 'valor') # Un color 'Rojo' solo puede existir una vez para el tipo 'Color'

    def __str__(self):
        return f"{self.tipo_variacion.nombre}: {self.valor}"

class VariacionProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variaciones')
    # Un producto puede tener muchas variaciones, cada una con un conjunto de valores de variación
    # Por ejemplo, una camiseta puede tener Color: Rojo, Talla: M
    valores = models.ManyToManyField(ValorVariacion) # Aquí se vinculan los valores específicos
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    precio_adicional = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    imagen_variacion = models.ImageField(upload_to='productos/variaciones/', blank=True, null=True) # Imagen específica para esta variación
    
     # --- AÑADE ESTA LÍNEA AQUÍ ---
    activo = models.BooleanField(default=True) # Campo para activar/desactivar la variación
    # -----------------------------
    
    
    class Meta:
        unique_together = ('producto', 'sku') # Un SKU debe ser único por producto
        verbose_name_plural = "Variaciones de Producto"

    # def save(self, *args, **kwargs):
    #     if not self.sku and self.producto:
    #         # Generar un SKU básico, lo ideal es una lógica más robusta para SKUs
    #         self.sku = slugify(f"{self.producto.nombre}-{'-'.join([v.valor for v in self.valores.all()])}")[:100]
    #     super().save(*args, **kwargs)

    def __str__(self):
        # Esta es la línea que debe cambiar (o la que se parece a la línea 99 en tu archivo)
        # Versión más segura para evitar recursión
        try:
            # Intenta construir una cadena legible de forma segura
            valores_nombres = []
            # Accede a los atributos directos de ValorVariacion para evitar bucles de __str__
            # Esto es crucial: evitamos llamar `str(v)` directamente si `str(v)` a su vez
            # llama a algo que refiere a `VariacionProducto`.
            for valor_obj in self.valores.all():
                valores_nombres.append(f"{valor_obj.tipo_variacion.nombre}: {valor_obj.valor}")

            if valores_nombres:
                return f"{self.producto.nombre} - {', '.join(valores_nombres)}"
            else:
                return f"{self.producto.nombre} - Sin Variaciones (SKU: {self.sku or 'N/A'})"
        except Exception:
            # En caso de que falle la obtención de valores (e.g., al inicio de la creación),
            # proporciona una representación simple para evitar el error.
            return f"Variación de {self.producto.nombre} (ID: {self.pk or 'Nuevo'})"
    
    def save(self, *args, **kwargs):
        # 1. Primero, guarda la instancia principal para que tenga un ID (PK)
        super().save(*args, **kwargs)

        # 2. Si el SKU no está establecido y el objeto ya tiene un PK
        if not self.sku and self.pk:
            # Genera un SKU simple usando el slug del producto y el ID de la variación.
            base_sku = slugify(self.producto.nombre)
            self.sku = f"{base_sku}-{self.pk}"[:100]
            
            # 3. Vuelve a guardar solo el campo SKU para evitar un bucle
            super().save(update_fields=['sku'])






def product_image_upload_to(instance, filename):
    # Genera una ruta de archivo única para cada imagen
    base_filename, file_extension = os.path.splitext(filename)
    new_filename = f"{instance.producto.slug}-{instance.pk}-{base_filename}{file_extension}"
    return os.path.join('productos/imagenes/', new_filename)

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/imagenes/') # Se recomienda una función para la ruta de subida
    es_principal = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name_plural = "Imágenes de Producto"

    def __str__(self):
        return f"Imagen de {self.producto.nombre} ({self.orden})"



