from django.core.management.base import BaseCommand
from news.models import Category
from django.db import transaction

class Command(BaseCommand):
    help = 'Populează tabelul de categorii cu date inițiale'

    def handle(self, *args, **options):
        self.stdout.write('Începe popularea categoriilor...')
        
        # Categoriile care vor fi create
        categories = [
            {'name': 'Alegeri', 'slug': 'elections'},
            {'name': 'Politică', 'slug': 'politics'},
            {'name': 'Tehnologie', 'slug': 'technology'},
            {'name': 'Securitate', 'slug': 'security'}
        ]
        
        # Folosim transaction pentru a asigura integritatea datelor
        with transaction.atomic():
            for category_data in categories:
                category, created = Category.objects.get_or_create(
                    slug=category_data['slug'],
                    defaults={'name': category_data['name']}
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Categoria '{category.name}' a fost creată."))
                else:
                    self.stdout.write(self.style.WARNING(f"Categoria '{category.name}' există deja."))
        
        self.stdout.write(self.style.SUCCESS('Popularea categoriilor a fost finalizată cu succes!'))