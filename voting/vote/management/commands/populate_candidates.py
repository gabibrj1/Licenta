import random
import pickle
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction, connection


class Command(BaseCommand):
    help = 'Populează baza de date cu candidați locali pentru toate județele și UAT-urile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Șterge candidații existenți înainte de a adăuga alții noi'
        )
        parser.add_argument(
            '--judet',
            type=str,
            help='Populează candidați doar pentru un anumit județ (cod de 2 litere, ex: AB)'
        )
        parser.add_argument(
            '--uat',
            type=str,
            help='Populează candidați doar pentru un anumit UAT (trebuie specificat și județul)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Numărul de UAT-uri procesate într-un lot (default: 50)'
        )
    
    def handle(self, *args, **options):
        """
        Populează candidații locali folosind datele extrase din modelul AI pentru secțiile de vot.
        Modelul AI a fost rulat anterior pentru a extrage asocierile județ-UAT, care au fost salvate
        în directorul 'vote/ai_models/judet_uat_data/'.
        
        Datele utilizate:
        - judet_uat_list.pkl: lista tuturor asocierilor județ-UAT extrase din XLSX
        - resedinte_judete.pkl: dicționarul cu reședințele județelor pentru adăugarea candidaților județeni
        """
        batch_size = options['batch_size']
        self.stdout.write(f"Se folosește dimensiunea lotului de {batch_size} UAT-uri")
        
        # Obține numele tabelei din Django
        app_name = 'vote'
        model_name = 'localcandidate'
        table_name = f"{app_name}_{model_name}"
        
        # Verifică structura tabelei (doar pentru debug)
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            table_structure = cursor.fetchall()
            self.stdout.write(f"Structura tabelei {table_name}:")
            for column in table_structure:
                self.stdout.write(f"  {column}")

        # Calea către icoanele pentru genuri
        female_avatar_url = "http://localhost:8000/static/icons/female-user-icon.png"
        male_avatar_url = "http://localhost:8000/static/icons/male-user-icon.png"
        
        # Partidele politice românești
        partide = [
            "PSD - Partidul Social Democrat", 
            "PNL - Partidul Național Liberal",
            "USR - Uniunea Salvați România",
            "AUR - Alianța pentru Unirea Românilor",
            "UDMR - Uniunea Democrată Maghiară din România",
            "PMP - Partidul Mișcarea Populară",
            "PRO România", 
            "ALDE - Alianța Liberalilor și Democraților",
            "PLUS - Partidul Libertate, Unitate și Solidaritate",
            "REPER - Reînnoim Proiectul European al României",
            "Forța Dreptei",
            "Partidul Verde",
            "Independent"
        ]
        
        # Prenume românești 
        prenume_barbati = [
            "Alexandru", "Andrei", "Mihai", "Cristian", "Ionuț", "Ștefan", "Gabriel", "Marian", 
            "Nicolae", "Adrian", "Daniel", "Florin", "Ioan", "Vasile", "Constantin", "Bogdan", 
            "Vlad", "George", "Marius", "Cătălin", "Victor", "Răzvan", "Cosmin", "Dumitru", 
            "Robert", "Valentin", "Radu", "Lucian", "Dorin", "Liviu", "Iulian", "Sorin"
        ]
        
        prenume_femei = [
            "Maria", "Elena", "Ana", "Ioana", "Mihaela", "Andreea", "Cristina", "Daniela", 
            "Alexandra", "Adriana", "Nicoleta", "Simona", "Georgiana", "Florentina", "Monica", 
            "Alina", "Gabriela", "Diana", "Roxana", "Laura", "Carmen", "Raluca", "Iuliana", 
            "Oana", "Claudia", "Mădălina", "Camelia", "Mirela", "Luminița", "Florina", "Ramona"
        ]
        
        # Nume de familie românești
        nume_familie = [
            "Popa", "Popescu", "Pop", "Radu", "Dumitru", "Stan", "Stoica", "Gheorghe", 
            "Matei", "Ciobanu", "Ionescu", "Rusu", "Constantin", "Dinu", "Mihai", "Ilie", 
            "Moldovan", "Florescu", "Bălan", "Diaconu", "Cojocaru", "Mazilu", "Drăghici", 
            "Tudor", "Iordache", "Lupescu", "Enache", "Marin", "Nistor", "Dumitrescu",
            "Cristea", "Dobre", "Șerban", "Vlad", "Neagu", "Mocanu", "Pavel", "Filip",
            "Lazăr", "Bucur", "Manea", "Avram", "Badea", "Sava", "Neacșu", "Anghel"
        ]
        
        # Generează un nume aleatoriu și determină genul
        def genereaza_nume_si_gen():
            gen = random.choice(['M', 'F'])
            if gen == 'M':
                prenume = random.choice(prenume_barbati)
                # Pentru bărbați, setăm URL-ul corespunzător
                photo_url = male_avatar_url
            else:
                prenume = random.choice(prenume_femei)
                # Pentru femei, setăm URL-ul corespunzător
                photo_url = female_avatar_url
                
            nume = random.choice(nume_familie)
            return f"{prenume} {nume}", gen, photo_url
        
        # Verifică dacă trebuie să ștergem candidații existenți
        if options['clean']:
            try:
                with connection.cursor() as cursor:
                    if options['judet']:
                        # Șterge doar candidații pentru județul specificat
                        judet = options['judet']
                        cursor.execute(f"DELETE FROM {table_name} WHERE county = %s", [judet])
                        self.stdout.write(self.style.SUCCESS(f"S-au șters candidații pentru județul {judet}"))
                    else:
                        # Șterge toți candidații
                        cursor.execute(f"DELETE FROM {table_name}")
                        self.stdout.write(self.style.SUCCESS(f"S-au șters toți candidații existenți"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Eroare la ștergerea candidaților: {e}"))
        
        # Încărcarea datelor despre județe și UAT-uri
        try:
            # Folosim calea bazată pe settings.BASE_DIR pentru a fi siguri că găsim fișierele
            data_dir = os.path.join(settings.BASE_DIR, 'vote', 'ai_models', 'judet_uat_data')
            
            # Verificăm dacă directorul există
            if not os.path.exists(data_dir):
                self.stdout.write(self.style.ERROR(f"Directorul {data_dir} nu există!"))
                self.stdout.write(self.style.WARNING(f"Încercăm calea absolută alternativă..."))
                
                # Încercăm cu calea absolută specificată
                data_dir = r'C:\Users\brj\Desktop\voting\vote\ai_models\judet_uat_data'
                
                if not os.path.exists(data_dir):
                    self.stdout.write(self.style.ERROR(f"Nici directorul {data_dir} nu există!"))
                    return
            
            # Încărcăm lista de tupluri (JUDET, UAT)
            judet_uat_path = os.path.join(data_dir, 'judet_uat_list.pkl')
            if not os.path.exists(judet_uat_path):
                self.stdout.write(self.style.ERROR(f"Fișierul {judet_uat_path} nu există!"))
                return
                
            with open(judet_uat_path, 'rb') as f:
                judet_uat_list = pickle.load(f)
            
            # Încărcăm dicționarul cu reședința fiecărui județ
            resedinte_path = os.path.join(data_dir, 'resedinte_judete.pkl')
            if not os.path.exists(resedinte_path):
                self.stdout.write(self.style.ERROR(f"Fișierul {resedinte_path} nu există!"))
                return
                
            with open(resedinte_path, 'rb') as f:
                resedinte_judete = pickle.load(f)
            
            self.stdout.write(f"S-au încărcat {len(judet_uat_list)} combinații județ-UAT și {len(resedinte_judete)} reședințe de județ")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Eroare la încărcarea datelor: {e}"))
            return
        
        # Filtrăm datele în funcție de parametrii specificați
        if options['judet']:
            judet_filter = options['judet']
            judet_uat_list = [item for item in judet_uat_list if item[0] == judet_filter]
            self.stdout.write(f"Filtrare pentru județul {judet_filter}: {len(judet_uat_list)} UAT-uri găsite")
            
            if options['uat']:
                uat_filter = options['uat']
                judet_uat_list = [item for item in judet_uat_list if item[1] == uat_filter]
                self.stdout.write(f"Filtrare pentru UAT-ul {uat_filter}: {len(judet_uat_list)} combinații găsite")
        
        # Procesare
        total_candidates = 0
        locations_processed = 0
        
        # Împărțim UAT-urile în loturi mai mici pentru a evita tranzacții prea mari
        total_uat = len(judet_uat_list)
        num_batches = (total_uat + batch_size - 1) // batch_size
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_uat)
            batch = judet_uat_list[start_idx:end_idx]
            
            self.stdout.write(f"Procesare lot {batch_idx+1}/{num_batches} ({start_idx}-{end_idx-1} din {total_uat} UAT-uri)")
            
            # Procesăm fiecare UAT individual pentru a evita erori la nivel de lot
            batch_candidates = 0
            batch_locations = 0
            
            for judet, uat in batch:
                # Folosim o tranzacție separată pentru fiecare UAT
                with transaction.atomic():
                    try:
                        # Determinăm dacă acest UAT este reședință de județ
                        este_resedinta = uat == resedinte_judete.get(judet)
                        
                        # Determinăm numărul de candidați în funcție de tipul UAT-ului
                        if 'MUNICIPIUL' in uat:
                            nr_primari = random.randint(4, 7)
                            nr_consilieri = random.randint(10, 15)
                        elif 'ORAȘ' in uat or 'ORASUL' in uat or 'ORAŞUL' in uat:
                            nr_primari = random.randint(3, 5)
                            nr_consilieri = random.randint(6, 10)
                        elif 'SECTORUL' in uat and ('BUCUREŞTI' in uat or 'BUCURESTI' in uat):
                            # Sectoarele București, tratate similar cu municipiile
                            nr_primari = random.randint(4, 7)
                            nr_consilieri = random.randint(10, 15)
                        else:
                            # Comune
                            nr_primari = random.randint(2, 4)
                            nr_consilieri = random.randint(4, 8)
                        
                        # Lista temporară pentru SQL
                        insert_values = []
                        
                        # Verifică ce coloane are tabela
                        with connection.cursor() as cursor:
                            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                            columns = [col[0] for col in cursor.fetchall()]
                            self.stdout.write(f"Coloanele din tabelă: {', '.join(columns)}")
                            
                            # Determinăm numele corect al coloanei pentru partid (party sau party_id)
                            party_column = 'party_id' if 'party_id' in columns else 'party'
                            self.stdout.write(f"Se folosește coloana {party_column} pentru partid")
                            
                            # Verificăm dacă avem coloana pentru gen
                            has_gender_column = 'gender' in columns
                            
                            # Dacă nu există coloana pentru gen, o adăugăm
                            if not has_gender_column:
                                try:
                                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN gender CHAR(1) NULL")
                                    self.stdout.write("S-a adăugat coloana 'gender' în tabelă")
                                    has_gender_column = True
                                except Exception as e:
                                    self.stdout.write(self.style.WARNING(f"Nu s-a putut adăuga coloana 'gender': {e}"))
                        
                        # Contoare pentru numerele electorale
                        counter_mayor = 1
                        counter_councilor = 1
                        counter_county_president = 1
                        counter_county_councilor = 1
                        
                        # 1. Adăugăm candidați pentru primar
                        for _ in range(nr_primari):
                            partid = random.choice(partide)
                            nume, gen, photo_url = genereaza_nume_si_gen()
                            electoral_number = counter_mayor
                            counter_mayor += 1
                            
                            # Determin party_name (aceeași valoare ca partid)
                            party_name = partid
                            
                            # Creăm dicționarul de valori
                            candidate_data = {
                                'name': nume,
                                'party_id': partid,
                                'party': partid,  # Ambele party și party_id primesc aceeași valoare
                                'position': 'mayor',
                                'county': judet,
                                'city': uat,
                                'photo_url': photo_url,
                                'electoral_number': electoral_number,
                                'party_name': party_name
                            }
                            
                            # Adaugă informația despre gen dacă tabela are coloana
                            if has_gender_column:
                                candidate_data['gender'] = gen
                            
                            # Adaug în lista de valori pentru inserare
                            insert_values.append(candidate_data)
                        
                        # 2. Adăugăm consilieri locali
                        for _ in range(nr_consilieri):
                            partid = random.choice(partide)
                            nume, gen, photo_url = genereaza_nume_si_gen()
                            electoral_number = counter_councilor
                            counter_councilor += 1
                            
                            # Determin party_name (aceeași valoare ca partid)
                            party_name = partid
                            
                            # Creăm dicționarul de valori
                            candidate_data = {
                                'name': nume,
                                'party_id': partid,
                                'party': partid,  # Ambele party și party_id primesc aceeași valoare
                                'position': 'councilor',
                                'county': judet,
                                'city': uat,
                                'photo_url': photo_url,
                                'electoral_number': electoral_number,
                                'party_name': party_name
                            }
                            
                            # Adaugă informația despre gen dacă tabela are coloana
                            if has_gender_column:
                                candidate_data['gender'] = gen
                            
                            # Adaug în lista de valori pentru inserare
                            insert_values.append(candidate_data)
                        
                        # 3. Dacă UAT-ul este reședința județului, adăugăm și candidați pentru funcții județene
                        if este_resedinta:
                            self.stdout.write(f"Adăugăm candidați județeni pentru {judet}, {uat} (reședință de județ)")
                            
                            # Președinți consiliu județean
                            for _ in range(random.randint(3, 5)):
                                partid = random.choice(partide)
                                nume, gen, photo_url = genereaza_nume_si_gen()
                                electoral_number = counter_county_president
                                counter_county_president += 1
                                
                                # Determin party_name (aceeași valoare ca partid)
                                party_name = partid
                                
                                # Creăm dicționarul de valori
                                candidate_data = {
                                    'name': nume,
                                    'party_id': partid,
                                    'party': partid,  # Ambele party și party_id primesc aceeași valoare
                                    'position': 'county_president',
                                    'county': judet,
                                    'city': uat,
                                    'photo_url': photo_url,
                                    'electoral_number': electoral_number,
                                    'party_name': party_name
                                }
                                
                                # Adaugă informația despre gen dacă tabela are coloana
                                if has_gender_column:
                                    candidate_data['gender'] = gen
                                
                                # Adaug în lista de valori pentru inserare
                                insert_values.append(candidate_data)
                            
                            # Consilieri județeni
                            for _ in range(random.randint(8, 15)):
                                partid = random.choice(partide)
                                nume, gen, photo_url = genereaza_nume_si_gen()
                                electoral_number = counter_county_councilor
                                counter_county_councilor += 1
                                
                                # Determin party_name (aceeași valoare ca partid)
                                party_name = partid
                                
                                # Creăm dicționarul de valori
                                candidate_data = {
                                    'name': nume,
                                    'party_id': partid,
                                    'party': partid,  # Ambele party și party_id primesc aceeași valoare
                                    'position': 'county_councilor',
                                    'county': judet,
                                    'city': uat,
                                    'photo_url': photo_url,
                                    'electoral_number': electoral_number,
                                    'party_name': party_name
                                }
                                
                                # Adaugă informația despre gen dacă tabela are coloana
                                if has_gender_column:
                                    candidate_data['gender'] = gen
                                
                                # Adaug în lista de valori pentru inserare
                                insert_values.append(candidate_data)
                        
                        # 4. Salvăm candidații în baza de date folosind SQL direct
                        if insert_values:
                            with connection.cursor() as cursor:
                                # Prepare parametrii pentru SQL
                                for candidate in insert_values:
                                    # Construiesc șirul de coloane și valorile pentru INSERT
                                    columns_str = ', '.join(candidate.keys())
                                    placeholders = ', '.join(['%s'] * len(candidate))
                                    values = list(candidate.values())
                                    
                                    # SQL pentru inserare
                                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                                    cursor.execute(sql, values)
                                
                                batch_candidates += len(insert_values)
                                batch_locations += 1
                                
                                self.stdout.write(self.style.SUCCESS(
                                    f"Adăugat {len(insert_values)} candidați pentru {judet}, {uat}"
                                ))
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Eroare la procesarea {judet}, {uat}: {str(e)}"))
                        # Continuăm cu următorul UAT
            
            # Actualizăm totalurile
            total_candidates += batch_candidates
            locations_processed += batch_locations
            
            self.stdout.write(self.style.SUCCESS(
                f"Lot {batch_idx+1} finalizat: {batch_candidates} candidați adăugați pentru {batch_locations} UAT-uri"
            ))
        
        # Mesaj final
        self.stdout.write(self.style.SUCCESS(
            f"Procesare completă! S-au adăugat {total_candidates} candidați pentru {locations_processed} locații."
        ))