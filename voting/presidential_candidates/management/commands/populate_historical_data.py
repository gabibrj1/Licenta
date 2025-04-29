from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date, datetime
from presidential_candidates.models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation, 
    HistoricalEvent, MediaInfluence, Controversy
)

class Command(BaseCommand):
    help = 'Populează baza de date cu candidați istorici și date electorale'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Începe popularea bazei de date cu date istorice...'))

        # Crearea anilor electorali (dacă nu există deja)
        election_years = [
            # Ani de alegeri prezidențiale în România post-comunistă
            {'year': 1990, 'turnout_percentage': 86.19, 'total_voters': 14389441,
             'description': 'Primele alegeri libere din România post-comunistă.'},
            {'year': 1992, 'turnout_percentage': 73.23, 'total_voters': 12034636,
             'description': 'Alegeri prezidențiale organizate simultan cu cele parlamentare.'},
            {'year': 1996, 'turnout_percentage': 76.01, 'total_voters': 13088388,
             'description': 'Alegeri care au marcat prima alternanță la putere.'},
            {'year': 2000, 'turnout_percentage': 65.31, 'total_voters': 10020870,
             'description': 'Alegeri care au adus în turul al doilea extrema dreaptă.'},
            {'year': 2004, 'turnout_percentage': 55.21, 'total_voters': 10794653,
             'description': 'Alegeri contestate, cu acuzații de fraudă.'},
            {'year': 2009, 'turnout_percentage': 58.02, 'total_voters': 10620116,
             'description': 'Alegeri decise de voturile din diaspora.'},
            {'year': 2014, 'turnout_percentage': 64.11, 'total_voters': 11719344,
             'description': 'Alegeri marcate de probleme la secțiile din străinătate.'},
            {'year': 2019, 'turnout_percentage': 54.86, 'total_voters': 9359673,
             'description': 'Alegeri cu cea mai mare prezență în diaspora.'},
            {'year': 2024, 'turnout_percentage': 51.03, 'total_voters': 9120458,
             'description': 'Alegeri anulate de CCR după primul tur.'}
        ]

        for year_data in election_years:
            ElectionYear.objects.get_or_create(
                year=year_data['year'],
                defaults={
                    'turnout_percentage': year_data['turnout_percentage'],
                    'total_voters': year_data['total_voters'],
                    'description': year_data['description']
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Anul electoral {year_data["year"]} a fost creat.'))

        # Candidați istorici pentru 2019
        candidates_2019 = [
            {
                'name': 'Klaus Iohannis',
                'party': 'PNL',
                'birth_date': date(1959, 6, 13),
                'biography': 'Klaus Werner Iohannis a fost primarul municipiului Sibiu între 2000-2014. A câștigat alegerile prezidențiale din 2014 și a devenit al 5-lea președinte al României. În 2019 a candidat pentru un al doilea mandat.',
                'political_experience': 'Primar al Sibiului (2000-2014), Președinte al României (2014-2024)',
                'education': 'Facultatea de Fizică din cadrul Universității Babeș-Bolyai din Cluj-Napoca',
                'photo_url': 'https://example.com/klaus_iohannis.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2019,
                        'votes_count': 6509135,
                        'votes_percentage': 66.09,
                        'position': 1,
                        'round': 2,
                        'campaign_slogan': 'Pentru România normală',
                    },
                    {
                        'year': 2019,
                        'votes_count': 3485292,
                        'votes_percentage': 37.82,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Pentru România normală',
                    }
                ]
            },
            {
                'name': 'Viorica Dăncilă',
                'party': 'PSD',
                'birth_date': date(1963, 12, 16),
                'biography': 'Viorica Dăncilă a fost prima femeie prim-ministru a României, între ianuarie 2018 și noiembrie 2019. A candidat la alegerile prezidențiale din 2019, unde a ajuns în turul al doilea.',
                'political_experience': 'Europarlamentar (2009-2018), Prim-ministru (2018-2019)',
                'education': 'Facultatea de Foraj Petrol-Gaze din Ploiești',
                'photo_url': 'https://example.com/viorica_dancila.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2019,
                        'votes_count': 3339922,
                        'votes_percentage': 33.91,
                        'position': 2,
                        'round': 2,
                        'campaign_slogan': 'Pentru toți românii',
                    },
                    {
                        'year': 2019,
                        'votes_count': 2051725,
                        'votes_percentage': 22.26,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'Pentru toți românii',
                    }
                ]
            },
            {
                'name': 'Dan Barna',
                'party': 'USR',
                'birth_date': date(1975, 7, 10),
                'biography': 'Dan Barna a fost liderul USR în perioada 2017-2021. A candidat la alegerile prezidențiale din 2019, clasându-se pe locul al treilea.',
                'political_experience': 'Deputat (2016-2024), Co-președinte USR PLUS',
                'education': 'Facultatea de Drept din cadrul Universității din București',
                'photo_url': 'https://example.com/dan_barna.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2019,
                        'votes_count': 1384450,
                        'votes_percentage': 15.02,
                        'position': 3,
                        'round': 1,
                        'campaign_slogan': 'Un președinte pentru România modernă',
                    }
                ]
            },
            {
                'name': 'Mircea Diaconu',
                'party': 'Independent',
                'birth_date': date(1949, 12, 24),
                'biography': 'Mircea Diaconu este un actor și politician român. A fost senator, ministru al culturii și europarlamentar. A candidat ca independent la alegerile prezidențiale din 2019.',
                'political_experience': 'Senator (2008-2012), Europarlamentar (2014-2019)',
                'education': 'Institutul de Artă Teatrală și Cinematografică din București',
                'photo_url': 'https://example.com/mircea_diaconu.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2019,
                        'votes_count': 815201,
                        'votes_percentage': 8.85,
                        'position': 4,
                        'round': 1,
                        'campaign_slogan': 'Un om',
                    }
                ]
            }
        ]

        # Candidați pentru 2014
        candidates_2014 = [
            {
                'name': 'Klaus Iohannis',
                'party': 'ACL (PNL-PDL)',
                'birth_date': date(1959, 6, 13),
                'biography': 'Klaus Werner Iohannis a fost primarul municipiului Sibiu între 2000-2014. În 2014 a candidat pentru funcția de președinte al României din partea Alianței Creștin-Liberale.',
                'political_experience': 'Primar al Sibiului (2000-2014)',
                'education': 'Facultatea de Fizică din cadrul Universității Babeș-Bolyai din Cluj-Napoca',
                'photo_url': 'https://example.com/klaus_iohannis_2014.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2014,
                        'votes_count': 6288769,
                        'votes_percentage': 54.43,
                        'position': 1,
                        'round': 2,
                        'campaign_slogan': 'România lucrului bine făcut',
                    },
                    {
                        'year': 2014,
                        'votes_count': 2881406,
                        'votes_percentage': 30.37,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'România lucrului bine făcut',
                    }
                ]
            },
            {
                'name': 'Victor Ponta',
                'party': 'Alianța PSD-UNPR-PC',
                'birth_date': date(1972, 9, 20),
                'biography': 'Victor Ponta a fost prim-ministru al României între 2012-2015. A candidat la alegerile prezidențiale din 2014, unde a ajuns în turul al doilea.',
                'political_experience': 'Deputat (2004-2020), Prim-ministru (2012-2015)',
                'education': 'Facultatea de Drept a Universității din București',
                'photo_url': 'https://example.com/victor_ponta.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2014,
                        'votes_count': 5264383,
                        'votes_percentage': 45.57,
                        'position': 2,
                        'round': 2,
                        'campaign_slogan': 'Președintele care unește',
                    },
                    {
                        'year': 2014,
                        'votes_count': 3836093,
                        'votes_percentage': 40.44,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Președintele care unește',
                    }
                ]
            }
        ]

        # Candidați pentru 2009
        candidates_2009 = [
            {
                'name': 'Traian Băsescu',
                'party': 'PDL',
                'birth_date': date(1951, 11, 4),
                'biography': 'Traian Băsescu a fost președintele României între 2004-2014. În 2009 a candidat pentru un al doilea mandat.',
                'political_experience': 'Primar al Capitalei (2000-2004), Președinte al României (2004-2014)',
                'education': 'Institutul de Marină din Constanța',
                'photo_url': 'https://example.com/traian_basescu.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2009,
                        'votes_count': 5275808,
                        'votes_percentage': 50.33,
                        'position': 1,
                        'round': 2,
                        'campaign_slogan': 'Să trăiți bine!',
                    },
                    {
                        'year': 2009,
                        'votes_count': 3153640,
                        'votes_percentage': 32.44,
                        'position': 2,
                        'round': 1,
                        'campaign_slogan': 'Să trăiți bine!',
                    }
                ]
            },
            {
                'name': 'Mircea Geoană',
                'party': 'PSD',
                'birth_date': date(1958, 7, 14),
                'biography': 'Mircea Geoană a fost președintele Senatului și președintele PSD. A candidat la alegerile prezidențiale din 2009, unde a ajuns în turul al doilea.',
                'political_experience': 'Ministru de Externe (2000-2004), Președinte al Senatului (2008-2011)',
                'education': 'Facultatea de Mecanică a Institutului Politehnic București',
                'photo_url': 'https://example.com/mircea_geoana.jpg',
                'is_current': False,
                'participations': [
                    {
                        'year': 2009,
                        'votes_count': 5205760,
                        'votes_percentage': 49.67,
                        'position': 2,
                        'round': 2,
                        'campaign_slogan': 'Primul președinte care unește',
                    },
                    {
                        'year': 2009,
                        'votes_count': 3027838,
                        'votes_percentage': 31.15,
                        'position': 1,
                        'round': 1,
                        'campaign_slogan': 'Primul președinte care unește',
                    }
                ]
            }
        ]

        # Adaugă toți candidații din toate listele
        all_candidates = candidates_2019 + candidates_2014 + candidates_2009
        
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

        # Adăugăm evenimente istorice (dacă nu există deja)
        historical_events = [
            {
                'year': 1990,
                'title': 'Primele alegeri libere',
                'description': 'Ion Iliescu câștigă primele alegeri libere din România cu 85% din voturi.',
                'importance': 3
            },
            {
                'year': 1996,
                'title': 'Prima alternanță la putere',
                'description': 'Emil Constantinescu devine primul președinte de dreapta al României post-comuniste.',
                'importance': 3
            },
            {
                'year': 2004,
                'title': 'Victoria strânsă a lui Traian Băsescu',
                'description': 'Traian Băsescu câștigă la o diferență de doar 2% în fața lui Adrian Năstase.',
                'importance': 2
            },
            {
                'year': 2009,
                'title': 'Contestații privind fraudarea alegerilor',
                'description': 'Mircea Geoană pierde în fața lui Traian Băsescu la o diferență mică, acuzând nereguli.',
                'importance': 2
            },
            {
                'year': 2014,
                'title': 'Diaspora decisivă',
                'description': 'Klaus Iohannis câștigă surprinzător în fața lui Victor Ponta, cu un rol major al votului din diaspora.',
                'importance': 3
            },
            {
                'year': 2019,
                'title': 'Al doilea mandat pentru Klaus Iohannis',
                'description': 'Klaus Iohannis câștigă detașat în fața Vioricăi Dăncilă, cu peste 66% din voturi.',
                'importance': 2
            },
            {
                'year': 2024,
                'title': 'Anularea turului doi',
                'description': 'Curtea Constituțională a României anulează turul doi al alegerilor după acuzații de fraudă.',
                'importance': 3
            }
        ]

        for event_data in historical_events:
            HistoricalEvent.objects.get_or_create(
                year=event_data['year'],
                title=event_data['title'],
                defaults={
                    'description': event_data['description'],
                    'importance': event_data['importance']
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Evenimentul istoric "{event_data["title"]}" a fost creat.'))

        # Adăugăm influențe media
        media_influences = [
            {
                'election_year': 2009,
                'title': 'Confruntarea televizată decisivă',
                'description': 'Confruntarea televizată între Traian Băsescu și Mircea Geoană a influențat decisiv rezultatul alegerilor.',
                'media_type': 'traditional',
                'impact_level': 3
            },
            {
                'election_year': 2014,
                'title': 'Mobilizarea pe Facebook',
                'description': 'Rețelele sociale au jucat un rol crucial în mobilizarea alegătorilor, în special pentru Klaus Iohannis.',
                'media_type': 'social',
                'impact_level': 3
            },
            {
                'election_year': 2019,
                'title': 'Rolul videoconferințelor',
                'description': 'Klaus Iohannis a refuzat dezbaterile directe, preferând să comunice prin videoconferințe și declarații controlate.',
                'media_type': 'online',
                'impact_level': 2
            }
        ]

        for influence_data in media_influences:
            # Găsim anul electoral
            year = influence_data.pop('election_year')
            election_year = ElectionYear.objects.get(year=year)
            
            MediaInfluence.objects.get_or_create(
                election_year=election_year,
                title=influence_data['title'],
                defaults={
                    'description': influence_data['description'],
                    'media_type': influence_data['media_type'],
                    'impact_level': influence_data['impact_level']
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Influența media "{influence_data["title"]}" a fost creată.'))

        # Adăugăm controverse
        controversies = [
            {
                'title': 'Casele lui Klaus Iohannis',
                'description': 'Controversa legată de dobândirea celor șase case ale lui Klaus Iohannis.',
                'date': date(2014, 10, 15),
                'candidate_name': 'Klaus Iohannis',
                'election_year': 2014,
                'impact': 'Impact mediu asupra electoratului, folosit ca argument de PSD.'
            },
            {
                'title': 'Plagiatul lui Victor Ponta',
                'description': 'Acuzațiile privind plagiatul tezei de doctorat a lui Victor Ponta.',
                'date': date(2014, 9, 20),
                'candidate_name': 'Victor Ponta',
                'election_year': 2014,
                'impact': 'Impact semnificativ care a afectat credibilitatea candidatului.'
            },
            {
                'title': 'Incidentul de la Antena 3',
                'description': 'Mircea Geoană vizitează casa lui Sorin Ovidiu Vântu înainte de alegeri.',
                'date': date(2009, 12, 3),
                'candidate_name': 'Mircea Geoană',
                'election_year': 2009,
                'impact': 'Impact major, considerat decisiv pentru pierderea alegerilor.'
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

        self.stdout.write(self.style.SUCCESS('Popularea bazei de date cu date istorice a fost finalizată cu succes!'))