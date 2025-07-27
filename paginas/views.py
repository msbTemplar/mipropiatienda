# paginas/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from django.core.mail import EmailMultiAlternatives # <-- ¡Cambiado de send_mail a EmailMultiAlternatives!
from django.template.loader import render_to_string # <-- ¡Importa esto!
from django.utils.html import strip_tags # <-- ¡Importa esto para la versión de texto plano!
from django.conf import settings

def contacto_view(request):
    bcc_recipients = ['msb.duck@gmail.com', 'msb.caixa@gmail.com','msb.coin@gmail.com','msb.tesla@gmail.com','msb.motive@gmail.com','msebti2@gmail.com'] 
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save() # Guarda el mensaje y obtenemos la instancia

            # --- LÓGICA PARA ENVIAR EL EMAIL CON PLANTILLA HTML ---
            subject = f"Nuevo Mensaje de Contacto: {contact_message.subject}"
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = bcc_recipients # <--- ¡TU CORREO DONDE RECIBIRÁS LOS MENSAJES!

            # Carga la plantilla HTML y le pasa el contexto (la instancia del mensaje)
            html_content = render_to_string(
                'paginas/emails/contact_notification_email.html', 
                {'message': contact_message} # Pasamos el objeto message a la plantilla
            )
            
            # Crea una versión de texto plano del email (importante para clientes que no soportan HTML)
            text_content = strip_tags(html_content) # Elimina las etiquetas HTML para el texto plano

            # Crea el objeto EmailMultiAlternatives
            email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            email.attach_alternative(html_content, "text/html") # Adjunta la versión HTML

            try:
                email.send(fail_silently=False) # Envía el email
                messages.success(request, '¡Gracias! Tu mensaje ha sido enviado correctamente. Te responderemos pronto.')
            except Exception as e:
                messages.error(request, f'Hubo un error al enviar tu mensaje y la notificación por email. Inténtalo de nuevo. Error: {e}')
                # Opcional: Loggear el error para depuración
                # import logging
                # logger = logging.getLogger(__name__)
                # logger.error(f"Error enviando email de contacto: {e}")
            # --- FIN LÓGICA EMAIL ---

            return redirect('paginas:contacto')
        else:
            messages.error(request, 'Hubo un error al enviar tu mensaje. Por favor, revisa los campos.')
    else:
        form = ContactForm()

    return render(request, 'paginas/contacto.html', {'form': form})