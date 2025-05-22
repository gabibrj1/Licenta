from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from statistici.models import VoteStatistics
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populează baza de date cu statistici pentru alegătorii din străinătate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=200,
            help='Numărul de utilizatori de test pentru străinătate',
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
            help='Șterge datele existente pentru străinătate înainte de populare',
        )

    def handle(self, *args, **options):
        if options['clear']:
            # Șterge statisticile pentru străinătate
            deleted_stats = VoteStatistics.objects.filter(location_type='strainatate').delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Au fost șterse {deleted_stats} statistici pentru străinătate.')
            )

        # Creează utilizatori pentru străinătate dacă nu există
        strainatate_users = self.create_strainatate_users(options['users'])
        
        # Populează statisticile pentru turul 1 2024 (date istorice)
        self.stdout.write('Populez statistici pentru Turul 1 Prezidențiale 2024 - Străinătate...')
        
        vote_date_2024 = timezone.make_aware(timezone.datetime(2024, 12, 8, 7, 0, 0))
        
        stats_2024 = self.populate_strainatate_vote_statistics(
            vote_type='prezidentiale',
            users=strainatate_users,
            vote_start_time=vote_date_2024
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Au fost create {len(stats_2024)} statistici pentru Turul 1 2024 - Străinătate.')
        )

        # Afișează un sumar
        self.stdout.write('\n=== SUMAR STATISTICI STRĂINĂTATE ===')
        
        total_stats = VoteStatistics.objects.filter(location_type='strainatate').count()
        self.stdout.write(f'Total statistici străinătate: {total_stats}')
        
        # Statistici pe țări
        self.stdout.write('\nDistribuția pe țări:')
        countries = VoteStatistics.objects.filter(location_type='strainatate').values_list('county', flat=True).distinct()
        for country in countries:
            if country:
                count = VoteStatistics.objects.filter(location_type='strainatate', county=country).count()
                percentage = (count / total_stats * 100) if total_stats > 0 else 0
                self.stdout.write(f'{country}: {count} ({percentage:.1f}%)')

        self.stdout.write(
            self.style.SUCCESS('\n✓ Popularea statisticilor pentru străinătate s-a finalizat cu succes!')
        )

    def create_strainatate_users(self, count):
        """Creează utilizatori pentru străinătate"""
        
        # Nume internaționale pentru realismul datelor
        INTERNATIONAL_FIRST_NAMES_M = [
            'John', 'Michael', 'David', 'James', 'Robert', 'William', 'Richard', 'Charles',
            'Thomas', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven'
        ]
        
        INTERNATIONAL_FIRST_NAMES_F = [
            'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica',
            'Sarah', 'Karen', 'Nancy', 'Lisa', 'Betty', 'Helen', 'Sandra', 'Donna'
        ]
        
        ROMANIAN_LAST_NAMES = [
            'Popescu', 'Ionescu', 'Popa', 'Radu', 'Stoica', 'Stan', 'Dumitrescu', 'Diaconu',
            'Constantinescu', 'Georgescu', 'Munteanu', 'Marin', 'Tudor', 'Preda', 'Moldovan'
        ]
        
        # Adrese internaționale
        INTERNATIONAL_ADDRESSES = [
            'New York, United States, 123 Main Street',
            'London, United Kingdom, 45 Baker Street', 
            'Paris, France, 78 Rue de la Paix',
            'Berlin, Germany, 12 Unter den Linden',
            'Rome, Italy, 34 Via del Corso',
            'Madrid, Spain, 56 Gran Via',
            'Vienna, Austria, 23 Ringstrasse',
            'Brussels, Belgium, 67 Avenue Louise',
            'Toronto, Canada, 89 Queen Street',
            'Melbourne, Australia, 45 Collins Street'
        ]
        
        created_users = []
        
        # Verifică câți utilizatori pentru străinătate există deja
        existing_count = User.objects.filter(email__contains='@strainatate.ro').count()
        
        for i in range(existing_count, existing_count + count):
            gender = random.choice(['M', 'F'])
            birth_year = random.randint(1950, 2005)
            
            first_name = random.choice(
                INTERNATIONAL_FIRST_NAMES_M if gender == 'M' else INTERNATIONAL_FIRST_NAMES_F
            )
            last_name = random.choice(ROMANIAN_LAST_NAMES)
            
            # Generează CNP
            cnp = self.generate_cnp(gender, birth_year)
            
            # Email unic pentru străinătate
            email = f"{first_name.lower()}.{last_name.lower()}.{i}@strainatate.ro"
            
            # Adresă internațională
            address = random.choice(INTERNATIONAL_ADDRESSES)
            
            try:
                user = User.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    cnp=cnp,
                    is_verified_by_id=True,
                    is_active=True
                )
                
                # Adaugă adresa dacă modelul o suportă
                if hasattr(user, 'address'):
                    user.address = address
                    user.save()
                
                created_users.append(user)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Eroare la crearea utilizatorului {email}: {e}")
                )
                continue
        
        if created_users:
            self.stdout.write(
                self.style.SUCCESS(f'Au fost creați {len(created_users)} utilizatori noi pentru străinătate.')
            )
        else:
            # Folosește utilizatorii existenți
            existing_users = User.objects.filter(email__contains='@strainatate.ro')[:count]
            created_users = list(existing_users)
            self.stdout.write(f'Se folosesc {len(created_users)} utilizatori existenți pentru străinătate.')
        
        return created_users

    def generate_cnp(self, gender, birth_year):
        """Generează un CNP valid"""
        if 1900 <= birth_year <= 1999:
            first_digit = 1 if gender == 'M' else 2
        elif 2000 <= birth_year <= 2099:
            first_digit = 3 if gender == 'M' else 4
        else:
            first_digit = 1 if gender == 'M' else 2
        
        year_suffix = str(birth_year)[-2:]
        month = f"{random.randint(1, 12):02d}"
        day = f"{random.randint(1, 28):02d}"
        county_code = f"{random.randint(1, 46):02d}"
        order_number = f"{random.randint(1, 999):03d}"
        
        cnp_without_check = f"{first_digit}{year_suffix}{month}{day}{county_code}{order_number}"
        check_digit = random.randint(0, 9)
        
        return cnp_without_check + str(check_digit)

    def populate_strainatate_vote_statistics(self, vote_type='prezidentiale', users=None, vote_start_time=None):
        """Populează statisticile de vot pentru străinătate"""
        if users is None:
            users = User.objects.filter(email__contains='@strainatate.ro')
        
        if vote_start_time is None:
            vote_start_time = timezone.now() - timedelta(hours=12)
        
        vote_end_time = vote_start_time + timedelta(hours=12)
        
        # Țări principale pentru diaspora română
        COUNTRIES = ['Germania', 'Italia', 'Spania', 'Franța', 'Marea Britanie', 'SUA', 'Canada', 'Austria']
        CITIES = {
            'Germania': ['Berlin', 'München', 'Frankfurt', 'Düsseldorf'],
            'Italia': ['Roma', 'Milano', 'Torino', 'Bologna'],
            'Spania': ['Madrid', 'Barcelona', 'Valencia', 'Sevilla'],
            'Franța': ['Paris', 'Lyon', 'Marseille', 'Toulouse'],
            'Marea Britanie': ['Londra', 'Manchester', 'Birmingham', 'Leeds'],
            'SUA': ['New York', 'Los Angeles', 'Chicago', 'Washington'],
            'Canada': ['Toronto', 'Montreal', 'Vancouver', 'Ottawa'],
            'Austria': ['Viena', 'Salzburg', 'Graz', 'Innsbruck']
        }
        
        created_stats = []
        total_users = len(users)
        
        # Pentru străinătate, participarea este de obicei mai mică (40%)
        users_to_vote = random.sample(list(users), min(int(total_users * 0.4), total_users))
        
        for i, user in enumerate(users_to_vote):
            # Distribuție diferită pentru străinătate - mai multe voturi în weekend
            progress = i / len(users_to_vote)
            
            if progress < 0.2:  # Start mai lent
                vote_time_offset = random.uniform(0, 2 * 3600)
            elif progress < 0.7:  # Perioada principală
                vote_time_offset = random.uniform(2 * 3600, 8 * 3600)
            else:  # Final intens
                vote_time_offset = random.uniform(8 * 3600, 12 * 3600)
            
            vote_datetime = vote_start_time + timedelta(seconds=vote_time_offset)
            
            # Alege țara și orașul
            country = random.choice(COUNTRIES)
            city = random.choice(CITIES[country])
            
            # Creează statistica pentru străinătate
            stat = VoteStatistics.create_from_vote(
                user=user,
                vote_type=vote_type,
                vote_datetime=vote_datetime,
                location_type='strainatate',
                county=country,
                city=city
            )
            
            if stat:
                created_stats.append(stat)
        
        return created_stats