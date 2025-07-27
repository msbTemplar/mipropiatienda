# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Aquí puedes añadir campos adicionales que necesites
    telefono = models.CharField(max_length=20, blank=True, null=True)
    # Por defecto, Django ya gestiona email, nombre, apellido, is_staff, is_active, is_superuser

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username # O self.email si lo usas como identificador principal