from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date
from presidential_candidates.models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation,
    HistoricalEvent, MediaInfluence, Controversy
)

class Command(BaseCommand):
    help = 'Populează baza de date cu informații despre candidații prezidențiali, istoricul alegerilor și controverse'

    def handle(self, *args, **kwargs):
        self.stdout.write('Începe popularea bazei de date...')
        
        # Folosim o tranzacție pentru a asigura consistența datelor
        with transaction.atomic():
            # Șterge datele existente (opțional)
            self.clear_existing_data()
            
            # Populăm anii electorali
            self.populate_election_years()
            
            # Populăm candidații
            self.populate_candidates()
            
            # Populăm participările la alegeri
            self.populate_participations()
            
            # Populăm evenimente istorice
            self.populate_historical_events()
            
            # Populăm influențele media
            self.populate_media_influences()
            
            # Populăm controversele
            self.populate_controversies()

        self.stdout.write(self.style.SUCCESS('Popularea bazei de date s-a încheiat cu succes!'))

    def clear_existing_data(self):
        """Șterge datele existente din tabele"""
        Controversy.objects.all().delete()
        MediaInfluence.objects.all().delete()
        HistoricalEvent.objects.all().delete()
        ElectionParticipation.objects.all().delete()
        PresidentialCandidate.objects.all().delete()
        ElectionYear.objects.all().delete()
        self.stdout.write('Datele existente au fost șterse.')

    def populate_election_years(self):
        """Populează anii electorali"""
        election_years_data = [
            {
                'year': 2014,
                'description': 'Alegeri prezidențiale marcate de mobilizarea diasporei și victoria surpriză a lui Klaus Iohannis.',
                'turnout_percentage': 64.11,
                'total_voters': 11553152
            },
            {
                'year': 2019,
                'description': 'Alegeri în care Klaus Iohannis a obținut al doilea mandat, învingând-o pe Viorica Dăncilă în turul doi.',
                'turnout_percentage': 54.86,
                'total_voters': 9478151
            },
            {
                'year': 2024,
                'description': 'Alegeri controversate cu implicații majore pentru politica românească, marcate de ascensiunea unor noi actori politici.',
                'turnout_percentage': 52.32,
                'total_voters': 9125000
            },
            {
                'year': 2009,
                'description': 'Alegeri extrem de strânse între Traian Băsescu și Mircea Geoană, decise la o diferență foarte mică de voturi.',
                'turnout_percentage': 58.02,
                'total_voters': 10481568
            },
            {
                'year': 2004,
                'description': 'Alegeri care au marcat sfârșitul guvernării PSD și începutul mandatelor lui Traian Băsescu.',
                'turnout_percentage': 55.21,
                'total_voters': 10794653
            }
        ]
        
        for year_data in election_years_data:
            ElectionYear.objects.create(**year_data)
            
        self.stdout.write(f'Au fost adăugați {len(election_years_data)} ani electorali.')

    def populate_candidates(self):
        """Populează candidații prezidențiali"""
        candidates_data = [
            {
                'name': 'Klaus Iohannis',
                'birth_date': date(1959, 6, 13),
                'party': 'Partidul Național Liberal',
                'photo_url': 'https://example.com/iohannis.jpg',
                'biography': 'Klaus Iohannis este un politician român, care a fost președintele României între 2014 și 2024. '
                             'Anterior a fost profesor de fizică și ulterior primar al Sibiului timp de 14 ani.',
                'political_experience': 'Primar al municipiului Sibiu (2000-2014), Președinte al României (2014-2024)',
                'education': 'Universitatea Babeș-Bolyai, Facultatea de Fizică',
                'is_current': False
            },
            {
                'name': 'Mircea Geoană',
                'birth_date': date(1958, 7, 14),
                'party': 'Independent',
                'photo_url': 'https://example.com/geoana.jpg',
                'biography': 'Mircea Geoană este un diplomat și politician român, care a ocupat funcția de Secretar General Adjunct al NATO. '
                             'A fost președinte al Partidului Social Democrat între 2005 și 2010.',
                'political_experience': 'Ministru de externe (2000-2004), Președinte PSD (2005-2010), Secretar General Adjunct NATO (2019-2024)',
                'education': 'Facultatea de Mecanică din cadrul Politehnicii București, Școala Națională de Studii Politice și Administrative',
                'is_current': False
            },
            {
                'name': 'Elena Lasconi',
                'birth_date': date(1971, 10, 29),
                'party': 'Uniunea Salvați România',
                'photo_url': 'https://example.com/lasconi.jpg',
                'biography': 'Elena Lasconi este o fostă jurnalistă și politician român, care a devenit cunoscută ca primar al orașului Câmpulung. '
                             'După o carieră de peste 25 de ani în televiziune, a intrat în politică în 2020.',
                'political_experience': 'Primar al orașului Câmpulung (2020-prezent), Președinte USR (2023-prezent)',
                'education': 'Universitatea din București, Facultatea de Jurnalism și Științele Comunicării',
                'is_current': True
            },
            {
                'name': 'Traian Băsescu',
                'birth_date': date(1951, 11, 4),
                'party': 'Partidul Democrat/Partidul Democrat Liberal',
                'photo_url': 'https://example.com/basescu.jpg',
                'biography': 'Traian Băsescu este un politician român care a ocupat funcția de președinte al României pentru două mandate, '
                             'între 2004 și 2014. Anterior a fost primar al municipiului București și ministru al transporturilor.',
                'political_experience': 'Ministru al Transporturilor (1991-1992, 1996-2000), Primar al Bucureștiului (2000-2004), Președinte al României (2004-2014)',
                'education': 'Institutul de Marină "Mircea cel Bătrân" din Constanța',
                'is_current': False
            },
            {
                'name': 'Crin Antonescu',
                'birth_date': date(1959, 9, 21),
                'party': 'Alianța Electorală România Înainte (PSD-PNL-UDMR)',
                'photo_url': 'https://example.com/antonescu.jpg',
                'biography': 'Crin Antonescu este un politician român, fost președinte al PNL și fost președinte interimar al României '
                             'după suspendarea lui Traian Băsescu în 2012. S-a retras din politică în 2014, revenind în 2024.',
                'political_experience': 'Ministru al Tineretului și Sportului (1997-2000), Președinte PNL (2009-2014), Președinte interimar al României (iulie-august 2012)',
                'education': 'Universitatea din București, Facultatea de Istorie-Filosofie',
                'is_current': True
            },
            {
                'name': 'George Simion',
                'birth_date': date(1986, 9, 21),
                'party': 'Alianța pentru Unirea Românilor',
                'photo_url': 'https://example.com/simion.jpg',
                'biography': 'George Simion este un politician și activist român, cofondator și președinte al partidului AUR. '
                             'Anterior a fost cunoscut pentru activismul său legat de unirea României cu Republica Moldova.',
                'political_experience': 'Cofondator și președinte AUR (2019-prezent), Deputat (2020-prezent)',
                'education': 'Academia de Studii Economice din București',
                'is_current': True
            },
            {
                'name': 'Victor Ponta',
                'birth_date': date(1972, 9, 20),
                'party': 'Independent (anterior PSD)',
                'photo_url': 'https://example.com/ponta.jpg',
                'biography': 'Victor Ponta este un politician român care a ocupat funcția de prim-ministru între 2012 și 2015. '
                             'A demisionat în urma protestelor generate de tragedia de la Colectiv.',
                'political_experience': 'Prim-ministru al României (2012-2015), Președinte PSD (2010-2015)',
                'education': 'Universitatea din București, Facultatea de Drept',
                'is_current': True
            },
            {
                'name': 'Mircea Diaconu',
                'birth_date': date(1949, 12, 24),
                'party': 'Independent/Alianța Un Om',
                'photo_url': 'https://example.com/diaconu.jpg',
                'biography': 'Mircea Diaconu este un actor și politician român, care a ocupat funcția de europarlamentar. '
                             'A candidat ca independent la alegerile prezidențiale din 2019.',
                'political_experience': 'Senator (2008-2012), Europarlamentar (2014-2019)',
                'education': 'Institutul de Artă Teatrală și Cinematografică',
                'is_current': False
            },
            {
                'name': 'Dan Barna',
                'birth_date': date(1975, 7, 10),
                'party': 'Uniunea Salvați România',
                'photo_url': 'https://example.com/barna.jpg',
                'biography': 'Dan Barna este un politician român, care a fost președinte al USR între 2017 și 2021. '
                             'A candidat la alegerile prezidențiale din 2019, clasându-se pe locul al treilea.',
                'political_experience': 'Președinte USR (2017-2021), Viceprim-ministru (2020-2021)',
                'education': 'Universitatea din București, Facultatea de Drept',
                'is_current': False
            },
            {
                'name': 'Călin Georgescu',
                'birth_date': date(1962, 11, 21),
                'party': 'Independent',
                'photo_url': 'https://example.com/georgescu.jpg',
                'biography': 'Călin Georgescu este un expert în dezvoltare durabilă, care a lucrat pentru Organizația Națiunilor Unite. '
                             'A devenit cunoscut în urma participării la alegerile prezidențiale din 2024.',
                'political_experience': 'Director executiv al Centrului Național pentru Dezvoltare Durabilă (1997-2013)',
                'education': 'Universitatea de Științe Agronomice și Medicină Veterinară din București',
                'is_current': False
            },
            {
                'name': 'Nicolae Ciucă',
                'birth_date': date(1967, 2, 7),
                'party': 'Partidul Național Liberal',
                'photo_url': 'https://example.com/ciuca.jpg',
                'biography': 'Nicolae Ciucă este un militar și politician român, care a ocupat funcția de prim-ministru între 2021 și 2023. '
                             'Anterior a fost șef al Statului Major al Apărării.',
                'political_experience': 'Ministru al Apărării (2019-2021), Prim-ministru al României (2021-2023), Președinte PNL (2022-prezent)',
                'education': 'Academia Forțelor Terestre "Nicolae Bălcescu", Universitatea Națională de Apărare "Carol I"',
                'is_current': False
            },
            {
                'name': 'Kelemen Hunor',
                'birth_date': date(1967, 10, 18),
                'party': 'Uniunea Democrată Maghiară din România',
                'photo_url': 'https://example.com/kelemen.jpg',
                'biography': 'Kelemen Hunor este un politician român de etnie maghiară, care ocupă funcția de președinte al UDMR din 2011. '
                             'A candidat la alegerile prezidențiale din 2009, 2014 și 2019.',
                'political_experience': 'Președinte UDMR (2011-prezent), Ministru al Culturii (2009-2012), Viceprim-ministru (2020-2023)',
                'education': 'Universitatea de Medicină și Farmacie din Târgu Mureș, Facultatea de Arhitectură',
                'is_current': False
            },
            {
                'name': 'Nicușor Dan',
                'birth_date': date(1969, 12, 20),
                'party': 'Independent (anterior USR)',
                'photo_url': 'https://example.com/nicusor.jpg',
                'biography': 'Nicușor Dan este un matematician și politician român, fondator al Uniunii Salvați România și al Asociației Salvați Bucureștiul. '
                             'Din 2020 ocupă funcția de primar general al Bucureștiului.',
                'political_experience': 'Fondator USR (2016), Primar general al Bucureștiului (2020-prezent)',
                'education': 'Universitatea din București, Facultatea de Matematică, École Normale Supérieure (Paris)',
                'is_current': True
            },
            {
                'name': 'Lavinia Șandru',
                'birth_date': date(1975, 7, 23),
                'party': 'Partidul Umanist Social Liberal',
                'photo_url': 'https://example.com/sandru.jpg',
                'biography': 'Lavinia Șandru este o jurnalistă și politician român, care a fost deputat între 2004 și 2008. '
                             'A revenit în politică pentru a candida la alegerile prezidențiale din 2025.',
                'political_experience': 'Deputat (2004-2008), Coordonator de comunicare PUSL',
                'education': 'Academia de Studii Economice din București',
                'is_current': True
            }
        ]
        
        for candidate_data in candidates_data:
            PresidentialCandidate.objects.create(**candidate_data)
            
        self.stdout.write(f'Au fost adăugați {len(candidates_data)} candidați prezidențiali.')

    def populate_participations(self):
        """Populează participările la alegeri"""
        participations_data = [
            # Alegeri 2024
            {
                'candidate_name': 'Călin Georgescu',
                'election_year': 2024,
                'votes_count': 2046419,
                'votes_percentage': 22.95,
                'position': 1,
                'round': 1,
                'campaign_slogan': 'România are nevoie de suveranitate',
                'notable_events': 'A provocat un șoc în primul tur, dar candidatura pentru turul 2 a fost anulată de CCR.'
            },
            {
                'candidate_name': 'Elena Lasconi',
                'election_year': 2024,
                'votes_count': 1772008,
                'votes_percentage': 19.87,
                'position': 2,
                'round': 1,
                'campaign_slogan': 'România merită mai mult',
                'notable_events': 'Prezența puternică în online și surpriza poziției secunde în primul tur.'
            },
            {
                'candidate_name': 'Marcel Ciolacu',
                'election_year': 2024,
                'votes_count': 1472773,
                'votes_percentage': 16.52,
                'position': 3,
                'round': 1,
                'campaign_slogan': 'Împreună pentru România',
                'notable_events': 'Campanie axată pe realizările guvernului și stabilitate.'
            },
            {
                'candidate_name': 'George Simion',
                'election_year': 2024,
                'votes_count': 1372708,
                'votes_percentage': 15.4,
                'position': 4,
                'round': 1,
                'campaign_slogan': 'România pentru români',
                'notable_events': 'Campanie controversată, cu accent naționalist.'
            },
            {
                'candidate_name': 'Nicolae Ciucă',
                'election_year': 2024,
                'votes_count': 728236,
                'votes_percentage': 8.17,
                'position': 5,
                'round': 1,
                'campaign_slogan': 'România sigură și puternică',
                'notable_events': 'Campanie axată pe experiența militară și de guvernare.'
            },
            # Alegeri second round 2024 (anulate)
            {
                'candidate_name': 'Călin Georgescu',
                'election_year': 2024,
                'votes_count': None,
                'votes_percentage': None,
                'position': None,
                'round': 2,
                'campaign_slogan': 'România are nevoie de suveranitate',
                'notable_events': 'Turul 2 anulat de CCR, ducând la repetarea alegerilor în 2025.'
            },
            {
                'candidate_name': 'Elena Lasconi',
                'election_year': 2024,
                'votes_count': None,
                'votes_percentage': None,
                'position': None,
                'round': 2,
                'campaign_slogan': 'România merită mai mult',
                'notable_events': 'Turul 2 anulat de CCR, ducând la repetarea alegerilor în 2025.'
            },
            
            # Alegeri 2019
            {
                'candidate_name': 'Klaus Iohannis',
                'election_year': 2019,
                'votes_count': 3485292,
                'votes_percentage': 37.82,
                'position': 1,
                'round': 1,
                'campaign_slogan': 'Pentru o Românie normală',
                'notable_events': 'Campanie axată pe continuitate și stabilitate.'
            },
            {
                'candidate_name': 'Viorica Dăncilă',
                'election_year': 2019,
                'votes_count': 2051275,
                'votes_percentage': 22.26,
                'position': 2,
                'round': 1,
                'campaign_slogan': 'Fapte, nu vorbe',
                'notable_events': 'Prima femeie care ajunge în turul doi la prezidențiale în România.'
            },
            {
                'candidate_name': 'Dan Barna',
                'election_year': 2019,
                'votes_count': 1384450,
                'votes_percentage': 15.02,
                'position': 3,
                'round': 1,
                'campaign_slogan': 'Un președinte care lucrează pentru tine',
                'notable_events': 'Campanie axată pe reforma statului și pe atragerea tinerilor.'
            },
            {
                'candidate_name': 'Mircea Diaconu',
                'election_year': 2019,
                'votes_count': 815201,
                'votes_percentage': 8.85,
                'position': 4,
                'round': 1,
                'campaign_slogan': 'Un om',
                'notable_events': 'Candidat independent susținut de o alianță'
            },
            {
                'candidate_name': 'Kelemen Hunor',
                'election_year': 2019,
                'votes_count': 357014,
                'votes_percentage': 3.87,
                'position': 6,
                'round': 1,
                'campaign_slogan': 'Respect pentru toți',
                'notable_events': 'Campanie axată pe drepturile minorităților și dialog.'
            },
            # Turul 2 2019
            {
                'candidate_name': 'Klaus Iohannis',
                'election_year': 2019,
                'votes_count': 6509135,
                'votes_percentage': 66.09,
                'position': 1,
                'round': 2,
                'campaign_slogan': 'Pentru o Românie normală',
                'notable_events': 'Victorie categorică în turul doi, cu cel mai mare număr de voturi din 1990.'
            },
            {
                'candidate_name': 'Viorica Dăncilă',
                'election_year': 2019,
                'votes_count': 3339922,
                'votes_percentage': 33.91,
                'position': 2,
                'round': 2,
                'campaign_slogan': 'Fapte, nu vorbe',
                'notable_events': 'Cel mai slab scor pentru PSD într-un tur doi de prezidențiale.'
            },
            
            # Alegeri 2014
            {
                'candidate_name': 'Victor Ponta',
                'election_year': 2014,
                'votes_count': 3836093,
                'votes_percentage': 40.44,
                'position': 1,
                'round': 1,
                'campaign_slogan': 'Președintele care unește',
                'notable_events': 'Campanie axată pe patriotism și unitate națională.'
            },
            {
                'candidate_name': 'Klaus Iohannis',
                'election_year': 2014,
                'votes_count': 2881406,
                'votes_percentage': 30.37,
                'position': 2,
                'round': 1,
                'campaign_slogan': 'România lucrului bine făcut',
                'notable_events': 'Utilizarea intensivă a rețelelor sociale și mobilizarea diasporei.'
            },
            {
                'candidate_name': 'Kelemen Hunor',
                'election_year': 2014,
                'votes_count': 329727,
                'votes_percentage': 3.47,
                'position': 6,
                'round': 1,
                'campaign_slogan': 'Președinte pentru toți',
                'notable_events': 'Campanie axată pe drepturile minorităților.'
            },
            # Turul 2 2014
            {
                'candidate_name': 'Klaus Iohannis',
                'election_year': 2014,
                'votes_count': 6288769,
                'votes_percentage': 54.43,
                'position': 1,
                'round': 2,
                'campaign_slogan': 'România lucrului bine făcut',
                'notable_events': 'Răsturnare de situație față de turul 1, victoria surprinzătoare a lui Iohannis.'
            },
            {
                'candidate_name': 'Victor Ponta',
                'election_year': 2014,
                'votes_count': 5264383,
                'votes_percentage': 45.56,
                'position': 2,
                'round': 2,
                'campaign_slogan': 'Președintele care unește',
                'notable_events': 'Pierde în ciuda avantajului din primul tur, scandal cu votul diasporei.'
            },
            
            # Alegeri 2009
            {
                'candidate_name': 'Traian Băsescu',
                'election_year': 2009,
                'votes_count': 3153640,
                'votes_percentage': 32.44,
                'position': 2,
                'round': 1,
                'campaign_slogan': 'Să trăiți bine!',
                'notable_events': 'Campanie în plină criză economică, axată pe reformă.'
            },
            {
                'candidate_name': 'Mircea Geoană',
                'election_year': 2009,
                'votes_count': 3027838,
                'votes_percentage': 31.15,
                'position': 1,
                'round': 1,
                'campaign_slogan': 'Adevăr și dreptate',
                'notable_events': 'Câștigă primul tur cu o diferență mică, susținut de o alianță largă.'
            },
            # Turul 2 2009
            {
                'candidate_name': 'Traian Băsescu',
                'election_year': 2009,
                'votes_count': 5275808,
                'votes_percentage': 50.33,
                'position': 1,
                'round': 2,
                'campaign_slogan': 'Să trăiți bine!',
                'notable_events': 'Victorie la limită, diferență de aproximativ 70.000 de voturi. Controversa vizitei la Vântu.'
            },
            {
                'candidate_name': 'Mircea Geoană',
                'election_year': 2009,
                'votes_count': 5205760,
                'votes_percentage': 49.66,
                'position': 2,
                'round': 2,
                'campaign_slogan': 'Adevăr și dreptate',
                'notable_events': 'Pierde în ciuda declarării ca învingător în seara alegerilor pe baza exit-poll-urilor.'
            }
        ]
        
        for participation_data in participations_data:
            # Extragem numele candidatului și anul electoral
            candidate_name = participation_data.pop('candidate_name')
            election_year_value = participation_data.pop('election_year')
            
            # Găsim candidatul și anul electoral în baza de date
            try:
                candidate = PresidentialCandidate.objects.get(name=candidate_name)
                election_year = ElectionYear.objects.get(year=election_year_value)
                
                # Creăm participarea
                ElectionParticipation.objects.create(
                    candidate=candidate,
                    election_year=election_year,
                    **participation_data
                )
            except PresidentialCandidate.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Candidatul {candidate_name} nu există în baza de date.'))
            except ElectionYear.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Anul electoral {election_year_value} nu există în baza de date.'))
        
        self.stdout.write(f'Au fost adăugate {len(participations_data)} participări la alegeri.')

    def populate_historical_events(self):
        """Populează evenimente istorice legate de alegerile prezidențiale"""
        historical_events_data = [
            {
                'year': 1990,
                'title': 'Primele alegeri prezidențiale din România post-comunistă',
                'description': 'Pe 20 mai 1990, România a organizat primele alegeri libere după căderea regimului comunist. '
                               'Ion Iliescu a câștigat detașat cu 85% din voturi.',
                'importance': 3
            },
            {
                'year': 1996,
                'title': 'Prima alternanță democratică la putere',
                'description': 'Emil Constantinescu devine președinte, învingându-l pe Ion Iliescu. '
                               'Este prima dată când puterea se transferă pașnic între partide politice rivale.',
                'importance': 3
            },
            {
                'year': 2004,
                'title': 'Traian Băsescu câștigă primul mandat',
                'description': 'După o campanie intensă, Traian Băsescu îl învinge pe Adrian Năstase în turul doi cu 51,23% din voturi, '
                               'într-un scrutin considerat un punct de cotitură pentru democrația românească.',
                'importance': 2
            },
            {
                'year': 2009,
                'title': 'Cea mai strânsă victorie din istoria alegerilor prezidențiale',
                'description': 'Traian Băsescu îl învinge pe Mircea Geoană cu doar 70.000 de voturi diferență (50,33% vs 49,66%). '
                               'Controversa întâlnirii lui Geoană cu Sorin Ovidiu Vântu în seara dinaintea turului doi a influențat rezultatul.',
                'importance': 3
            },
            {
                'year': 2014,
                'title': 'Scandalul votului din diaspora',
                'description': 'Românii din străinătate au stat la cozi de multe ore pentru a vota, mulți nereușind să își exercite dreptul. '
                               'Situația a generat proteste și a contribuit la înfrângerea lui Victor Ponta.',
                'importance': 3
            },
            {
                'year': 2014,
                'title': 'Răsturnarea situației între turul 1 și turul 2',
                'description': 'Klaus Iohannis recuperează un deficit de 10 procente din primul tur și câștigă detașat turul doi '
                               'cu 54,43%, într-una din cele mai spectaculoase răsturnări de situație din istoria alegerilor.',
                'importance': 3
            },
            {
                'year': 2019,
                'title': 'Prima femeie în turul doi al alegerilor prezidențiale',
                'description': 'Viorica Dăncilă devine prima femeie care ajunge în turul doi al alegerilor prezidențiale din România, '
                               'deși pierde detașat în fața lui Klaus Iohannis.',
                'importance': 2
            },
            {
                'year': 2024,
                'title': 'Anularea turului doi de către CCR',
                'description': 'Curtea Constituțională anulează turul doi al alegerilor din 2024, invocând nereguli procedurale și '
                               'probleme legate de candidatura lui Călin Georgescu, declanșând o criză politică.',
                'importance': 3
            },
            {
                'year': 2025,
                'title': 'Alegeri prezidențiale anticipate',
                'description': 'Pentru prima dată în istoria României post-comuniste se organizează alegeri prezidențiale '
                               'anticipate, în urma anulării turului doi din 2024.',
                'importance': 3
            }
        ]
        
        for event_data in historical_events_data:
            HistoricalEvent.objects.create(**event_data)
            
        self.stdout.write(f'Au fost adăugate {len(historical_events_data)} evenimente istorice.')

    def populate_media_influences(self):
        """Populează influențele media asupra alegerilor"""
        media_influences_data = [
            {
                'title': 'Rolul Facebook în alegerile din 2014',
                'description': 'Facebook a jucat un rol crucial în mobilizarea alegătorilor pentru Klaus Iohannis, '
                               'în special în rândul tinerilor și al diasporei. Campania de pe rețelele sociale a fost '
                               'mult mai eficientă decât abordarea tradițională a lui Victor Ponta.',
                'election_year_value': 2014,
                'media_type': 'social',
                'impact_level': 3
            },
            {
                'title': 'Dezbateri televizate 2009',
                'description': 'Ultima dezbatere televizată dintre Băsescu și Geoană a influențat decisiv rezultatul. '
                               'Momentul în care Băsescu l-a întrebat pe Geoană despre vizita la Vântu a devenit iconic.',
                'election_year_value': 2009,
                'media_type': 'traditional',
                'impact_level': 3
            },
            {
                'title': 'Televiziunile de știri și polarizarea din 2019',
                'description': 'Canalele de știri au fost puternic polarizate în timpul campaniei din 2019, '
                               'contribuind la divizarea societății între susținătorii și criticii PSD.',
                'election_year_value': 2019,
                'media_type': 'traditional',
                'impact_level': 2
            },
            {
                'title': 'Ascensiunea TikTok în campania din 2024',
                'description': 'TikTok a devenit o platformă esențială pentru comunicarea politică, în special pentru '
                               'candidații care au vizat electoratul tânăr. Videoclipurile scurte și autentice au generat '
                               'milioane de vizualizări.',
                'election_year_value': 2024,
                'media_type': 'social',
                'impact_level': 3
            },
            {
                'title': 'Dezinformarea pe WhatsApp în 2019',
                'description': 'Campanii de dezinformare distribuite prin grupuri de WhatsApp au influențat '
                               'percepția alegătorilor, în special în rândul persoanelor în vârstă.',
                'election_year_value': 2019,
                'media_type': 'social',
                'impact_level': 2
            },
            {
                'title': 'Blogurile politice în 2014',
                'description': 'Bloggerii politici au jucat un rol important în formarea opiniei publice '
                               'în timpul campaniei din 2014, mulți poziționându-se împotriva PSD.',
                'election_year_value': 2014,
                'media_type': 'online',
                'impact_level': 2
            },
            {
                'title': 'Podcasturile politice în 2024',
                'description': 'Podcasturile au devenit o platformă esențială pentru discuții politice de substanță, '
                               'cu majoritatea candidaților participând la interviuri lungi și aprofundate.',
                'election_year_value': 2024,
                'media_type': 'online',
                'impact_level': 2
            },
            {
                'title': 'Transmisii live și transparența votului din diaspora în 2024',
                'description': 'Transmisiile live de la secțiile de votare din diaspora au asigurat transparența '
                               'procesului electoral și au descurajat potențialele nereguli.',
                'election_year_value': 2024,
                'media_type': 'social',
                'impact_level': 2
            },
            {
                'title': 'Deepfakes și manipulare AI în 2024',
                'description': 'Pentru prima dată în România, conținutul generat de inteligența artificială (deepfakes) '
                               'a fost folosit pentru a manipula opinia publică, creând confuzie și dezinformare.',
                'election_year_value': 2024,
                'media_type': 'online',
                'impact_level': 3
            }
        ]
        
        for influence_data in media_influences_data:
            # Extragem anul electoral
            election_year_value = influence_data.pop('election_year_value')
            
            # Găsim anul electoral în baza de date
            try:
                election_year = ElectionYear.objects.get(year=election_year_value)
                
                # Creăm influența media
                MediaInfluence.objects.create(
                    election_year=election_year,
                    **influence_data
                )
            except ElectionYear.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Anul electoral {election_year_value} nu există în baza de date.'))
        
        self.stdout.write(f'Au fost adăugate {len(media_influences_data)} influențe media.')

    def populate_controversies(self):
        """Populează controversele legate de alegeri și candidați"""
        controversies_data = [
            {
                'title': 'Cartea lui Klaus Iohannis și acuzațiile de plagiat',
                'description': 'În timpul campaniei din 2014, au apărut acuzații că Klaus Iohannis ar fi plagiat '
                               'în cartea sa "Pas cu pas". Controversa a fost rapid estompată după verificări.',
                'date': date(2014, 10, 18),
                'candidate_name': 'Klaus Iohannis',
                'election_year_value': 2014,
                'impact': 'Impact redus asupra campaniei, acuzațiile fiind respinse de majoritatea analiștilor.'
            },
            {
                'title': 'Vizita lui Mircea Geoană la Sorin Ovidiu Vântu',
                'description': 'Cu o seară înainte de turul doi al alegerilor din 2009, Mircea Geoană l-a vizitat '
                               'pe omul de afaceri controversat Sorin Ovidiu Vântu. Această vizită a fost dezvăluită '
                               'de Traian Băsescu în timpul ultimei dezbateri televizate.',
                'date': date(2009, 12, 5),
                'candidate_name': 'Mircea Geoană',
                'election_year_value': 2009,
                'impact': 'Impact major, considerat unul din factorii decisivi care au dus la înfrângerea lui Geoană.'
            },
            {
                'title': 'Declarația lui Traian Băsescu despre lovitura aplicată unui copil',
                'description': 'În timpul campaniei din 2004, a apărut un videoclip în care Traian Băsescu părea să lovească '
                               'un copil într-o emisiune TV din 2004. Băsescu a negat incidentul, dar imaginile au fost intens dezbătute.',
                'date': date(2004, 11, 20),
                'candidate_name': 'Traian Băsescu',
                'election_year_value': 2004,
                'impact': 'Impact moderat, dar insuficient pentru a-i afecta victoria în alegeri.'
            },
            {
                'title': 'Scandalul imobilelor deținute de Klaus Iohannis',
                'description': 'În timpul campaniei din 2014, s-au intensificat acuzațiile legate de modul în care '
                               'Klaus Iohannis a intrat în posesia unor imobile în Sibiu. Acesta a fost acuzat de falsificare de documente.',
                'date': date(2014, 10, 30),
                'candidate_name': 'Klaus Iohannis',
                'election_year_value': 2014,
                'impact': 'Impact moderat, contrabalansat de percepția negativă despre adversarul său, Victor Ponta.'
            },
            {
                'title': 'Plagiatul tezei de doctorat a lui Victor Ponta',
                'description': 'În 2012, au apărut acuzații că Victor Ponta și-ar fi plagiat teza de doctorat. Scandalul a continuat '
                               'până în campania prezidențială din 2014, afectând credibilitatea candidatului PSD.',
                'date': date(2012, 6, 18),
                'candidate_name': 'Victor Ponta',
                'election_year_value': 2014,
                'impact': 'Impact semnificativ, contribuind la imaginea negativă a candidatului în rândul alegătorilor educați.'
            },
            {
                'title': 'Blocarea votului din diaspora în 2014',
                'description': 'În timpul primului tur al alegerilor din 2014, mii de români din diaspora nu au putut vota '
                               'din cauza organizării defectuoase. Situația a generat proteste și a fost atribuită guvernului condus de Victor Ponta.',
                'date': date(2014, 11, 2),
                'candidate_name': 'Victor Ponta',
                'election_year_value': 2014,
                'impact': 'Impact major, contribuind decisiv la mobilizarea anti-PSD în turul doi și la înfrângerea lui Ponta.'
            },
            {
                'title': 'Retragerea lui Dan Diaconescu din cursa prezidențială din 2014',
                'description': 'Dan Diaconescu, fondatorul PP-DD, a fost condamnat penal în 2015, după ce obținuse un '
                               'scor bun la alegerile prezidențiale din 2014. Mulți alegători au considerat că a fost o acțiune politică.',
                'date': date(2015, 3, 4),
                'election_year_value': 2014,
                'impact': 'Impact limitat asupra rezultatelor, dar a contribuit la percepția de justiție selectivă.'
            },
            {
                'title': 'Orientarea religioasă a lui Elena Lasconi',
                'description': 'În timpul campaniei din 2024, Elena Lasconi a stârnit controverse după ce a declarat '
                               'că a votat "Da" la referendumul pentru familie din 2018, generând tensiuni în interiorul USR.',
                'date': date(2024, 10, 15),
                'candidate_name': 'Elena Lasconi',
                'election_year_value': 2024,
                'impact': 'Impact moderat, provocând diviziuni în interiorul propriului partid, dar potențial pozitiv pentru alegătorii conservatori.'
            },
            {
                'title': 'Controversele legate de trecutul lui Călin Georgescu',
                'description': 'După succesul surprinzător din primul tur din 2024, au apărut numeroase controverse '
                               'legate de declarațiile anterioare ale lui Călin Georgescu despre personalități controversate ale istoriei.',
                'date': date(2024, 11, 25),
                'candidate_name': 'Călin Georgescu',
                'election_year_value': 2024,
                'impact': 'Impact major, ducând la anularea candidaturii pentru turul doi de către CCR.'
            }
        ]
        
        for controversy_data in controversies_data:
            # Extragem numele candidatului și anul electoral
            candidate_name = controversy_data.pop('candidate_name', None)
            election_year_value = controversy_data.pop('election_year_value', None)
            
            # Găsim candidatul și anul electoral în baza de date
            candidate = None
            election_year = None
            
            if candidate_name:
                try:
                    candidate = PresidentialCandidate.objects.get(name=candidate_name)
                except PresidentialCandidate.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Candidatul {candidate_name} nu există în baza de date.'))

            if election_year_value:
                try:
                    election_year = ElectionYear.objects.get(year=election_year_value)
                except ElectionYear.DoesNotExist:
                     self.stdout.write(self.style.WARNING(f'Anul electoral {election_year_value} nu există în baza de date.'))


            # Creăm controversele
            Controversy.objects.create(
                candidate=candidate,
                election_year=election_year,
                **controversy_data
            )
        self.stdout.write(f'Au fost adăugate {len(controversies_data)} controverse.')
         