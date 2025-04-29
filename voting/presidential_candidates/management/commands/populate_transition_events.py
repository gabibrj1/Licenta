from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date, datetime
from presidential_candidates.models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation, 
    HistoricalEvent, MediaInfluence, Controversy
)
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Populează baza de date cu evenimente legate de tranziția de la regimul comunist la democrație'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Începe popularea evenimentelor de tranziție de la comunism la democrație...'))

        # Adăugăm evenimente historice importante din perioada comunistă și a tranziției
        transition_events = [
            {
                'year': 1965,
                'title': 'Nicolae Ceaușescu devine conducătorul României',
                'description': 'Nicolae Ceaușescu devine Secretar General al Partidului Comunist Român, ' +
                              'marcând începutul a ceea ce va deveni unul dintre cele mai represive regimuri din Europa de Est.',
                'importance': 3
            },
            {
                'year': 1974,
                'title': 'Ceaușescu devine președinte al Republicii Socialiste România',
                'description': 'Nicolae Ceaușescu devine primul președinte al Republicii Socialiste România, ' +
                              'concentrând în mâinile sale atât puterea de partid, cât și cea de stat.',
                'importance': 2
            },
            {
                'year': 1980,
                'title': 'Începutul crizei economice',
                'description': 'România intră într-o criză economică severă, agravată de decizia lui Ceaușescu ' +
                              'de a plăti integral datoria externă, ceea ce duce la lipsuri grave pentru populație.',
                'importance': 2
            },
            {
                'year': 1989,
                'title': 'Revoluția Română',
                'description': 'În decembrie 1989, revolte populare izbucnesc în Timișoara și se extind în toată țara, ' +
                              'ducând la căderea regimului comunist după 45 de ani.',
                'importance': 3
            },
            {
                'year': 1989,
                'title': 'Execuția soților Ceaușescu',
                'description': 'În ziua de Crăciun, 25 decembrie 1989, Nicolae și Elena Ceaușescu sunt executați ' +
                              'după un proces sumar, marcând sfârșitul oficial al regimului comunist în România.',
                'importance': 3
            },
            {
                'year': 1989,
                'title': 'Formarea Consiliului Frontului Salvării Naționale',
                'description': 'CFSN, condus de Ion Iliescu, preia puterea în mod provizoriu și promite ' +
                              'organizarea primelor alegeri libere din România post-comunistă.',
                'importance': 3
            },
            {
                'year': 1990,
                'title': 'Manifestațiile din Piața Universității',
                'description': 'Protestele împotriva noii conduceri formate din foști comuniști, ' + 
                              'care au culminat cu "Fenomenul Piața Universității", o manifestație antiguvernamentală ' +
                              'care a durat 52 de zile înainte de alegerile din mai 1990.',
                'importance': 2
            }
        ]

        for event_data in transition_events:
            event, created = HistoricalEvent.objects.get_or_create(
                year=event_data['year'],
                title=event_data['title'],
                defaults={
                    'description': event_data['description'],
                    'importance': event_data['importance']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Evenimentul "{event_data["title"]}" a fost creat.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Evenimentul "{event_data["title"]}" există deja.'))

        # Adăugăm controversele legate de tranziția post-comunistă
        transition_controversies = [
            {
                'title': 'Procesul și execuția soților Ceaușescu',
                'description': 'Procesul sumar și execuția rapidă a lui Nicolae și Elena Ceaușescu în ziua de Crăciun ' +
                              'a ridicat numeroase întrebări privind legalitatea și legitimitatea acestui act, ' +
                              'fiind considerat de unii un act de justiție revoluționară, iar de alții o execuție politică.',
                'date': date(1989, 12, 25),
                'impact': 'Impact major asupra tranziției democratice, stabilind un precedent controversat ' +
                         'privind modul în care România s-a desprins de trecutul comunist.'
            },
            {
                'title': 'Evenimentele din decembrie 1989',
                'description': 'Natura exactă a evenimentelor din decembrie 1989 rămâne controversată, ' +
                               'cu teorii multiple despre implicarea serviciilor secrete străine, ' +
                               'și întrebări despre cine a tras în demonstranți după fuga lui Ceaușescu.',
                'date': date(1989, 12, 22),
                'impact': 'Impact profund asupra memoriei colective și asupra percepției privind ' +
                         'autenticitatea revoluției române și legitimitatea noilor structuri de putere.'
            },
            {
                'title': 'Venirea minerilor în București (Mineriada din iunie 1990)',
                'description': 'La chemarea președintelui Ion Iliescu, mii de mineri au venit în București ' +
                               'pentru a dispersa violent protestatarii din Piața Universității, ' +
                               'într-un episod care a afectat profund imaginea noii democrații românești.',
                'date': date(1990, 6, 13),
                'candidate_name': 'Ion Iliescu',
                'election_year': 1990,
                'impact': 'Impact major asupra credibilității democratice a primului guvern post-comunist ' +
                         'și a președintelui Ion Iliescu, afectând și relațiile internaționale ale României.'
            },
            {
                'title': 'Continuitatea elitelor comuniste',
                'description': 'Controversa privind prezența masivă a foștilor membri ai nomenclaturii comuniste ' +
                               'în structurile de putere post-revoluționare, eșecul lustrației ' +
                               'și influența continuă a Securității prin ofițerii săi acoperiți.',
                'date': date(1990, 5, 20),
                'election_year': 1990,
                'impact': 'Impact de durată asupra dezvoltării democratice a României, ' +
                         'creând o neîncredere persistentă în clasa politică și instituțiile statului.'
            }
        ]

        for controversy_data in transition_controversies:
            # Extragere candidate_name și election_year dacă există
            candidate_name = controversy_data.pop('candidate_name', None)
            election_year_value = controversy_data.pop('election_year', None)
            
            candidate = None
            election_year = None
            
            if candidate_name:
                candidates = PresidentialCandidate.objects.filter(name=candidate_name)
                if candidates.exists():
                    candidate = candidates.first()
                else:
                    self.stdout.write(self.style.WARNING(f'Candidatul {candidate_name} nu există în baza de date.'))
            
            if election_year_value:
                election_years = ElectionYear.objects.filter(year=election_year_value)
                if election_years.exists():
                    election_year = election_years.first()
                else:
                    self.stdout.write(self.style.WARNING(f'Anul electoral {election_year_value} nu există în baza de date.'))
            
            controversy, created = Controversy.objects.get_or_create(
                title=controversy_data['title'],
                date=controversy_data['date'],
                defaults={
                    'description': controversy_data['description'],
                    'candidate': candidate,
                    'election_year': election_year,
                    'impact': controversy_data.get('impact')
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost creată.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" există deja.'))

        # Adăugăm un candidat special pentru Nicolae Ceaușescu (doar pentru afișare istorică)
        ceausescu_data = {
            'name': 'Nicolae Ceaușescu',
            'party': 'Partidul Comunist Român',
            'birth_date': date(1918, 1, 26),
            'biography': 'Nicolae Ceaușescu a fost liderul comunist al României între 1965 și 1989. ' +
                        'Deși a început cu o anumită deschidere și independență față de Moscova, ' +
                        'regimul său a devenit tot mai autoritar, culminând cu represiunea violentă ' +
                        'a demonstrațiilor din decembrie 1989. A fost executat împreună cu soția sa, ' +
                        'Elena, pe 25 decembrie 1989, după un proces sumar.',
            'political_experience': 'Secretar General al PCR (1965-1989), Președinte al RSR (1974-1989)',
            'education': 'Studii primare, completate cu educație ideologică în URSS',
            'is_current': False
        }
        
        # Verificăm dacă există deja
        if not PresidentialCandidate.objects.filter(name='Nicolae Ceaușescu').exists():
            # Generăm slug manual pentru a asigura consistența
            ceausescu_data['slug'] = slugify(ceausescu_data['name'])
            PresidentialCandidate.objects.create(**ceausescu_data)
            self.stdout.write(self.style.SUCCESS('Nicolae Ceaușescu a fost adăugat ca referință istorică.'))
        else:
            self.stdout.write(self.style.SUCCESS('Nicolae Ceaușescu există deja în baza de date.'))

        self.stdout.write(self.style.SUCCESS('Popularea evenimentelor de tranziție a fost finalizată cu succes!'))