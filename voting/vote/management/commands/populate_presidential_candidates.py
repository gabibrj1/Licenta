import random
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction, connection
from vote.models import PresidentialCandidate

class Command(BaseCommand):
    help = 'Populează baza de date cu candidați prezidențiali'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Șterge candidații existenți înainte de a adăuga alții noi'
        )
    
    def handle(self, *args, **options):
        # Obține numele tabelei din Django
        app_name = 'vote'
        model_name = 'presidentialcandidate'
        table_name = f"{app_name}_{model_name}"
        
        # Verifică structura tabelei (doar pentru debug)
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            table_structure = cursor.fetchall()
            self.stdout.write(f"Structura tabelei {table_name}:")
            for column in table_structure:
                self.stdout.write(f"  {column}")

        # Verifică dacă trebuie să ștergem candidații existenți
        if options['clean']:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"DELETE FROM {table_name}")
                    self.stdout.write(self.style.SUCCESS(f"S-au șters toți candidații prezidențiali existenți"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Eroare la ștergerea candidaților: {e}"))
        
        # Lista candidaților prezidențiali conform datelor primite
        candidati_prezidentiali = [
            {
                'name': 'Crin Antonescu',
                'party': 'Alianța Electorală România Înainte (PSD-PNL-UDMR)',
                'description': 'Fostul președinte al PNL și fost președinte interimar după suspendarea lui Traian Băsescu are 65 de ani și a revenit în viaţa publică după 10 ani de absenţă, înainte de alegerile prezidențiale din acest an.',
                'photo_url': "http://localhost:8000/static/icons/crin.jpg",
                'order_nr': 2,
                'gender': 'M'
            },
            {
                'name': 'George Simion',
                'party': 'Alianța pentru Unirea Românilor',
                'description': 'Este la a doua candidatură pentru Președinția României, după ce la alegerile din 2024 a fost pe locul al patrulea în clasament. Liderul AUR a intrat în cursa pentru Cotroceni de anul acesta după ce candidatura lui Călin Georgescu a fost respinsă de Curtea Constituțională a României (CCR).',
                'photo_url': "http://localhost:8000/static/icons/simion.jpg",
                'order_nr': 1,
                'gender': 'M'
            },
            {
                'name': 'Elena Lasconi',
                'party': 'Uniunea Salvați România',
                'description': 'Este primar la Câmpulung și președinta USR. Și ea este la a doua candidatură la alegerile prezidențiale, după ce, în urma rezultatelor a primului tur din luna noiembrie, intrase în finala prezidențială cu Călin Georgescu.',
                'photo_url': "http://localhost:8000/static/icons/lasconi.jpg",
                'order_nr': 3,
                'gender': 'F'
            },
            {
                'name': 'Nicușor Dan',
                'party': 'Independent',
                'description': 'Este la prima candidatură pentru alegerile prezidențiale și la al doilea mandat de primar al Bucureștiului. El și-a anunțat intenția de a candida la președinție cu câteva zile după ce primele alegeri au fost anulate de către CCR.',
                'photo_url': "http://localhost:8000/static/icons/nicudan.jpg",
                'order_nr': 11,
                'gender': 'M'
            },
            {
                'name': 'Victor Ponta',
                'party': 'Independent',
                'description': 'Fost președinte PSD și fost premier, candidează pentru a doua oară la Președinția României, de data aceasta independent. Victor Ponta și-a dat demisia din funcția de premier în 2015, după tragedia de la Colectiv, în urma căreia au murit 65 de tineri.',
                'photo_url': "http://localhost:8000/static/icons/ponta.jpg",
                'order_nr': 6,
                'gender': 'M'
            },
            {
                'name': 'Lavinia Șandru',
                'party': 'Partidul Umanist Social Liberal',
                'description': 'Este fostă realizatoare TV și a fost coordonatoarea de comunicare a PUSL, partid fondat de Dan Voiculescu.',
                'photo_url': "http://localhost:8000/static/icons/sandru.jpg",
                'order_nr': 5,
                'gender': 'F'
            },
            {
                'name': 'Silviu Predoiu',
                'party': 'Partidul Liga Acțiunii Naționale',
                'description': 'Este fostul numărul doi al SIE și fost prim-adjunct al directorului SIE între 2005 și 2018. Este și el la a doua candidatură pentru Președinția României, prima dată în 2014, când s-a clasat pe ultimul loc, cu 0,12%.',
                'photo_url': "http://localhost:8000/static/icons/predoiu.jpg",
                'order_nr': 8,
                'gender': 'M'
            },
            {
                'name': 'Cristian Terheș',
                'party': 'Partidul Național Conservator Român',
                'description': 'Este europarlamentar la al doilea mandat, ales pe listele AUR, și a candidat și în 2024 la alegerile prezidențiale. La alegerile prezidențiale din 2024, Terheș a obținut 1,04%, adică 95.783 de voturi.',
                'photo_url': "http://localhost:8000/static/icons/terhes.jpg",
                'order_nr': 4,
                'gender': 'M'
            },
            {
                'name': 'Daniel Funeriu',
                'party': 'Independent',
                'description': 'Este fost ministru al Educației în guvernul Boc. De profesie chimist, fost membru al PLD, PDL și PMP, Daniel Funeriu (53 de ani) a mai fost europarlamentar în intervalul decembrie 2008-iulie 2009.',
                'photo_url': "http://localhost:8000/static/icons/funeriu.jpg",
                'order_nr': 10,
                'gender': 'M'
            },
            {
                'name': 'John-Ion Banu-Muscel',
                'party': 'Independent',
                'description': 'Candidează independent la prezidențiale și se prezintă drept om de afaceri româno-american. Potrivit stirileprotv.ro, în Statele Unite, el a creat Romanian-American League (Liga Româno-Americană), o asociație românească din Florida.',
                'photo_url': "http://localhost:8000/static/icons/muscel.jpg",
                'order_nr': 9,
                'gender': 'M'
            },
            {
                'name': 'Sebastian Constantin Popescu',
                'party': 'Partidul Noua Românie',
                'description': 'Are 43 de ani și este absolvent al Facultatății de Medicină Veterinară, Universitatea de Științe Agricole și Medicină Veterinară din Timișoara. El este președinte al Partidului Noua Românie și se prezintă drept jurnalist la „ExclusiveNews", conform CV-ului său.',
                'photo_url': "http://localhost:8000/static/icons/popescu.png",
                'order_nr': 7,
                'gender': 'M'
            }
        ]
        
        # Folosim o tranzacție pentru a ne asigura că toate schimbările sunt aplicate sau niciuna
        with transaction.atomic():
            try:
                # Verifică dacă tabela are coloana gender
                with connection.cursor() as check_cursor:
                    check_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                    columns = [col[0] for col in check_cursor.fetchall()]
                    has_gender_column = 'gender' in columns
                    
                    # Dacă nu există coloana pentru gen, o adăugăm
                    if not has_gender_column:
                        try:
                            check_cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN gender CHAR(1) NULL")
                            self.stdout.write("S-a adăugat coloana 'gender' în tabelă")
                            has_gender_column = True
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"Nu s-a putut adăuga coloana 'gender': {e}"))

                # Verifică dacă există coloana order_nr sau trebuie redenumită order
                with connection.cursor() as check_cursor:
                    check_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                    columns = [col[0] for col in check_cursor.fetchall()]
                    
                    # Dacă există coloana 'order' dar nu 'order_nr'
                    if 'order' in columns and 'order_nr' not in columns:
                        try:
                            # Redenumim coloana 'order' în 'order_nr'
                            check_cursor.execute(f"ALTER TABLE {table_name} CHANGE `order` `order_nr` INT")
                            self.stdout.write("S-a redenumit coloana 'order' în 'order_nr'")
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"Nu s-a putut redenumi coloana 'order': {e}"))
                            
                            # În cazul în care redenumirea nu funcționează, păstrăm numele original
                            for candidat in candidati_prezidentiali:
                                if 'order_nr' in candidat:
                                    candidat['order'] = candidat.pop('order_nr')

                # Adăugăm fiecare candidat folosind SQL direct pentru eficiență
                with connection.cursor() as cursor:
                    # Pregătim inserțiile pentru toți candidații
                    for candidat in candidati_prezidentiali:
                        # Verificăm dacă trebuie să omitem coloana gender din inserare
                        if not has_gender_column and 'gender' in candidat:
                            del candidat['gender']
                        
                        # Construiesc șirul de coloane și valorile pentru INSERT
                        # Folosesc backticks pentru fiecare coloană pentru a evita probleme cu cuvintele rezervate
                        columns_str = ', '.join([f"`{col}`" for col in candidat.keys()])
                        placeholders = ', '.join(['%s'] * len(candidat))
                        values = list(candidat.values())
                        
                        # SQL pentru inserare
                        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        cursor.execute(sql, values)
                
                self.stdout.write(self.style.SUCCESS(
                    f"S-au adăugat {len(candidati_prezidentiali)} candidați prezidențiali în baza de date."
                ))
                
                # Verifică dacă inserarea a avut succes
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"Total candidați prezidențiali în bază: {count}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Eroare la adăugarea candidaților: {str(e)}"))
                raise