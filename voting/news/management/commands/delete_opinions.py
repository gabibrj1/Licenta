from django.core.management.base import BaseCommand
from news.models import NewsArticle
from django.db import transaction

class Command(BaseCommand):
    help = 'Șterge opiniile adăugate de scriptul de populare'

    def handle(self, *args, **options):
        self.stdout.write('Începe ștergerea opiniilor...')
        
        # Lista de slug-uri pentru opiniile create de scriptul de populare
        opinion_slugs = [
            'votul-electronic-oportunitate-sau-risc-pentru-democratie',
            'identitatea-digitala-fundamentul-votului-electronic-sigur',
            'transparenta-cheia-increderii-in-votul-electronic',
            'de-ce-romania-nu-este-inca-pregatita-pentru-votul-electronic',
            'lectii-din-estonia-pentru-implementarea-votului-electronic'
        ]
        
        try:
            with transaction.atomic():
                # Ștergem opiniile bazate pe slug-uri
                deleted_by_slug = NewsArticle.objects.filter(slug__in=opinion_slugs).delete()
                
                # Alternativ, putem șterge toate articolele de tip opinie
                # Decomentează următoarea linie dacă dorești să ștergi toate opiniile
                # deleted_all = NewsArticle.objects.filter(article_type='opinion').delete()
                
                self.stdout.write(self.style.SUCCESS(f'S-au șters {deleted_by_slug[0]} opinii în total.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Eroare la ștergerea opiniilor: {str(e)}'))
            return
        
        self.stdout.write(self.style.SUCCESS('Ștergerea opiniilor a fost finalizată cu succes!'))