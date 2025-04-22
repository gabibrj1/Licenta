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
                'name': 'E-Democracy News',
                'url': 'https://edemocracynews.example.com',
                'api_endpoint': 'https://api.edemocracynews.example.com/v1/news',
                'is_active': True
            },
            {
                'name': 'TechVote',
                'url': 'https://techvote.example.com',
                'api_endpoint': 'https://api.techvote.example.com/news',
                'is_active': True
            },
            {
                'name': 'Election Observer',
                'url': 'https://electionobserver.example.com',
                'api_endpoint': 'https://api.electionobserver.example.com/latest',
                'is_active': True
            },
            {
                'name': 'SmartVote Analysis',
                'url': 'https://smartvote.example.com/analysis',
                'api_endpoint': 'https://api.smartvote.example.com/analysis',
                'is_active': True
            },
            {
                'name': 'VoteWatch',
                'url': 'https://votewatch.example.com',
                'api_endpoint': 'https://api.votewatch.example.com/feed',
                'is_active': True
            }
        ]
        
        # Folosim transaction pentru a asigura integritatea datelor
        with transaction.atomic():
            for source_data in sources_data:
                source, created = ExternalNewsSource.objects.get_or_create(
                    name=source_data['name'],
                    defaults=source_data
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Sursa externă '{source.name}' a fost creată."))
                else:
                    self.stdout.write(self.style.WARNING(f"Sursa externă '{source.name}' există deja."))
        
        self.stdout.write(self.style.SUCCESS('Popularea surselor externe de știri a fost finalizată cu succes!'))