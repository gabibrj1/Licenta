from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date
from local_candidates.models import (
    ElectionCycle, LocalElectionType, LocalPosition,
    LocalElectionRule, SignificantCandidate, ImportantEvent,
    LegislationChange
)

class Command(BaseCommand):
    help = 'Populează baza de date cu informații despre alegerile locale'

    def handle(self, *args, **kwargs):
        self.stdout.write('Începe popularea bazei de date pentru alegerile locale...')
        
        # Folosim o tranzacție pentru a asigura consistența datelor
        with transaction.atomic():
            # Șterge datele existente
            self.clear_existing_data()
            
            # Populăm ciclurile electorale
            self.populate_election_cycles()
            
            # Populăm tipurile de alegeri locale
            self.populate_election_types()
            
            # Populăm pozițiile administrative locale
            self.populate_positions()
            
            # Populăm regulile electorale
            self.populate_election_rules()
            
            # Populăm candidați semnificativi
            self.populate_significant_candidates()
            
            # Populăm evenimente importante
            self.populate_important_events()
            
            # Populăm modificări legislative
            self.populate_legislation_changes()

        self.stdout.write(self.style.SUCCESS('Popularea bazei de date pentru alegerile locale s-a încheiat cu succes!'))

    def clear_existing_data(self):
        """Șterge datele existente din tabele"""
        LegislationChange.objects.all().delete()
        ImportantEvent.objects.all().delete()
        SignificantCandidate.objects.all().delete()
        LocalElectionRule.objects.all().delete()
        LocalPosition.objects.all().delete()
        LocalElectionType.objects.all().delete()
        ElectionCycle.objects.all().delete()
        self.stdout.write('Datele existente au fost șterse.')

    def populate_election_cycles(self):
        """Populează ciclurile electorale locale"""
        election_cycles = [
            {
                'year': 1992,
                'description': 'Primele alegeri locale după căderea regimului comunist. S-au ales primari, consilieri locali și consilieri județeni.',
                'turnout_percentage': 65.0,
                'total_voters': 10500000
            },
            {
                'year': 1996,
                'description': 'Alegeri locale organizate simultan cu alegerile parlamentare și prezidențiale.',
                'turnout_percentage': 56.5,
                'total_voters': 10200000
            },
            {
                'year': 2000,
                'description': 'Alegeri locale marcate de consolidarea partidelor post-comuniste și apariția unor forțe politice noi.',
                'turnout_percentage': 50.8,
                'total_voters': 9800000
            },
            {
                'year': 2004,
                'description': 'Alegeri locale cu o prezență mai ridicată, marcate de competiția acerbă PSD-PNL-PD.',
                'turnout_percentage': 54.2,
                'total_voters': 10100000
            },
            {
                'year': 2008,
                'description': 'Primele alegeri locale de după aderarea României la Uniunea Europeană. S-a introdus sistemul uninominal pentru consiliile locale.',
                'turnout_percentage': 48.7,
                'total_voters': 9600000
            },
            {
                'year': 2012,
                'description': 'Alegeri marcate de tensiuni politice și comasate cu alegeri parlamentare.',
                'turnout_percentage': 56.3,
                'total_voters': 10300000
            },
            {
                'year': 2016,
                'description': 'Alegeri locale organizate sub noua legislație electorală, cu un singur tur pentru primari.',
                'turnout_percentage': 48.4,
                'total_voters': 9400000
            },
            {
                'year': 2020,
                'description': 'Alegeri locale organizate în contextul pandemiei COVID-19, cu măsuri sanitare stricte.',
                'turnout_percentage': 46.6,
                'total_voters': 9200000
            },
            {
                'year': 2024,
                'description': 'Alegeri locale organizate simultan cu alegerile parlamentare europene. Marcate de dezbaterea privind revenirea la două tururi pentru primari.',
                'turnout_percentage': 49.2,
                'total_voters': 9500000
            }
        ]
        
        for cycle_data in election_cycles:
            ElectionCycle.objects.create(**cycle_data)
            
        self.stdout.write(f'Au fost adăugate {len(election_cycles)} cicluri electorale.')

    def populate_election_types(self):
        """Populează tipurile de alegeri locale"""
        election_types = [
            {
                'name': 'Alegeri pentru primar',
                'description': 'Alegeri pentru funcția de primar al unei localități (municipiu, oraș sau comună).'
            },
            {
                'name': 'Alegeri pentru consilii locale',
                'description': 'Alegeri pentru membrii consiliilor locale din municipii, orașe și comune.'
            },
            {
                'name': 'Alegeri pentru consilii județene',
                'description': 'Alegeri pentru membrii consiliilor județene.'
            },
            {
                'name': 'Alegeri pentru președinți de consilii județene',
                'description': 'Alegeri pentru funcția de președinte al consiliului județean, introduse în 2008.'
            }
        ]
        
        for type_data in election_types:
            LocalElectionType.objects.create(**type_data)
            
        self.stdout.write(f'Au fost adăugate {len(election_types)} tipuri de alegeri locale.')

    def populate_positions(self):
        """Populează pozițiile administrative locale"""
        positions_data = [
            {
                'name': 'Primar municipiu reședință de județ',
                'description': 'Conducătorul administrației publice locale dintr-un municipiu reședință de județ. Roluri: reprezentarea orașului, conducerea serviciilor publice, emiterea de dispoziții, propunerea bugetului local.',
                'election_type_name': 'Alegeri pentru primar',
                'importance': 3
            },
            {
                'name': 'Primar sector București',
                'description': 'Conducătorul administrației publice locale dintr-un sector al municipiului București. Are atribuții similare cu primarii de municipii.',
                'election_type_name': 'Alegeri pentru primar',
                'importance': 3
            },
            {
                'name': 'Primar General al Municipiului București',
                'description': 'Conducătorul administrației publice la nivelul întregului municipiu București. Coordonează activitățile de interes general și colaborează cu primarii de sectoare.',
                'election_type_name': 'Alegeri pentru primar',
                'importance': 3
            },
            {
                'name': 'Primar municipiu',
                'description': 'Conducătorul administrației publice locale dintr-un municipiu. Roluri similare cu primarii de municipii reședință de județ, dar la scara unui municipiu mai mic.',
                'election_type_name': 'Alegeri pentru primar',
                'importance': 2
            },
            {
                'name': 'Primar oraș',
                'description': 'Conducătorul administrației publice locale dintr-un oraș. Administrează interesele comunității la nivelul orașului respectiv.',
                'election_type_name': 'Alegeri pentru primar',
                'importance': 2
            },
            {
                'name': 'Primar comună',
                'description': 'Conducătorul administrației publice locale dintr-o comună. Administrează interesele comunității la nivelul comunei respective.',
                'election_type_name': 'Alegeri pentru primar',
                'importance': 1
            },
            {
                'name': 'Președinte consiliu județean',
                'description': 'Conducătorul executiv al consiliului județean. Coordonează activitatea consiliului județean și reprezintă județul în relațiile cu alte instituții.',
                'election_type_name': 'Alegeri pentru președinți de consilii județene',
                'importance': 3
            },
            {
                'name': 'Consilier local',
                'description': 'Membru al consiliului local, cu rol deliberativ la nivelul unei localități (municipiu, oraș sau comună).',
                'election_type_name': 'Alegeri pentru consilii locale',
                'importance': 1
            },
            {
                'name': 'Consilier județean',
                'description': 'Membru al consiliului județean, cu rol deliberativ la nivelul unui județ.',
                'election_type_name': 'Alegeri pentru consilii județene',
                'importance': 2
            }
        ]
        
        for position_data in positions_data:
            # Extragem numele tipului de alegeri
            election_type_name = position_data.pop('election_type_name')
            
            # Găsim tipul de alegeri în baza de date
            try:
                election_type = LocalElectionType.objects.get(name=election_type_name)
                
                # Creăm poziția
                LocalPosition.objects.create(
                    election_type=election_type,
                    **position_data
                )
            except LocalElectionType.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Tipul de alegeri {election_type_name} nu există în baza de date.'))
        
        self.stdout.write(f'Au fost adăugate {len(positions_data)} poziții administrative locale.')

    def populate_election_rules(self):
        """Populează regulile electorale locale"""
        rules_data = [
            {
                'title': 'Alegerea primarului într-un singur tur',
                'description': 'Primarul este ales în cadrul unui singur tur de scrutin, fiind declarat câștigător candidatul care obține cele mai multe voturi valabil exprimate.',
                'election_type_name': 'Alegeri pentru primar',
                'since_year': 2012,
                'is_current': True
            },
            {
                'title': 'Alegerea primarului în două tururi',
                'description': 'Primarul era ales prin majoritatea absolută (peste 50% din voturi) în primul tur, sau prin balotaj între primii doi clasați, în al doilea tur, dacă niciunul nu obținea majoritatea în primul tur.',
                'election_type_name': 'Alegeri pentru primar',
                'since_year': 1992,
                'is_current': False
            },
            {
                'title': 'Pragul electoral pentru consilii locale',
                'description': 'Partidele politice trebuie să obțină minimum 5% din voturi pentru a obține mandate în consiliile locale. Alianțele politice au un prag mai mare, în funcție de numărul membrilor.',
                'election_type_name': 'Alegeri pentru consilii locale',
                'since_year': 2000,
                'is_current': True
            },
            {
                'title': 'Metoda de atribuire a mandatelor D\'Hondt',
                'description': 'Metodă de alocare a mandatelor pentru consiliile locale și județene, care favorizează partidele mai mari. Se aplică după depășirea pragului electoral.',
                'election_type_name': 'Alegeri pentru consilii locale',
                'since_year': 1992,
                'is_current': True
            },
            {
                'title': 'Alegerea președintelui consiliului județean prin vot direct',
                'description': 'Președintele consiliului județean este ales prin vot universal, egal, direct, secret și liber exprimat.',
                'election_type_name': 'Alegeri pentru președinți de consilii județene',
                'since_year': 2008,
                'is_current': True
            },
            {
                'title': 'Alegerea președintelui consiliului județean de către consilieri',
                'description': 'Președintele consiliului județean era ales de către și dintre membrii consiliului județean.',
                'election_type_name': 'Alegeri pentru președinți de consilii județene',
                'since_year': 1992,
                'is_current': False
            },
            {
                'title': 'Reprezentarea minorităților naționale',
                'description': 'Organizațiile minorităților naționale care nu depășesc pragul electoral pot obține un mandat de consilier dacă obțin un număr de voturi valabil exprimate egal cu cel puțin 5% din coeficientul electoral.',
                'election_type_name': 'Alegeri pentru consilii locale',
                'since_year': 1996,
                'is_current': True
            }
        ]
        
        for rule_data in rules_data:
            # Extragem numele tipului de alegeri
            election_type_name = rule_data.pop('election_type_name')
            
            # Găsim tipul de alegeri în baza de date
            try:
                election_type = LocalElectionType.objects.get(name=election_type_name)
                
                # Creăm regula electorală
                LocalElectionRule.objects.create(
                    election_type=election_type,
                    **rule_data
                )
            except LocalElectionType.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Tipul de alegeri {election_type_name} nu există în baza de date.'))
        
        self.stdout.write(f'Au fost adăugate {len(rules_data)} reguli electorale.')

    def populate_significant_candidates(self):
        """Populează candidați locali semnificativi"""
        candidates_data = [
            {
                'name': 'Gabriela Firea',
                'position_name': 'Primar General al Municipiului București',
                'location': 'București',
                'election_cycle_year': 2016,
                'party': 'Partidul Social Democrat',
                'photo_url': 'https://example.com/firea.jpg',
                'achievement': 'Prima femeie aleasă primar general al Capitalei. A implementat programele sociale precum stimulentele pentru nou-născuți și vouchere pentru elevi.'
            },
            {
                'name': 'Emil Boc',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Cluj-Napoca',
                'election_cycle_year': 2012,
                'party': 'Partidul Democrat Liberal / Partidul Național Liberal',
                'photo_url': 'https://example.com/boc.jpg',
                'achievement': 'A transformat Cluj-Napoca într-un pol de dezvoltare tehnologică și culturală. Reales pentru multiple mandate consecutive.'
            },
            {
                'name': 'Ilie Bolojan',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Oradea',
                'election_cycle_year': 2008,
                'party': 'Partidul Național Liberal',
                'photo_url': 'https://example.com/bolojan.jpg',
                'achievement': 'A implementat proiecte majore de regenerare urbană și atragere de fonduri europene, transformând Oradea într-un model de administrație eficientă.'
            },
            {
                'name': 'Nicușor Dan',
                'position_name': 'Primar General al Municipiului București',
                'location': 'București',
                'election_cycle_year': 2020,
                'party': 'Independent',
                'photo_url': 'https://example.com/nicusor.jpg',
                'achievement': 'Fondator al Asociației Salvați Bucureștiul și al USR. A câștigat primăria capitalei ca independent, cu un program axat pe rezolvarea problemelor de infrastructură.'
            },
            {
                'name': 'Dominic Fritz',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Timișoara',
                'election_cycle_year': 2020,
                'party': 'Uniunea Salvați România',
                'photo_url': 'https://example.com/fritz.jpg',
                'achievement': 'Primul cetățean german ales primar într-un oraș mare din România. A câștigat alegerile cu o platformă de transparență și modernizare.'
            },
            {
                'name': 'Allen Coliban',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Brașov',
                'election_cycle_year': 2020,
                'party': 'Uniunea Salvați România',
                'photo_url': 'https://example.com/coliban.jpg',
                'achievement': 'A câștigat primăria Brașovului pentru USR, promovând digitalizarea administrației și dezvoltarea durabilă.'
            },
            {
                'name': 'Elena Lasconi',
                'position_name': 'Primar oraș',
                'location': 'Câmpulung',
                'election_cycle_year': 2020,
                'party': 'Uniunea Salvați România',
                'photo_url': 'https://example.com/lasconi.jpg',
                'achievement': 'Fostă jurnalistă TV care a câștigat primăria orașului Câmpulung. Cunoscută pentru proiectele de transparentizare și modernizare.'
            },
            {
                'name': 'Traian Băsescu',
                'position_name': 'Primar General al Municipiului București',
                'location': 'București',
                'election_cycle_year': 2000,
                'party': 'Partidul Democrat',
                'photo_url': 'https://example.com/basescu.jpg',
                'achievement': 'A fost primar al Capitalei între 2000-2004, marcând începutul unor proiecte de infrastructură majore. A demisionat pentru a candida la președinția României.'
            },
            {
                'name': 'Gheorghe Funar',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Cluj-Napoca',
                'election_cycle_year': 1992,
                'party': 'Partidul Unității Naționale a Românilor',
                'photo_url': 'https://example.com/funar.jpg',
                'achievement': 'Controversat primar naționalist al Cluj-Napoca în perioada 1992-2004. Cunoscut pentru acțiunile de marcare a spațiului public în culorile drapelului României.'
            }
        ]
        
        for candidate_data in candidates_data:
            # Extragem numele poziției și anul ciclului electoral
            position_name = candidate_data.pop('position_name')
            election_cycle_year = candidate_data.pop('election_cycle_year')
            
            # Găsim poziția și ciclul electoral în baza de date
            try:
                position = LocalPosition.objects.get(name=position_name)
                election_cycle = ElectionCycle.objects.get(year=election_cycle_year)
                
                # Creăm candidatul
                SignificantCandidate.objects.create(
                    position=position,
                    election_cycle=election_cycle,
                    **candidate_data
                )
            except LocalPosition.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Poziția {position_name} nu există în baza de date.'))
            except ElectionCycle.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Ciclul electoral {election_cycle_year} nu există în baza de date.'))
        
        self.stdout.write(f'Au fost adăugați {len(candidates_data)} candidați locali semnificativi.')

    def populate_important_events(self):
        """Populează evenimente importante în alegerile locale"""
        events_data = [
            {
                'year': 1992,
                'title': 'Primele alegeri locale democratice',
                'description': 'Primele alegeri locale democratice organizate în România post-comunistă, marcând începutul procesului de descentralizare și autonomie locală.',
                'election_cycle_year': 1992,
                'importance': 3
            },
            {
                'year': 1996,
                'title': 'Prima alternanță politică majoră la nivel local',
                'description': 'Alegerile locale din 1996 au marcat prima schimbare politică majoră, cu multe primării trecând de la PDSR (actualul PSD) la partidele din Convenția Democratică.',
                'election_cycle_year': 1996,
                'importance': 3
            },
            {
                'year': 2000,
                'title': 'Revenirea PSD la conducerea multor administrații locale',
                'description': 'PDSR (ulterior PSD) revine la conducerea majorității consiliilor județene și a multor primării importante.',
                'election_cycle_year': 2000,
                'importance': 2
            },
            {
                'year': 2004,
                'title': 'Introducerea alegerilor în două tururi pentru primari',
                'description': 'A fost reconfirmată regula alegerii primarilor în două tururi, ceea ce a permis coalizarea forțelor politice între tururi.',
                'election_cycle_year': 2004,
                'importance': 2
            },
            {
                'year': 2008,
                'title': 'Alegerea directă a președinților de consilii județene',
                'description': 'Pentru prima dată, președinții consiliilor județene au fost aleși prin vot direct, nu de către consilierii județeni.',
                'election_cycle_year': 2008,
                'importance': 3
            },
            {
                'year': 2012,
                'title': 'Introducerea alegerilor într-un singur tur pentru primari',
                'description': 'Modificare legislativă majoră: primarii sunt aleși într-un singur tur de scrutin, ceea ce a favorizat partidele mari și candidații cu notorietate.',
                'election_cycle_year': 2012,
                'importance': 3
            },
            {
                'year': 2016,
                'title': 'Creșterea importanței candidaților independenți',
                'description': 'Alegeri marcate de creșterea numărului de candidați independenți și a șanselor lor de succes, în special în orașele mici și mijlocii.',
                'election_cycle_year': 2016,
                'importance': 2
            },
            {
                'year': 2020,
                'title': 'Alegeri locale în timpul pandemiei COVID-19',
                'description': 'Primele alegeri organizate în condiții de pandemie, cu măsuri sanitare stricte și o abordare diferită a campaniei electorale, bazată mai mult pe online.',
                'election_cycle_year': 2020,
                'importance': 3
            },
            {
                'year': 2024,
                'title': 'Comasarea alegerilor locale cu europarlamentarele',
                'description': 'Pentru prima dată în România, alegerile locale au fost organizate în aceeași zi cu alegerile pentru Parlamentul European, crescând complexitatea procesului electoral.',
                'election_cycle_year': 2024,
                'importance': 3
            }
        ]
        
        for event_data in events_data:
            # Extragem anul ciclului electoral
            election_cycle_year = event_data.pop('election_cycle_year', None)
            
            # Găsim ciclul electoral în baza de date
            election_cycle = None
            if election_cycle_year:
                try:
                    election_cycle = ElectionCycle.objects.get(year=election_cycle_year)
                except ElectionCycle.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Ciclul electoral {election_cycle_year} nu există în baza de date.'))
            
            # Creăm evenimentul
            ImportantEvent.objects.create(
                election_cycle=election_cycle,
                **event_data
            )
        
        self.stdout.write(f'Au fost adăugate {len(events_data)} evenimente importante.')

    def populate_legislation_changes(self):
        """Populează modificări legislative relevante pentru alegerile locale"""
        legislation_changes = [
            {
                'title': 'Legea administrației publice locale',
                'description': 'Legea 215/2001 a administrației publice locale a stabilit cadrul general pentru organizarea și funcționarea autorităților administrației publice locale.',
                'year': 2001,
                'law_number': 'Legea 215/2001',
                'impact': 'A definit clar atribuțiile primarilor, consiliilor locale și județene, precum și relațiile dintre acestea.'
            },
            {
                'title': 'Introducerea alegerilor într-un singur tur pentru primari',
                'description': 'Modificarea legislației electorale pentru a permite alegerea primarilor într-un singur tur de scrutin.',
                'year': 2011,
                'law_number': 'Legea 129/2011',
                'impact': 'A favorizat partidele mari și candidații cu notorietate, schimbând fundamental dinamica alegerilor locale.'
            },
            {
                'title': 'Alegerea directă a președinților de consilii județene',
                'description': 'Modificare legislativă pentru alegerea președinților consiliilor județene prin vot direct al cetățenilor.',
                'year': 2008,
                'law_number': 'OUG 1/2008',
                'impact': 'A crescut legitimitatea președinților de consilii județene și a schimbat strategiile de campanie la nivel județean.'
            },
            {
                'title': 'Codul Administrativ',
                'description': 'Adoptarea Codului Administrativ care a unificat majoritatea reglementărilor privind administrația publică locală.',
                'year': 2019,
                'law_number': 'OUG 57/2019',
                'impact': 'A clarificat statutul aleșilor locali, regimul incompatibilităților și al conflictelor de interese.'
            },
            {
                'title': 'Pragul de reprezentare pentru consiliile locale',
                'description': 'Stabilirea unui prag electoral de 5% pentru partidele politice care doresc să obțină mandate în consiliile locale.',
                'year': 2004,
                'law_number': 'Legea 67/2004',
                'impact': 'A redus fragmentarea politică în consiliile locale și a favorizat partidele mari.'
            },
            {
                'title': 'Legea pentru alegerea autorităților administrației publice locale',
                'description': 'Cadrul legal actualizat pentru organizarea și desfășurarea alegerilor locale.',
                'year': 2015,
                'law_number': 'Legea 115/2015',
                'impact': 'A integrat toate modificările legislative anterioare și a stabilit proceduri clare pentru procesul electoral local.'
            },
            {
                'title': 'Reglementarea finanțării campaniilor electorale locale',
                'description': 'Limitarea și transparentizarea finanțării campaniilor electorale pentru alegerile locale.',
                'year': 2016,
                'law_number': 'Legea 334/2006, modificată',
                'impact': 'A crescut transparența finanțării campaniilor și a limitat posibilitățile de abuz în finanțarea candidaților.'
            },
            {
                'title': 'Implementarea votului electronic în secțiile de votare',
                'description': 'Introducerea Sistemului Informatic de Monitorizare a Prezenței la Vot și de Prevenire a Votului Ilegal (SIMPV).',
                'year': 2016,
                'law_number': 'Hotărârea BEC nr. 30/2016',
                'impact': 'A crescut acuratețea procesului electoral și a redus semnificativ posibilitățile de fraudă electorală.'
            },
            {
                'title': 'Măsuri speciale pentru alegerile în perioada pandemiei',
                'description': 'Reglementări pentru organizarea alegerilor locale în condiții de siguranță sanitară în contextul COVID-19.',
                'year': 2020,
                'law_number': 'Legea 135/2020',
                'impact': 'A permis desfășurarea procesului electoral în condiții de siguranță, asigurând dreptul la vot.'
            }
        ]
        
        for change_data in legislation_changes:
            LegislationChange.objects.create(**change_data)
            
        self.stdout.write(f'Au fost adăugate {len(legislation_changes)} modificări legislative.')