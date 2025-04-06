import random
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction, connection
from vote.models import ParliamentaryParty

class Command(BaseCommand):
    help = 'Populează baza de date cu partide pentru alegerile parlamentare'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Șterge partidele existente înainte de a adăuga altele noi'
        )
    
    def handle(self, *args, **options):
        # Obține numele tabelei din Django
        app_name = 'vote'
        model_name = 'parliamentaryparty'
        table_name = f"{app_name}_{model_name}"
        votes_table = "vote_parliamentaryvote"
        
        # Verifică structura tabelei (doar pentru debug)
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            table_structure = cursor.fetchall()
            self.stdout.write(f"Structura tabelei {table_name}:")
            for column in table_structure:
                self.stdout.write(f"  {column}")

        # Verifică dacă trebuie să ștergem partidele existente
        if options['clean']:
            try:
                # Primul pas: șterge voturile care referențiază partidele
                with connection.cursor() as cursor:
                    self.stdout.write("Se șterg mai întâi voturile parlamentare existente...")
                    cursor.execute(f"DELETE FROM {votes_table}")
                    self.stdout.write(self.style.SUCCESS(f"S-au șters toate voturile parlamentare existente"))
                
                # Al doilea pas: șterge partidele
                with connection.cursor() as cursor:
                    cursor.execute(f"DELETE FROM {table_name}")
                    self.stdout.write(self.style.SUCCESS(f"S-au șters toate partidele parlamentare existente"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Eroare la ștergerea partidelor: {e}"))
        
        # Lista partidelor parlamentare
        partide_parlamentare = [
            {
                'name': 'Alianța Electorală România Înainte',
                'abbreviation': 'AERI',
                'description': 'Alianță formată din PSD, PNL și UDMR pentru alegerile parlamentare din acest an.',
                'logo_url': "http://localhost:8000/static/icons/romania-inainte.png",
                'order_nr': 1
            },
            {
                'name': 'Alianța pentru Unirea Românilor',
                'abbreviation': 'AUR',
                'description': 'Partid politic parlamentar de orientare naționalistă și conservatoare.',
                'logo_url': "http://localhost:8000/static/icons/aur.jpeg",
                'order_nr': 2
            },
            {
                'name': 'Uniunea Salvați România',
                'abbreviation': 'USR',
                'description': 'Partid politic parlamentar de orientare centristă, promotor al transparenței și reformei administrației.',
                'logo_url': "http://localhost:8000/static/icons/usr.png",
                'order_nr': 3
            },
            {
                'name': 'Partidul Umanist Social Liberal',
                'abbreviation': 'PUSL',
                'description': 'Partid politic care promovează valorile umaniste și combină politici sociale cu elemente liberale.',
                'logo_url': "http://localhost:8000/static/icons/pusl.png",
                'order_nr': 4
            },
            {
                'name': 'Partidul Mișcarea România Mare',
                'abbreviation': 'PMRM',
                'description': 'Partid politic naționalist care susține dezvoltarea economiei românești și suveranitatea națională.',
                'logo_url': "http://localhost:8000/static/icons/pmrm.png",
                'order_nr': 5
            },
            {
                'name': 'Partidul Național Conservator Român',
                'abbreviation': 'PNCR',
                'description': 'Partid care promovează valorile conservatoare și tradiția românească.',
                'logo_url': "http://localhost:8000/static/icons/pncr.png",
                'order_nr': 6
            },
            {
                'name': 'Partidul Noua Românie',
                'abbreviation': 'PNR',
                'description': 'Partid care militează pentru reformarea clasei politice și modernizarea instituțiilor statului.',
                'logo_url': "http://localhost:8000/static/icons/pnr.png",
                'order_nr': 7
            },
            {
                'name': 'Partidul Verde',
                'abbreviation': 'PV',
                'description': 'Partid ecologist care promovează politici de protejare a mediului și dezvoltare sustenabilă.',
                'logo_url': "http://localhost:8000/static/icons/pv.png",
                'order_nr': 8
            },
            {
                'name': 'Partidul Forța Dreptei',
                'abbreviation': 'PFD',
                'description': 'Partid de centru-dreapta care susține reformele democratice și integrarea europeană.',
                'logo_url': "http://localhost:8000/static/icons/forta.png",
                'order_nr': 9
            },
            {
                'name': 'Partidul Mișcarea Populară',
                'abbreviation': 'PMP',
                'description': 'Partid de centru-dreapta care promovează valori creștin-democrate și susține economia de piață.',
                'logo_url': "http://localhost:8000/static/icons/pmp.png",
                'order_nr': 10
            },
            {
                'name': 'Partidul România Liberă',
                'abbreviation': 'PRL',
                'description': 'Partid care susține politici liberale și reducerea intervenției statului în economie.',
                'logo_url': "http://localhost:8000/static/icons/prl.png",
                'order_nr': 11
            }
        ]
        
        # Folosim o tranzacție pentru a ne asigura că toate schimbările sunt aplicate sau niciuna
        with transaction.atomic():
            try:
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
                            for partid in partide_parlamentare:
                                if 'order_nr' in partid:
                                    partid['order'] = partid.pop('order_nr')

                # Verifică dacă partidele există deja pentru a evita duplicatele
                partide_adaugate = 0
                partide_sarite = 0
                
                for partid in partide_parlamentare:
                    with connection.cursor() as cursor:
                        # Verifică dacă partidul există deja
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE name = %s", [partid['name']])
                        count = cursor.fetchone()[0]
                        
                        if count > 0:
                            self.stdout.write(f"Partidul '{partid['name']}' există deja, se omite.")
                            partide_sarite += 1
                            continue
                        
                        # Construiesc șirul de coloane și valorile pentru INSERT
                        # Folosesc backticks pentru fiecare coloană pentru a evita probleme cu cuvintele rezervate
                        columns_str = ', '.join([f"`{col}`" for col in partid.keys()])
                        placeholders = ', '.join(['%s'] * len(partid))
                        values = list(partid.values())
                        
                        # SQL pentru inserare
                        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        cursor.execute(sql, values)
                        partide_adaugate += 1
                
                if partide_adaugate > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f"S-au adăugat {partide_adaugate} partide parlamentare în baza de date."
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        "Nu s-a adăugat niciun partid nou (toate partidele există deja)."
                    ))
                
                if partide_sarite > 0:
                    self.stdout.write(self.style.WARNING(
                        f"S-au omis {partide_sarite} partide existente."
                    ))
                
                # Verifică dacă inserarea a avut succes
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"Total partide parlamentare în bază: {count}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Eroare la adăugarea partidelor: {str(e)}"))
                raise