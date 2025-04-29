from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date
from presidential_candidates.models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation
)
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Adaugă Marcel Ciolacu și participarea sa la alegerile din 2024'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Începe adăugarea lui Marcel Ciolacu și a participării sale la alegerile din 2024...'))

        # 1. Verifică existența anului electoral 2024
        try:
            election_year_2024 = ElectionYear.objects.get(year=2024)
            self.stdout.write(self.style.SUCCESS(f'Anul electoral 2024 există deja.'))
        except ElectionYear.DoesNotExist:
            # Creăm anul electoral dacă nu există
            election_year_2024 = ElectionYear.objects.create(
                year=2024,
                description='Alegeri prezidențiale parțial anulate de CCR.',
                turnout_percentage=51.03,
                total_voters=9120458
            )
            self.stdout.write(self.style.SUCCESS(f'Anul electoral 2024 a fost creat.'))

        # 2. Verifică existența lui Marcel Ciolacu ca și candidat
        ciolacu_data = {
            'name': 'Marcel Ciolacu',
            'birth_date': date(1967, 11, 28),
            'party': 'PSD',
            'biography': 'Marcel Ciolacu este un politician român, membru al Partidului Social Democrat. '
                        'A ocupat funcția de președinte al Camerei Deputaților și a devenit prim-ministru al României '
                        'în iunie 2023. La alegerile prezidențiale din 2024, a candidat din partea PSD, '
                        'fiind susținut de coaliția PSD-PNL.',
            'political_experience': 'Prim-ministru al României (2023-prezent), Președinte al Camerei Deputaților (2019-2023), '
                                   'Președinte PSD (2020-prezent), Deputat (2012-prezent)',
            'education': 'Universitatea Ecologică din București, Facultatea de Drept',
            'photo_url': 'https://example.com/marcel_ciolacu.jpg',
            'is_current': False,  # Va participa la alegerile din 2025, nu la cele actuale
        }
        
        # Generează slug
        ciolacu_data['slug'] = slugify(ciolacu_data['name'])
        
        # Verifică existența candidatului
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=ciolacu_data['name'],
            defaults=ciolacu_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {ciolacu_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in ciolacu_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {ciolacu_data["name"]} a fost actualizat.'))
        
        # 3. Adaugă participarea lui Marcel Ciolacu la alegerile din 2024
        participation_data = {
            'votes_count': 1472773,
            'votes_percentage': 16.52,
            'position': 3,  # A fost pe poziția 3 în primul tur
            'round': 1,  # Primul tur
            'campaign_slogan': 'Împreună pentru România',
            'notable_events': 'Campanie axată pe realizările guvernului și stabilitate economică, susținută de coaliția PSD-PNL.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_year_2024,
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2024, turul {participation.round} a fost adăugată.'
            ))
        else:
            # Actualizăm participarea dacă există deja
            for key, value in participation_data.items():
                setattr(participation, key, value)
            participation.save()
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2024, turul {participation.round} a fost actualizată.'
            ))
        
        self.stdout.write(self.style.SUCCESS('Adăugarea lui Marcel Ciolacu și a participării sale a fost finalizată cu succes!'))