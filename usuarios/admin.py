# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Si solo quieres el modelo de usuario, así es suficiente
# admin.site.register(CustomUser)

# Para personalizar el panel de administración del usuario (opcional pero útil)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('telefono',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {'fields': ('telefono',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)