import random
from datetime import datetime, date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import VoteStatistics

User = get_user_model()

class StatisticsPopulator:
    """Utility pentru popularea statisticilor cu date de test"""
    
    ROMANIAN_FIRST_NAMES_M = [
        'Alexandru', 'Andrei', 'Adrian', 'Bogdan', 'Cristian', 'Daniel', 'Gabriel', 'Ionut', 
        'Marius', 'Mihai', 'Nicolae', 'Radu', 'Stefan', 'Vlad', 'Florin', 'Catalin'
    ]
    
    ROMANIAN_FIRST_NAMES_F = [
        'Maria', 'Ana', 'Elena', 'Ioana', 'Cristina', 'Andreea', 'Mihaela', 'Diana', 
        'Alexandra', 'Raluca', 'Daniela', 'Gabriela', 'Monica', 'Carmen', 'Alina', 'Roxana'
    ]
    
    ROMANIAN_LAST_NAMES = [
        'Popescu', 'Ionescu', 'Popa', 'Radu', 'Stoica', 'Stan', 'Dumitrescu', 'Diaconu',
        'Constantinescu', 'Georgescu', 'Munteanu', 'Marin', 'Tudor', 'Preda', 'Moldovan', 'Florescu'
    ]
    
    URBAN_ADDRESSES = [
        'Municipiul București, Sector 1, Strada Victoriei nr. 25',
        'Municipiul Cluj-Napoca, Strada Memorandumului nr. 15',
        'Municipiul Timișoara, Strada Lipovei nr. 8',
        'Municipiul Iași, Strada Păcurari nr. 42',
        'Municipiul Constanța, Strada Tomis nr. 120',
        'Orașul Ploiești, Strada Republicii nr. 33',
        'Municipiul Craiova, Strada Calea București nr. 67',
        'Municipiul Galați, Strada Brăilei nr. 89',
    ]
    
    RURAL_ADDRESSES = [
        'Comuna Voluntari, Sat Voluntari nr. 45',
        'Comuna Bragadiru, Sat Bragadiru nr. 23',
        'Comuna Corbeanca, Sat Corbeanca nr. 12',
        'Comuna Chitila, Sat Chitila nr. 78',
        'Comuna Pantelimon, Sat Pantelimon nr. 56',
        'Comuna Mogoșoaia, Sat Mogoșoaia nr. 34',
        'Comuna Balotești, Sat Balotești nr. 91',
        'Comuna Dascălu, Sat Dascălu nr. 67',
    ]
    
    COUNTIES = ['B', 'CJ', 'TM', 'IS', 'CT', 'PH', 'DJ', 'GL', 'BV', 'HD']
    
    @classmethod
    def generate_cnp(cls, gender, birth_year):
        """Generează un CNP valid"""
        # Determină prima cifră pe baza genului și anului
        if 1900 <= birth_year <= 1999:
            first_digit = 1 if gender == 'M' else 2
        elif 2000 <= birth_year <= 2099:
            first_digit = 3 if gender == 'M' else 4
        else:
            first_digit = 1 if gender == 'M' else 2  # fallback
        
        # Generează data de naștere
        year_suffix = str(birth_year)[-2:]
        month = f"{random.randint(1, 12):02d}"
        day = f"{random.randint(1, 28):02d}"  # 28 pentru a evita probleme cu februarie
        
        # Generează județul și numărul de ordine
        county_code = f"{random.randint(1, 46):02d}"
        order_number = f"{random.randint(1, 999):03d}"
        
        # Construiește CNP-ul fără cifra de control
        cnp_without_check = f"{first_digit}{year_suffix}{month}{day}{county_code}{order_number}"
        
        # Calculează cifra de control (algoritm simplificat)
        check_digit = random.randint(0, 9)
        
        return cnp_without_check + str(check_digit)
    
    @classmethod
    def create_test_users(cls, count=500):
        """Creează utilizatori de test cu CNP-uri și adrese"""
        created_users = []
        
        for i in range(count):
            # Generează datele utilizatorului
            gender = random.choice(['M', 'F'])
            birth_year = random.randint(1950, 2005)
            
            first_name = random.choice(
                cls.ROMANIAN_FIRST_NAMES_M if gender == 'M' else cls.ROMANIAN_FIRST_NAMES_F
            )
            last_name = random.choice(cls.ROMANIAN_LAST_NAMES)
            
            # Generează CNP
            cnp = cls.generate_cnp(gender, birth_year)
            
            # Generează email unic
            email = f"{first_name.lower()}.{last_name.lower()}.{i}@testuser.ro"
            
            # Alege adresa (70% urban, 30% rural pentru realismul datelor)
            is_urban = random.random() < 0.7
            address = random.choice(cls.URBAN_ADDRESSES if is_urban else cls.RURAL_ADDRESSES)
            
            # Creează utilizatorul
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
                print(f"Eroare la crearea utilizatorului {email}: {e}")
                continue
        
        return created_users
    
    @classmethod
    def populate_vote_statistics(cls, vote_type='prezidentiale', users=None, vote_start_time=None):
        """Populează statisticile de vot pentru un tip de vot dat"""
        if users is None:
            users = User.objects.filter(cnp__isnull=False, is_verified_by_id=True)
        
        if vote_start_time is None:
            vote_start_time = timezone.now() - timedelta(hours=12)
        
        vote_end_time = vote_start_time + timedelta(hours=12)
        
        # Simulează un aflux realist de votanți (mai mulți la început și sfârșit)
        created_stats = []
        total_users = len(users)
        users_to_vote = random.sample(list(users), min(int(total_users * 0.6), total_users))  # 60% participare
        
        for i, user in enumerate(users_to_vote):
            # Generează timpul de vot (distribuție realistă)
            progress = i / len(users_to_vote)
            
            if progress < 0.3:  # Primul val (primele 3 ore)
                vote_time_offset = random.uniform(0, 3 * 3600)
            elif progress < 0.6:  # Perioada liniștită (următoarele 6 ore)
                vote_time_offset = random.uniform(3 * 3600, 9 * 3600)
            else:  # Valul final (ultimele 3 ore)
                vote_time_offset = random.uniform(9 * 3600, 12 * 3600)
            
            vote_datetime = vote_start_time + timedelta(seconds=vote_time_offset)
            
            # Creează statistica
            stat = VoteStatistics.create_from_vote(
                user=user,
                vote_type=vote_type,
                vote_datetime=vote_datetime,
                location_type='romania',
                county=random.choice(cls.COUNTIES),
                city=f"Oraș Test {random.randint(1, 50)}"
            )
            
            if stat:
                created_stats.append(stat)
        
        return created_stats