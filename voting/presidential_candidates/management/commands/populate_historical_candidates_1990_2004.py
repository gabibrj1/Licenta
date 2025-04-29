from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date, datetime
from presidential_candidates.models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation, 
    HistoricalEvent, MediaInfluence, Controversy
)

class Command(BaseCommand):
    help = 'Populează baza de date cu candidați istorici din perioada 1990-2004'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Începe popularea candidaților istorici din perioada 1990-2004...'))

        # Verificăm existența anilor electorali
        election_years = [1990, 1992, 1996, 2000, 2004]
        for year in election_years:
            if not ElectionYear.objects.filter(year=year).exists():
                self.stdout.write(self.style.WARNING(f'Anul electoral {year} nu există în baza de date. Vă rugăm să rulați mai întâi scriptul de populare a anilor electorali.'))
                return

        # Candidați 2004
        candidates_2004 = [
            {
                'name': 'Traian Băsescu',
                'party': 'Alianța D.A. (PNL-PD)',
                'birth_date': date(1951, 11, 4),
                'biography': 'Traian Băsescu a fost primar al Bucureștiului între 2000-2004. În 2004 a candidat pentru funcția de președinte al României din partea Alianței Dreptate și Adevăr.',
                'political_experience': 'Ministru al Transporturilor (1991-1992, 1996-2000), Primar al Bucureștiului (2000-2004)',
                'education': 'Institutul de Marină din Constanța',
                'photo_url': 'https://example.com/traian_basescu_2004.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2004,
                        'votes_count': 5126794,
                        'votes_percentage': 51.23,
                        'position': 1,
                        'round': 2,
                        'campaign_slogan': 'Să trăiți bine!',
                    },
                    {
                        'year': 2004,
                        'votes_count': 3545236,
                        'votes_percentage': 33.92,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'Să trăiți bine!',
                    }
                ]
            },
            {
                'name': 'Adrian Năstase',
                'party': 'PSD',
                'birth_date': date(1950, 6, 22),
                'biography': 'Adrian Năstase a fost prim-ministru al României între 2000-2004. A candidat la alegerile prezidențiale din 2004, unde a ajuns în turul al doilea.',
                'political_experience': 'Ministru de Externe (1990-1992), Președinte al Camerei Deputaților (1992-1996), Prim-ministru (2000-2004)',
                'education': 'Facultatea de Drept a Universității din București',
                'photo_url': 'https://example.com/adrian_nastase.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2004,
                        'votes_count': 4881520,
                        'votes_percentage': 48.77,
                        'position': 2,
                        'round': 2,
                        'campaign_slogan': 'Faptele sunt politica mea',
                    },
                    {
                        'year': 2004,
                        'votes_count': 4278864,
                        'votes_percentage': 40.94,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Faptele sunt politica mea',
                    }
                ]
            },
            {
                'name': 'Corneliu Vadim Tudor',
                'party': 'PRM',
                'birth_date': date(1949, 11, 28),
                'biography': 'Corneliu Vadim Tudor a fost poet, publicist și politician român. A fondat Partidul România Mare și a candidat la alegerile prezidențiale din 2000 și 2004.',
                'political_experience': 'Senator (1992-2008), Europarlamentar (2009-2014)',
                'education': 'Facultatea de Filosofie a Universității din București',
                'photo_url': 'https://example.com/corneliu_vadim_tudor.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2004,
                        'votes_count': 1313714,
                        'votes_percentage': 12.57,
                        'position': 3,
                        'round': 1,
                        'campaign_slogan': 'Sus Patria, jos trădarea!',
                    }
                ]
            }
        ]

        # Candidați 2000
        candidates_2000 = [
            {
                'name': 'Ion Iliescu',
                'party': 'PDSR',
                'birth_date': date(1930, 3, 3),
                'biography': 'Ion Iliescu a fost primul președinte al României post-comuniste (1990-1996, 2000-2004). În 2000 a candidat pentru un nou mandat.',
                'political_experience': 'Președinte al României (1990-1996), Președinte PDSR/PSD',
                'education': 'Institutul de Energie din Moscova',
                'photo_url': 'https://example.com/ion_iliescu.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2000,
                        'votes_count': 6696623,
                        'votes_percentage': 66.83,
                        'position': 1,
                        'round': 2,
                        'campaign_slogan': 'Un președinte pentru toți românii',
                    },
                    {
                        'year': 2000,
                        'votes_count': 4076273,
                        'votes_percentage': 36.35,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Un președinte pentru toți românii',
                    }
                ]
            },
            {
                'name': 'Corneliu Vadim Tudor',
                'party': 'PRM',
                'birth_date': date(1949, 11, 28),
                'biography': 'Corneliu Vadim Tudor a fost poet, publicist și politician român. A fondat Partidul România Mare și a candidat la alegerile prezidențiale din 2000, ajungând în turul doi.',
                'political_experience': 'Senator (1992-2008)',
                'education': 'Facultatea de Filosofie a Universității din București',
                'photo_url': 'https://example.com/corneliu_vadim_tudor_2000.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2000,
                        'votes_count': 3324247,
                        'votes_percentage': 33.17,
                        'position': 2,
                        'round': 2,
                        'campaign_slogan': 'Să ne unim cu cei care nu fură!',
                    },
                    {
                        'year': 2000,
                        'votes_count': 3178293,
                        'votes_percentage': 28.34,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'Să ne unim cu cei care nu fură!',
                    }
                ]
            },
            {
                'name': 'Theodor Stolojan',
                'party': 'PNL',
                'birth_date': date(1943, 10, 24),
                'biography': 'Theodor Stolojan a fost prim-ministru al României între septembrie 1991 și noiembrie 1992. A candidat la alegerile prezidențiale din 2000.',
                'political_experience': 'Prim-ministru (1991-1992), Deputat (1996-2000, 2004-2007), Europarlamentar (2007-2019)',
                'education': 'Academia de Studii Economice din București',
                'photo_url': 'https://example.com/theodor_stolojan.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2000,
                        'votes_count': 1321420,
                        'votes_percentage': 11.78,
                        'position': 3,
                        'round': 1,
                        'campaign_slogan': 'Să trăim mai bine!',
                    }
                ]
            }
        ]

        # Candidați 1996
        candidates_1996 = [
            {
                'name': 'Emil Constantinescu',
                'party': 'CDR',
                'birth_date': date(1939, 11, 19),
                'biography': 'Emil Constantinescu a fost președintele României între 1996 și 2000. A candidat din partea Convenției Democrate Române, învingându-l pe Ion Iliescu.',
                'political_experience': 'Rector al Universității din București (1992-1996), Președinte al României (1996-2000)',
                'education': 'Facultatea de Drept și Facultatea de Geologie-Geografie, Universitatea din București',
                'photo_url': 'https://example.com/emil_constantinescu.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1996,
                        'votes_count': 7057906,
                        'votes_percentage': 54.41,
                        'position': 1,
                        'round': 2,
                        'campaign_slogan': 'Acum sau niciodată!',
                    },
                    {
                        'year': 1996,
                        'votes_count': 3569941,
                        'votes_percentage': 28.21,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'Acum sau niciodată!',
                    }
                ]
            },
            {
                'name': 'Ion Iliescu',
                'party': 'PDSR',
                'birth_date': date(1930, 3, 3),
                'biography': 'Ion Iliescu a fost președintele României între 1990-1996. În 1996 a candidat pentru un nou mandat, fiind învins de Emil Constantinescu.',
                'political_experience': 'Președinte al României (1990-1996), Președinte PDSR',
                'education': 'Institutul de Energie din Moscova',
                'photo_url': 'https://example.com/ion_iliescu_1996.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1996,
                        'votes_count': 5914579,
                        'votes_percentage': 45.59,
                        'position': 2,
                        'round': 2,
                        'campaign_slogan': 'Liniște și stabilitate',
                    },
                    {
                        'year': 1996,
                        'votes_count': 4081093,
                        'votes_percentage': 32.25,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Liniște și stabilitate',
                    }
                ]
            },
            {
                'name': 'Petre Roman',
                'party': 'USD',
                'birth_date': date(1946, 7, 22),
                'biography': 'Petre Roman a fost primul prim-ministru post-comunist al României (1989-1991). A candidat la alegerile prezidențiale din 1996 din partea Uniunii Social Democrate.',
                'political_experience': 'Prim-ministru (1989-1991), Președinte al Senatului (1996-2000), Ministru de Externe (1999-2000)',
                'education': 'Institutul Politehnic București, Universitatea din Toulouse',
                'photo_url': 'https://example.com/petre_roman.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1996,
                        'votes_count': 2598545,
                        'votes_percentage': 20.54,
                        'position': 3,
                        'round': 1,
                        'campaign_slogan': 'Schimbarea în bine',
                    }
                ]
            }
        ]

        # Candidați 1992
        candidates_1992 = [
            {
                'name': 'Ion Iliescu',
                'party': 'FDSN',
                'birth_date': date(1930, 3, 3),
                'biography': 'Ion Iliescu a fost președintele României între 1990-1992. În 1992 a candidat pentru un nou mandat din partea Frontului Democrat al Salvării Naționale.',
                'political_experience': 'Președinte al României (1990-1992), Președinte FDSN',
                'education': 'Institutul de Energie din Moscova',
                'photo_url': 'https://example.com/ion_iliescu_1992.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1992,
                        'votes_count': 7393429,
                        'votes_percentage': 61.43,
                        'position': 1,
                        'round': 2,
                        'campaign_slogan': 'Liniște și stabilitate',
                    },
                    {
                        'year': 1992,
                        'votes_count': 5633465,
                        'votes_percentage': 47.34,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Liniște și stabilitate',
                    }
                ]
            },
            {
                'name': 'Emil Constantinescu',
                'party': 'CDR',
                'birth_date': date(1939, 11, 19),
                'biography': 'Emil Constantinescu a fost profesor universitar și rector al Universității din București. În 1992 a candidat din partea Convenției Democrate Române.',
                'political_experience': 'Rector al Universității din București (1992-1996)',
                'education': 'Facultatea de Drept și Facultatea de Geologie-Geografie, Universitatea din București',
                'photo_url': 'https://example.com/emil_constantinescu_1992.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1992,
                        'votes_count': 4641207,
                        'votes_percentage': 38.57,
                        'position': 2,
                        'round': 2,
                        'campaign_slogan': 'Schimbarea adevărată',
                    },
                    {
                        'year': 1992,
                        'votes_count': 3717006,
                        'votes_percentage': 31.24,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'Schimbarea adevărată',
                    }
                ]
            },
            {
                'name': 'Gheorghe Funar',
                'party': 'PUNR',
                'birth_date': date(1949, 9, 29),
                'biography': 'Gheorghe Funar a fost primarul municipiului Cluj-Napoca între 1992-2004. A candidat la alegerile prezidențiale din 1992 din partea Partidului Unității Naționale Române.',
                'political_experience': 'Primar al Cluj-Napoca (1992-2004), Senator (2004-2008)',
                'education': 'Facultatea de Științe Economice din Cluj',
                'photo_url': 'https://example.com/gheorghe_funar.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1992,
                        'votes_count': 1294388,
                        'votes_percentage': 10.88,
                        'position': 3,
                        'round': 1,
                        'campaign_slogan': 'România pentru români',
                    }
                ]
            }
        ]

        # Candidați 1990
        candidates_1990 = [
            {
                'name': 'Ion Iliescu',
                'party': 'FSN',
                'birth_date': date(1930, 3, 3),
                'biography': 'Ion Iliescu a fost lider al Revoluției Române din 1989 și președinte provizoriu al României până la alegerile din mai 1990. A candidat din partea Frontului Salvării Naționale.',
                'political_experience': 'Președinte provizoriu al României (1989-1990), Președinte FSN',
                'education': 'Institutul de Energie din Moscova',
                'photo_url': 'https://example.com/ion_iliescu_1990.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1990,
                        'votes_count': 12232498,
                        'votes_percentage': 85.07,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Pentru libertate și democrație',
                    }
                ]
            },
            {
                'name': 'Radu Câmpeanu',
                'party': 'PNL',
                'birth_date': date(1922, 2, 28),
                'biography': 'Radu Câmpeanu a fost un politician liberal român, întors din exil după Revoluția din 1989. A candidat la alegerile prezidențiale din 1990 din partea Partidului Național Liberal.',
                'political_experience': 'Președinte PNL (1990-1991), Senator (1990-1992)',
                'education': 'Facultatea de Drept, Universitatea din București',
                'photo_url': 'https://example.com/radu_campeanu.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1990,
                        'votes_count': 1529188,
                        'votes_percentage': 10.64,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'Prin noi înșine',
                    }
                ]
            },
            {
                'name': 'Ion Rațiu',
                'party': 'PNTCD',
                'birth_date': date(1917, 6, 6),
                'biography': 'Ion Rațiu a fost un politician și om de afaceri român, întors din exil după Revoluția din 1989. A candidat la alegerile prezidențiale din 1990 din partea Partidului Național Țărănesc Creștin Democrat.',
                'political_experience': 'Deputat (1990-1992, 1992-1996)',
                'education': 'Academia de Înalte Studii Comerciale și Industriale din Cluj, Facultatea de Drept din București',
                'photo_url': 'https://example.com/ion_ratiu.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 1990,
                        'votes_count': 617007,
                        'votes_percentage': 4.29,
                        'position': 3,
                        'round': 1,
                        'campaign_slogan': 'Voi lupta până la ultima mea picătură de sânge ca să ai dreptul să nu fii de acord cu mine!',
                    }
                ]
            }
        ]

        # Adaugă toți candidații din toate listele
        all_candidates = candidates_2004 + candidates_2000 + candidates_1996 + candidates_1992 + candidates_1990
        
        for candidate_data in all_candidates:
            # Extragem participările înainte de a crea candidatul
            participations_data = candidate_data.pop('participations', [])
            
            # Verificăm dacă candidatul există deja după nume
            candidate, created = PresidentialCandidate.objects.get_or_create(
                name=candidate_data['name'],
                defaults=candidate_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate.name} a fost creat.'))
            else:
                # Actualizăm candidatul dacă există deja
                for key, value in candidate_data.items():
                    setattr(candidate, key, value)
                candidate.save()
                self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate.name} a fost actualizat.'))
            
            # Adăugăm participările pentru acest candidat
            for participation_data in participations_data:
                # Găsim anul electoral
                election_year = ElectionYear.objects.get(year=participation_data['year'])
                
                # Verificăm dacă participarea există deja
                participation, created = ElectionParticipation.objects.get_or_create(
                    candidate=candidate,
                    election_year=election_year,
                    round=participation_data['round'],
                    defaults={
                        'votes_count': participation_data.get('votes_count'),
                        'votes_percentage': participation_data.get('votes_percentage'),
                        'position': participation_data.get('position'),
                        'campaign_slogan': participation_data.get('campaign_slogan'),
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Participare adăugată pentru {candidate.name} în anul {election_year.year}, turul {participation.round}.'
                    ))
                else:
                    # Actualizăm participarea dacă există deja
                    for key, value in participation_data.items():
                        if key not in ['year', 'round']:  # Excludem cheia year care nu este în model
                            setattr(participation, key, value)
                    participation.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'Participare actualizată pentru {candidate.name} în anul {election_year.year}, turul {participation.round}.'
                    ))

        # Adăugăm controverse din perioada 1990-2004
        controversies = [
            {
                'title': 'Mineriada din 13-15 iunie 1990',
                'description': 'Controversă legată de implicarea președintelui Ion Iliescu în chemarea minerilor în București pentru a dispersa protestele din Piața Universității.',
                'date': date(1990, 6, 13),
                'candidate_name': 'Ion Iliescu',
                'election_year': 1990,
                'impact': 'Impact major asupra credibilității democrației românești și a președintelui Iliescu pe plan internațional.'
            },
            {
                'title': 'Proclamația de la Timișoara',
                'description': 'Punct 8 al Proclamației de la Timișoara care cerea interzicerea candidaturii foștilor activiști comuniști la funcții publice, vizându-l în principal pe Ion Iliescu.',
                'date': date(1990, 3, 11),
                'candidate_name': 'Ion Iliescu',
                'election_year': 1990,
                'impact': 'Impact semnificativ, deși nu a împiedicat victoria zdrobitoare a lui Iliescu la alegerile din 1990.'
            },
            {
                'title': 'Discursul extremist al lui Corneliu Vadim Tudor',
                'description': 'Discursurile și declarațiile extremiste, xenofobe și antisemite ale lui Corneliu Vadim Tudor în timpul campaniei din 2000.',
                'date': date(2000, 11, 15),
                'candidate_name': 'Corneliu Vadim Tudor',
                'election_year': 2000,
                'impact': 'Deși a stârnit indignare internațională, a permis mobilizarea electoratului anti-Vadim în turul doi, ducând la o victorie zdrobitoare a lui Ion Iliescu.'
            },
            {
                'title': 'Contractul cu Bechtel',
                'description': 'Controversă legată de contractul încheiat de guvernul Năstase cu compania americană Bechtel pentru construcția autostrăzii Transilvania, fără licitație publică.',
                'date': date(2004, 10, 25),
                'candidate_name': 'Adrian Năstase',
                'election_year': 2004,
                'impact': 'Impact semnificativ, contribuind la percepția de corupție a guvernării PSD și a candidatului Adrian Năstase.'
            },
            {
                'title': 'Scandalul privatizărilor din perioada CDR',
                'description': 'Acuzații privind privatizările controversate din perioada guvernării CDR (1996-2000), care au afectat imaginea președintelui Emil Constantinescu.',
                'date': date(2000, 9, 28),
                'candidate_name': 'Emil Constantinescu',
                'election_year': 2000,
                'impact': 'Impact major, președintele Constantinescu renunțând să mai candideze pentru un nou mandat în 2000.'
            }
        ]

        for controversy_data in controversies:
            # Găsim candidatul și anul electoral
            candidate_name = controversy_data.pop('candidate_name', None)
            election_year_value = controversy_data.pop('election_year', None)
            
            candidate = None
            election_year = None
            
            if candidate_name:
                candidates = PresidentialCandidate.objects.filter(name=candidate_name)
                if candidates.exists():
                    candidate = candidates.first()
            
            if election_year_value:
                election_years = ElectionYear.objects.filter(year=election_year_value)
                if election_years.exists():
                    election_year = election_years.first()
            
            Controversy.objects.get_or_create(
                title=controversy_data['title'],
                date=controversy_data['date'],
                defaults={
                    'description': controversy_data['description'],
                    'candidate': candidate,
                    'election_year': election_year,
                    'impact': controversy_data.get('impact')
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost creată.'))

        self.stdout.write(self.style.SUCCESS('Popularea candidaților istorici din perioada 1990-2004 a fost finalizată cu succes!'))