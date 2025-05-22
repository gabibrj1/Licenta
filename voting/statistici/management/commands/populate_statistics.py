from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from statistici.utils import StatisticsPopulator
from statistici.models import VoteStatistics
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populează baza de date cu utilizatori și statistici de test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=500,
            help='Numărul de utilizatori de test de creat',
        )
        parser.add_argument(
            '--vote-type',
            type=str,
            default='prezidentiale',
            help='Tipul de vot pentru care să se creeze statistici',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Șterge datele existente înainte de populare',
        )

    def handle(self, *args, **options):
        if options['clear']:
            # Șterge utilizatorii de test și statisticile
            test_users = User.objects.filter(email__contains='@testuser.ro')
            deleted_users = test_users.count()
            test_users.delete()
            
            deleted_stats = VoteStatistics.objects.all().delete()[0]
            
            self.stdout.write(
                self.style.WARNING(
                    f'Au fost șterși {deleted_users} utilizatori de test și {deleted_stats} statistici.'
                )
            )

        # Creează utilizatori de test
        self.stdout.write('Creez utilizatori de test...')
        users = StatisticsPopulator.create_test_users(options['users'])
        self.stdout.write(
            self.style.SUCCESS(f'Au fost creați {len(users)} utilizatori de test.')
        )

        # Populează statisticile pentru turul 1 2024 (date istorice)
        self.stdout.write('Populez statistici pentru Turul 1 Prezidențiale 2024...')
        
        # Data alegerilor prezidențiale din 2024 (8 decembrie)
        vote_date_2024 = timezone.make_aware(timezone.datetime(2024, 12, 8, 7, 0, 0))
        
        stats_2024 = StatisticsPopulator.populate_vote_statistics(
            vote_type='prezidentiale',
            users=users,
            vote_start_time=vote_date_2024
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Au fost create {len(stats_2024)} statistici pentru Turul 1 2024.')
        )

        # Populează statistici pentru votul activ (dacă există)
        if options['vote_type'] != 'prezidentiale':
            self.stdout.write(f'Populez statistici pentru {options["vote_type"]}...')
            
            # Pentru votul activ, folosește timp recent
            recent_vote_time = timezone.now() - timedelta(hours=6)
            
            active_stats = StatisticsPopulator.populate_vote_statistics(
                vote_type=options['vote_type'],
                users=users[:200],  # Mai puțini pentru votul activ
                vote_start_time=recent_vote_time
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Au fost create {len(active_stats)} statistici pentru {options["vote_type"]}.')
            )

        # Afișează un sumar
        self.stdout.write('\n=== SUMAR STATISTICI ===')
        
        total_stats = VoteStatistics.objects.count()
        self.stdout.write(f'Total statistici: {total_stats}')
        
        for vote_type in ['prezidentiale', 'prezidentiale_tur2', 'parlamentare', 'locale']:
            count = VoteStatistics.objects.filter(vote_type=vote_type).count()
            if count > 0:
                self.stdout.write(f'{vote_type}: {count} voturi')
        
        # Statistici pe grupe de vârstă
        self.stdout.write('\nDistribuția pe grupe de vârstă:')
        for age_group in ['18-24', '25-34', '35-44', '45-64', '65+']:
            count = VoteStatistics.objects.filter(age_group=age_group).count()
            if count > 0:
                percentage = (count / total_stats * 100) if total_stats > 0 else 0
                self.stdout.write(f'{age_group}: {count} ({percentage:.1f}%)')
        
        # Statistici pe gen
        self.stdout.write('\nDistribuția pe gen:')
        male_count = VoteStatistics.objects.filter(gender='M').count()
        female_count = VoteStatistics.objects.filter(gender='F').count()
        
        if total_stats > 0:
            male_percentage = (male_count / total_stats * 100)
            female_percentage = (female_count / total_stats * 100)
            self.stdout.write(f'Bărbați: {male_count} ({male_percentage:.1f}%)')
            self.stdout.write(f'Femei: {female_count} ({female_percentage:.1f}%)')

        self.stdout.write(
            self.style.SUCCESS('\n✓ Popularea statisticilor s-a finalizat cu succes!')
        )