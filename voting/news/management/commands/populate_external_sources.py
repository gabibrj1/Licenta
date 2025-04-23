from django.core.management.base import BaseCommand
from news.models import ExternalNewsSource
from django.db import transaction

class Command(BaseCommand):
    help = 'Populează tabelul de surse externe de știri cu date inițiale'

    def handle(self, *args, **options):
        self.stdout.write('Începe popularea surselor externe de știri...')
        
        # Sursele care vor fi create
        sources_data = [
            {
                'name': 'Centrul pentru studiul democratiei',
                'url': 'https://democracycenter.ro',
                'api_endpoint': 'https://democracycenter.ro/api/news',
                'is_active': True
            },
            {
                'name': 'Code for Romania',
                'url': 'https://www.code4.ro',
                'api_endpoint': 'https://www.code4.ro/api/news',
                'is_active': True
            },
            {
                'name': 'DIGI 24',
                'url': 'https://www.digi24.ro',
                'api_endpoint': 'https://www.digi24.ro/api/news',
                'is_active': True
            },
            {
                'name': 'Guvernul României',
                'url': 'https://sgg.gov.ro',
                'api_endpoint': 'https://sgg.gov.ro/api/news',
                'is_active': True
            },
            {
                'name': 'PressOne',
                'url': 'https://pressone.ro',
                'api_endpoint': 'https://pressone.ro/api/news',
                'is_active': True
            }
        ]
        
        # Folosim transaction pentru a asigura integritatea datelor
        with transaction.atomic():
            # Mai întâi ștergem sursele existente pentru a evita duplicate
            ExternalNewsSource.objects.all().delete()
            self.stdout.write(self.style.WARNING("Sursele externe existente au fost șterse."))
            
            # Apoi adăugăm noile surse
            for source_data in sources_data:
                source = ExternalNewsSource.objects.create(**source_data)
                self.stdout.write(self.style.SUCCESS(f"Sursa externă '{source.name}' a fost creată."))
        
        self.stdout.write(self.style.SUCCESS('Popularea surselor externe de știri a fost finalizată cu succes!'))