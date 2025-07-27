# pedidos/management/commands/limpiar_carritos_antiguos.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from pedidos.models import Carrito # Asegúrate de que Carrito tiene un campo 'completado' y 'fecha_creacion'

class Command(BaseCommand):
    help = 'Limpia carritos incompletos y antiguos. Opcionalmente revierte stock si se implementó reserva.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7, # Por defecto, carritos de más de 7 días
            help='Número de días para considerar un carrito como antiguo.',
        )
        # Puedes añadir un argumento para revertir stock aquí si luego implementas la reserva
        # parser.add_argument(
        #     '--revertir-stock',
        #     action='store_true',
        #     help='Revertir el stock de carritos antiguos si el stock fue reservado.',
        # )

    def handle(self, *args, **kwargs):
        dias = kwargs['dias']
        
        # Fecha límite para carritos "antiguos"
        limite_fecha = timezone.now() - timedelta(days=dias)

        # Encontrar carritos que no han sido completados y son anteriores al límite
        carritos_antiguos = Carrito.objects.filter(
            completado=False,
            fecha_creacion__lt=limite_fecha
        )

        num_carritos_limpiados = carritos_antiguos.count()

        for carrito in carritos_antiguos:
            # Aquí, si tuvieras lógica de "reserva de stock en el carrito", la revertirías.
            # Por ejemplo: carrito.revertir_stock_reservado()
            
            # Puedes elegir si los borras o simplemente los marcas como "completados" (abandonados)
            # carrito.completado = True # Marcar como completado/abandonado
            # carrito.save()
            
            # O directamente borrarlos si no te interesa mantener el registro de carritos abandonados
            carrito.delete() 
            
        self.stdout.write(self.style.SUCCESS(f'Se han limpiado {num_carritos_limpiados} carritos incompletos con más de {dias} días de antigüedad.'))