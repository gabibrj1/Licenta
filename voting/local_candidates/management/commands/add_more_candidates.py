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
    help = 'Adaugă mai mulți candidați notabili pentru anii care lipsesc și reguli pentru consilii județene'

    def handle(self, *args, **kwargs):
        self.stdout.write('Începe adăugarea de candidați suplimentari și reguli...')
        
        # Folosim o tranzacție pentru a asigura consistența datelor
        with transaction.atomic():
            # Adăugăm candidați semnificativi suplimentari
            self.add_more_candidates()
            
            # Adăugăm reguli pentru consilii județene
            self.add_council_rules()

        self.stdout.write(self.style.SUCCESS('Adăugarea de candidați și reguli suplimentare s-a încheiat cu succes!'))

    def add_more_candidates(self):
        """Adaugă mai mulți candidați locali semnificativi pentru anii care lipsesc"""
        candidates_data = [
            # Candidați pentru 2024
            {
                'name': 'Cătălin Cherecheș',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Baia Mare',
                'election_cycle_year': 2024,
                'party': 'Independent (anterior PSD)',
                'photo_url': 'https://example.com/chereches.jpg',
                'achievement': 'A fost reales ca primar al Baia Mare în ciuda problemelor legale, fiind unul dintre primarii cu cele mai controversate mandate din România recentă.'
            },
            {
                'name': 'Ciprian Ciucu',
                'position_name': 'Primar sector București',
                'location': 'Sectorul 6',
                'election_cycle_year': 2024,
                'party': 'Partidul Național Liberal',
                'photo_url': 'https://example.com/ciucu.jpg',
                'achievement': 'A implementat proiecte moderne de urbanism și a promovat transparența administrativă, îmbunătățind infrastructura urbană din Sectorul 6.'
            },
            
            # Candidați pentru 2016 (suplimentar)
            {
                'name': 'Astrid Fodor',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Sibiu',
                'election_cycle_year': 2016,
                'party': 'Forumul Democrat al Germanilor din România',
                'photo_url': 'https://example.com/fodor.jpg',
                'achievement': 'Prima femeie primar a Sibiului, a continuat proiectele de dezvoltare urbană începute de Klaus Iohannis, menținând Sibiul ca un important centru cultural și turistic.'
            },
            {
                'name': 'Lia Olguța Vasilescu',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Craiova',
                'election_cycle_year': 2016,
                'party': 'Partidul Social Democrat',
                'photo_url': 'https://example.com/vasilescu.jpg',
                'achievement': 'A implementat proiecte majore de infrastructură în Craiova, inclusiv modernizarea centrului istoric și a transportului public.'
            },
            
            # Candidați pentru 2004
            {
                'name': 'Sorin Oprescu',
                'position_name': 'Primar General al Municipiului București',
                'location': 'București',
                'election_cycle_year': 2004,
                'party': 'Independent (susținut de PSD)',
                'photo_url': 'https://example.com/oprescu.jpg',
                'achievement': 'Deși a pierdut alegerile în fața lui Adriean Videanu, candidatura sa independentă a marcat o nouă eră a candidaturilor independente în politica locală românească.'
            },
            {
                'name': 'Adriean Videanu',
                'position_name': 'Primar General al Municipiului București',
                'location': 'București',
                'election_cycle_year': 2004,
                'party': 'Partidul Democrat',
                'photo_url': 'https://example.com/videanu.jpg',
                'achievement': 'A câștigat primăria Bucureștiului continuând proiectele de infrastructură începute de Traian Băsescu, concentrându-se pe modernizarea infrastructurii urbane.'
            },
            {
                'name': 'Gheorghe Falcă',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Arad',
                'election_cycle_year': 2004,
                'party': 'Partidul Democrat',
                'photo_url': 'https://example.com/falca.jpg',
                'achievement': 'A început o serie de mandate care au transformat Aradul, implementând proiecte de regenerare urbană și infrastructură modernă.'
            },
            
            # Candidați pentru 1996
            {
                'name': 'Victor Ciorbea',
                'position_name': 'Primar General al Municipiului București',
                'location': 'București',
                'election_cycle_year': 1996,
                'party': 'Convenția Democrată Română',
                'photo_url': 'https://example.com/ciorbea.jpg',
                'achievement': 'A câștigat primăria Capitalei ca parte a victoriei CDR în alegerile din 1996. Ulterior a demisionat pentru a deveni prim-ministru al României.'
            },
            {
                'name': 'Viorel Lis',
                'position_name': 'Primar General al Municipiului București',
                'location': 'București',
                'election_cycle_year': 1996,
                'party': 'Convenția Democrată Română',
                'photo_url': 'https://example.com/lis.jpg',
                'achievement': 'A preluat primăria după demisia lui Victor Ciorbea, devenind una dintre cele mai cunoscute figuri ale administrației locale bucureștene din anii 1990.'
            },
            {
                'name': 'Gheorghe Ștefan',
                'position_name': 'Primar municipiu',
                'location': 'Piatra Neamț',
                'election_cycle_year': 1996,
                'party': 'Convenția Democrată Română',
                'photo_url': 'https://example.com/stefan.jpg',
                'achievement': 'A inițiat primele proiecte de modernizare a orașului Piatra Neamț după perioada comunistă, punând bazele dezvoltării acestui municipiu.'
            },
            
            # Candidați pentru 2012 (suplimentar)
            {
                'name': 'Nicolae Robu',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Timișoara',
                'election_cycle_year': 2012,
                'party': 'Uniunea Social-Liberală',
                'photo_url': 'https://example.com/robu.jpg',
                'achievement': 'A inițiat procesul de transformare a Timișoarei într-un centru tehnologic și de inovație, punând accentul pe dezvoltarea economică și educațională.'
            },
            
            # Candidați pentru 2008 (suplimentar)
            {
                'name': 'Sorin Frunzăverde',
                'position_name': 'Președinte consiliu județean',
                'location': 'Caraș-Severin',
                'election_cycle_year': 2008,
                'party': 'Partidul Democrat Liberal',
                'photo_url': 'https://example.com/frunzaverde.jpg',
                'achievement': 'Primul președinte de consiliu județean ales prin vot direct. A implementat proiecte importante de dezvoltare a infrastructurii în Caraș-Severin.'
            },
            
            # Candidați pentru 2000 (suplimentar)
            {
                'name': 'Dumitru Sechelariu',
                'position_name': 'Primar municipiu reședință de județ',
                'location': 'Bacău',
                'election_cycle_year': 2000,
                'party': 'Partidul Democrației Sociale din România',
                'photo_url': 'https://example.com/sechelariu.jpg',
                'achievement': 'A fost un primar controversat, cunoscut pentru stilul său autoritar, dar și pentru investițiile în infrastructura sportivă a orașului Bacău.'
            }
        ]
        
        candidates_added = 0
        
        for candidate_data in candidates_data:
            # Extragem numele poziției și anul ciclului electoral
            position_name = candidate_data.pop('position_name')
            election_cycle_year = candidate_data.pop('election_cycle_year')
            
            # Găsim poziția și ciclul electoral în baza de date
            try:
                position = LocalPosition.objects.get(name=position_name)
                election_cycle = ElectionCycle.objects.get(year=election_cycle_year)
                
                # Verificăm dacă există deja un candidat cu același nume pentru același ciclu electoral
                if not SignificantCandidate.objects.filter(
                    name=candidate_data['name'], 
                    election_cycle=election_cycle
                ).exists():
                    # Creăm candidatul
                    SignificantCandidate.objects.create(
                        position=position,
                        election_cycle=election_cycle,
                        **candidate_data
                    )
                    candidates_added += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Candidatul {candidate_data["name"]} există deja pentru anul {election_cycle_year}.'
                    ))
                    
            except LocalPosition.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Poziția {position_name} nu există în baza de date.'))
            except ElectionCycle.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Ciclul electoral {election_cycle_year} nu există în baza de date.'))
        
        self.stdout.write(f'Au fost adăugați {candidates_added} candidați locali suplimentari.')

    def add_council_rules(self):
        """Adaugă reguli electorale pentru consiliile județene"""
        rules_data = [
            {
                'title': 'Alegerea consilierilor județeni prin scrutin de listă',
                'description': 'Consilierii județeni sunt aleși prin vot pe liste de partid, folosind un scrutin proporțional cu prag electoral de 5%.',
                'election_type_name': 'Alegeri pentru consilii județene',
                'since_year': 1992,
                'is_current': True
            },
            {
                'title': 'Numărul de consilieri județeni proporțional cu populația',
                'description': 'Numărul de membri ai consiliului județean este stabilit în funcție de populația județului, variind de la 31 la 37 de consilieri.',
                'election_type_name': 'Alegeri pentru consilii județene',
                'since_year': 2001,
                'is_current': True
            },
            {
                'title': 'Aplicarea metodei d\'Hondt pentru alocarea mandatelor de consilier județean',
                'description': 'Mandatele de consilier județean se distribuie partidelor politice proporțional cu numărul de voturi obținute, folosind metoda d\'Hondt care favorizează partidele mari.',
                'election_type_name': 'Alegeri pentru consilii județene',
                'since_year': 1992,
                'is_current': True
            },
            {
                'title': 'Alegerea indirectă a conducerii consiliului județean (2016-2020)',
                'description': 'Între 2016 și 2020, președintele consiliului județean a fost ales indirect, din rândul consilierilor județeni, prin vot secret.',
                'election_type_name': 'Alegeri pentru consilii județene',
                'since_year': 2016,
                'is_current': False
            },
            {
                'title': 'Revenirea la alegerea directă a președintelui consiliului județean',
                'description': 'Din 2020, s-a revenit la alegerea președintelui consiliului județean prin vot direct al cetățenilor, într-un singur tur de scrutin.',
                'election_type_name': 'Alegeri pentru consilii județene',
                'since_year': 2020,
                'is_current': True
            }
        ]
        
        rules_added = 0
        
        for rule_data in rules_data:
            # Extragem numele tipului de alegeri
            election_type_name = rule_data.pop('election_type_name')
            
            # Găsim tipul de alegeri în baza de date
            try:
                election_type = LocalElectionType.objects.get(name=election_type_name)
                
                # Verificăm dacă există deja o regulă cu același titlu
                if not LocalElectionRule.objects.filter(
                    title=rule_data['title'],
                    election_type=election_type
                ).exists():
                    # Creăm regula electorală
                    LocalElectionRule.objects.create(
                        election_type=election_type,
                        **rule_data
                    )
                    rules_added += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Regula "{rule_data["title"]}" există deja pentru tipul de alegeri {election_type_name}.'
                    ))
                    
            except LocalElectionType.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Tipul de alegeri {election_type_name} nu există în baza de date.'))
        
        self.stdout.write(f'Au fost adăugate {rules_added} reguli electorale pentru consilii județene.')