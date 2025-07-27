# paginas/admin.py
from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'subject', 'sent_at') # <-- ¡Añadido 'phone_number'!
    list_filter = ('sent_at',)
    search_fields = ('name', 'email', 'subject', 'message', 'phone_number') # <-- ¡Añadido 'phone_number'!
    readonly_fields = ('sent_at',)