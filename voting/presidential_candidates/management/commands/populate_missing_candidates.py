from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date
from django.utils.text import slugify
from presidential_candidates.models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation,
    HistoricalEvent, MediaInfluence, Controversy
)

class Command(BaseCommand):
    help = 'Populează baza de date cu candidați lipsă și participările lor la alegerile prezidențiale'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Începe popularea candidaților lipsă...'))

        # Verifică existența anilor electorali necesari
        election_years = {
            1996: None,
            2009: None,
            2014: None,
            2019: None
        }
        
        for year in election_years.keys():
            try:
                election_years[year] = ElectionYear.objects.get(year=year)
                self.stdout.write(self.style.SUCCESS(f'Anul electoral {year} există deja.'))
            except ElectionYear.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Anul electoral {year} nu există în baza de date. Rulează mai întâi scriptul de populare a anilor electorali.'))
                return

        # 0. Crin Antonescu (2009) - Adăugăm participarea lipsă
        self.add_crin_antonescu_2009(election_years)
        
        # 1. Sorin Oprescu (2009)
        self.add_sorin_oprescu(election_years)
        
        # 2. Elena Udrea (2014)
        self.add_elena_udrea(election_years)
        
        # 3. Monica Macovei (2014)
        self.add_monica_macovei(election_years)
        
        # 4. Completare pentru Kelemen Hunor (2014)
        self.update_kelemen_hunor(election_years)
        
        # 5. Călin Popescu-Tăriceanu (2014)
        self.add_calin_popescu_tariceanu(election_years)
        
        # 6. Sebastian Popescu (2019)
        self.add_sebastian_popescu(election_years)
        
        # 7. Alexandru Cumpănașu (2019)
        self.add_alexandru_cumpanasu(election_years)
        
        # 8. Remus Cernea (2014)
        self.add_remus_cernea(election_years)
        
        # 9. Cătălin Ivan (2019)
        self.add_catalin_ivan(election_years)
        
        # 10. Varujan Vosganian (1996)
        self.add_varujan_vosganian(election_years)
        
        # 11. Marko Bela (1996)
        self.add_marko_bela(election_years)

        self.stdout.write(self.style.SUCCESS('Popularea candidaților lipsă a fost finalizată cu succes!'))

    def add_crin_antonescu_2009(self, election_years):
        """Adaugă participarea lui Crin Antonescu la alegerile din 2009"""
        try:
            crin_antonescu = PresidentialCandidate.objects.get(name='Crin Antonescu')
            self.stdout.write(self.style.SUCCESS(f'Candidatul Crin Antonescu există deja în baza de date.'))
            
            # Actualizăm experiența politică a candidatului
            if 'Candidat prezidențial (2009)' not in crin_antonescu.political_experience:
                crin_antonescu.political_experience += ', Candidat prezidențial (2009)'
                crin_antonescu.save()
                self.stdout.write(self.style.SUCCESS(f'Experiența politică a candidatului a fost actualizată.'))
            
            # Adaugă participarea
            participation_data = {
                'votes_count': 1945831,
                'votes_percentage': 20.02,
                'position': 3,
                'round': 1,
                'campaign_slogan': 'Dreptate până la capăt',
                'notable_events': 'Campanie centrată pe reforma statului și lupta împotriva corupției. A obținut al treilea cel mai bun scor, după Băsescu și Geoană.'
            }
            
            # Verifică dacă participarea există deja
            participation, created = ElectionParticipation.objects.get_or_create(
                candidate=crin_antonescu,
                election_year=election_years[2009],
                round=participation_data['round'],
                defaults=participation_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Participarea lui {crin_antonescu.name} la alegerile din 2009, turul {participation.round} a fost adăugată.'
                ))
            else:
                # Actualizăm participarea dacă există deja
                for key, value in participation_data.items():
                    setattr(participation, key, value)
                participation.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Participarea lui {crin_antonescu.name} la alegerile din 2009, turul {participation.round} a fost actualizată.'
                ))
            
            # Adaugă controverse legate de campania din 2009
            controversy_data = [
                {
                    'title': 'Conflictul cu Traian Băsescu în dezbaterea prezidențială',
                    'description': 'În timpul dezbaterii prezidențiale din 2009, Crin Antonescu a avut un schimb dur de replici cu Traian Băsescu, '
                                'acuzându-l că a distrus economia României și că reprezintă un model toxic de președinte. '
                                'Momentul a fost considerat unul dintre cele mai tensionate din campania electorală.',
                    'date': date(2009, 11, 20),
                    'candidate': crin_antonescu,
                    'election_year': election_years[2009],
                    'impact': 'Impact moderat spre major, consolidând imaginea lui Antonescu ca principal adversar ideologic al lui Băsescu, '
                            'dar insuficient pentru a-i asigura intrarea în turul doi.'
                },
                {
                    'title': 'Refuzul de a-l susține pe Mircea Geoană în turul doi',
                    'description': 'După primul tur al alegerilor din 2009, Crin Antonescu a fost criticat pentru ezitarea și '
                                'condițiile puse înainte de a-și anunța susținerea pentru Mircea Geoană în turul doi. '
                                'Unii analiști consideră că această ezitare a contribuit la înfrângerea lui Geoană.',
                    'date': date(2009, 11, 26),
                    'candidate': crin_antonescu,
                    'election_year': election_years[2009],
                    'impact': 'Impact semnificativ asupra rezultatului turului doi și asupra relațiilor ulterioare dintre PNL și PSD.'
                }
            ]
            
            controversies_added = 0
            for controversy in controversy_data:
                # Verifică dacă există deja o controversă cu același titlu și dată
                exists = Controversy.objects.filter(title=controversy['title'], date=controversy['date']).exists()
                if not exists:
                    Controversy.objects.create(**controversy)
                    controversies_added += 1
                    self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy["title"]}" a fost adăugată.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Controversa "{controversy["title"]}" există deja.'))
            
            # Adaugă o influență media specifică pentru campania lui Antonescu din 2009
            media_influence_data = {
                'title': 'Impactul canalelor TV în promovarea lui Crin Antonescu',
                'description': 'În 2009, Crin Antonescu a beneficiat de o acoperire favorabilă pe anumite canale TV, '
                            'în special Realitatea TV, care i-a oferit o platformă amplă pentru a-și prezenta mesajul electoral. '
                            'Acest lucru a contribuit semnificativ la creșterea notorietății sale în timpul campaniei.',
                'election_year': election_years[2009],
                'media_type': 'traditional',
                'impact_level': 2  # Impact mediu
            }
            
            # Verifică dacă există deja
            exists = MediaInfluence.objects.filter(title=media_influence_data['title'], election_year=election_years[2009]).exists()
            if not exists:
                MediaInfluence.objects.create(**media_influence_data)
                self.stdout.write(self.style.SUCCESS(f'Influența media "{media_influence_data["title"]}" a fost adăugată.'))
            else:
                self.stdout.write(self.style.WARNING(f'Influența media "{media_influence_data["title"]}" există deja.'))
            
            self.stdout.write(self.style.SUCCESS(
                f'Adăugarea participării lui Crin Antonescu la alegerile din 2009 a fost finalizată cu succes! '
                f'Au fost adăugate {controversies_added} controverse noi.'
            ))
            
        except PresidentialCandidate.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Candidatul Crin Antonescu nu există în baza de date. Rulează mai întâi scriptul de populare a candidaților.'))

    def add_remus_cernea(self, election_years):
        """Adaugă pe Remus Cernea și participarea sa din 2014"""
        # Datele candidatului
        candidate_data = {
            'name': 'Remus Cernea',
            'birth_date': date(1974, 6, 25),
            'party': 'Independent',
            'photo_url': 'https://example.com/remus_cernea.jpg',
            'biography': 'Remus Cernea este un politician și activist român pentru drepturile omului și secularism. '
                        'A fost deputat între 2012 și 2016 și a candidat la alegerile prezidențiale din 2014 ca independent.',
            'political_experience': 'Deputat (2012-2016), Candidat prezidențial (2014)',
            'education': 'Facultatea de Filosofie, Universitatea din București',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 104131,
            'votes_percentage': 1.09,
            'position': 9,
            'round': 1,
            'campaign_slogan': 'Politică pentru secolul 21',
            'notable_events': 'Campanie axată pe secularism, drepturile omului și o viziune progresistă asupra societății.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2014],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2014, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Poziții anti-religioase în campania electorală',
            'description': 'Remus Cernea a stârnit controverse prin declarațiile sale considerate anti-religioase, '
                          'inclusiv propunerea de a elimina finanțarea cultelor religioase de către stat și criticile '
                          'la adresa influenței Bisericii Ortodoxe Române în societate.',
            'date': date(2014, 10, 12),
            'candidate': candidate,
            'election_year': election_years[2014],
            'impact': 'Impact semnificativ în rândul electoratului conservator și religios, generând reacții negative din partea BOR.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def add_catalin_ivan(self, election_years):
        """Adaugă pe Cătălin Ivan și participarea sa din 2019"""
        # Datele candidatului
        candidate_data = {
            'name': 'Cătălin Ivan',
            'birth_date': date(1978, 12, 23),
            'party': 'Alternativa pentru Demnitate Națională',
            'photo_url': 'https://example.com/catalin_ivan.jpg',
            'biography': 'Cătălin Ivan este un politician român care a fost europarlamentar între 2009 și 2019. '
                        'După ce a părăsit PSD, a fondat partidul Alternativa pentru Demnitate Națională (ADN) '
                        'și a candidat la alegerile prezidențiale din 2019.',
            'political_experience': 'Europarlamentar (2009-2019), Fondator ADN, Candidat prezidențial (2019)',
            'education': 'Facultatea de Economie și Administrarea Afacerilor, Universitatea Alexandru Ioan Cuza din Iași',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 32787,
            'votes_percentage': 0.36,
            'position': 9,
            'round': 1,
            'campaign_slogan': 'România demnă',
            'notable_events': 'Campanie centrată pe critica PSD și pe ideea de reîntoarcere la valorile tradiționale.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2019],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2019, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Demisia din PSD și acuzațiile la adresa conducerii',
            'description': 'Cătălin Ivan a stârnit controverse prin acuzațiile dure aduse la adresa conducerii PSD '
                          'după ce a demisionat din partid, afirmând că formațiunea a fost capturată de un grup restrâns '
                          'de persoane în jurul lui Liviu Dragnea și că ar fi deviată de la valorile social-democrate.',
            'date': date(2018, 9, 12),
            'candidate': candidate,
            'election_year': election_years[2019],
            'impact': 'Impact redus la nivel electoral, dar semnificativ în contextul tensiunilor din interiorul PSD.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def add_varujan_vosganian(self, election_years):
        """Adaugă pe Varujan Vosganian și participarea sa din 1996"""
        # Datele candidatului
        candidate_data = {
            'name': 'Varujan Vosganian',
            'birth_date': date(1958, 7, 25),
            'party': 'Uniunea Forțelor de Dreapta',
            'photo_url': 'https://example.com/varujan_vosganian.jpg',
            'biography': 'Varujan Vosganian este un politician, economist și scriitor român de etnie armeană. '
                        'A candidat la alegerile prezidențiale din 1996 din partea Uniunii Forțelor de Dreapta. '
                        'Ulterior, a ocupat funcția de ministru al Economiei și Finanțelor.',
            'political_experience': 'Senator (1990-prezent, cu întreruperi), Ministru al Economiei și Finanțelor (2007-2008, 2012-2013), Candidat prezidențial (1996)',
            'education': 'Facultatea de Comerț, Academia de Studii Economice din București',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 43642,
            'votes_percentage': 0.34,
            'position': 12,
            'round': 1,
            'campaign_slogan': 'Un președinte pentru toți românii',
            'notable_events': 'Prima participare a unui candidat de etnie armeană la alegerile prezidențiale din România modernă.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[1996],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 1996, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Tranziția politică de la liberalism la conservatorism',
            'description': 'Varujan Vosganian a stârnit controverse prin traseismul său politic, candidând inițial din partea '
                          'Uniunii Forțelor de Dreapta, apoi activând în Partidul Național Liberal, pentru ca ulterior să se '
                          'alăture formațiunilor conservatoare precum PC și ALDE.',
            'date': date(1996, 11, 1),
            'candidate': candidate,
            'election_year': election_years[1996],
            'impact': 'Impact moderat, afectând percepția despre consecvența sa ideologică în rândul alegătorilor.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def add_marko_bela(self, election_years):
        """Adaugă pe Marko Bela și participarea sa din 1996"""
        # Datele candidatului
        candidate_data = {
            'name': 'Marko Bela',
            'birth_date': date(1951, 9, 8),
            'party': 'Uniunea Democrată Maghiară din România',
            'photo_url': 'https://example.com/marko_bela.jpg',
            'biography': 'Marko Bela este un politician și scriitor român de etnie maghiară. A fost președintele UDMR '
                        'între 1993 și 2011 și a ocupat funcția de viceprim-ministru în mai multe guverne. A candidat '
                        'la alegerile prezidențiale din 1996 din partea UDMR.',
            'political_experience': 'Președinte UDMR (1993-2011), Deputat (1990-2004), Senator (2004-2012), Viceprim-ministru (2004-2007, 2009-2012), Candidat prezidențial (1996)',
            'education': 'Facultatea de Filologie, Universitatea Babeș-Bolyai din Cluj-Napoca',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 761411,
            'votes_percentage': 6.02,
            'position': 5,
            'round': 1,
            'campaign_slogan': 'Pentru drepturile minorităților',
            'notable_events': 'Prima candidatură semnificativă a unui reprezentant al minorității maghiare la alegerile prezidențiale.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[1996],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 1996, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Declarațiile despre autonomia Ținutului Secuiesc',
            'description': 'În timpul campaniei prezidențiale din 1996, Marko Bela a susținut public autonomia Ținutului Secuiesc, '
                          'generând reacții negative din partea celorlalți candidați și a unei părți semnificative a opiniei publice românești.',
            'date': date(1996, 10, 20),
            'candidate': candidate,
            'election_year': election_years[1996],
            'impact': 'Impact semnificativ, consolidând percepția că UDMR reprezintă exclusiv interesele comunității maghiare.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))
            
    def add_sorin_oprescu(self, election_years):
        """Adaugă pe Sorin Oprescu și participarea sa din 2009"""
        # Datele candidatului
        candidate_data = {
            'name': 'Sorin Oprescu',
            'birth_date': date(1951, 11, 7),
            'party': 'Independent',
            'photo_url': 'https://example.com/sorin_oprescu.jpg',
            'biography': 'Sorin Oprescu este un medic și politician român care a ocupat funcția de primar general al Bucureștiului '
                        'între 2008 și 2015. Anterior, a fost senator PSD, dar a candidat ca independent la alegerile '
                        'prezidențiale din 2009 și la cele pentru Primăria București din 2008.',
            'political_experience': 'Senator (2004-2008), Primar General al Bucureștiului (2008-2015), Candidat prezidențial (2009)',
            'education': 'Universitatea de Medicină și Farmacie Carol Davila din București',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 309764,
            'votes_percentage': 3.18,
            'position': 4,
            'round': 1,
            'campaign_slogan': 'Cu mintea și cu sufletul',
            'notable_events': 'A fost primul candidat independent cu notorietate după Revoluție care a obținut un scor semnificativ.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2009],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2009, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Candidatura lui Oprescu după demisia din PSD',
            'description': 'Sorin Oprescu a demisionat din PSD pentru a candida ca independent la alegerile prezidențiale din 2009, '
                          'ceea ce a generat acuzații că ar fi fost un candidat „marionetă" folosit pentru a diviza electoratul de stânga.',
            'date': date(2009, 9, 15),
            'candidate': candidate,
            'election_year': election_years[2009],
            'impact': 'Impact moderat, contribuind la fragmentarea votului de stânga și potențial afectând șansele lui Mircea Geoană.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def add_elena_udrea(self, election_years):
        """Adaugă pe Elena Udrea și participarea sa din 2014"""
        # Datele candidatului
        candidate_data = {
            'name': 'Elena Udrea',
            'birth_date': date(1973, 12, 26),
            'party': 'Partidul Mișcarea Populară',
            'photo_url': 'https://example.com/elena_udrea.jpg',
            'biography': 'Elena Udrea este o politiciană română care a ocupat funcția de ministru al Dezvoltării Regionale și Turismului '
                        'între 2009 și 2012. A fost una dintre cele mai apropiate colaboratoare ale președintelui Traian Băsescu și a '
                        'candidat la alegerile prezidențiale din 2014 din partea PMP.',
            'political_experience': 'Ministru al Dezvoltării Regionale și Turismului (2009-2012), Deputat (2008-2016), Candidat prezidențial (2014)',
            'education': 'Facultatea de Drept și Facultatea de Științe Economice, Universitatea Dimitrie Cantemir',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 493376,
            'votes_percentage': 5.20,
            'position': 4,
            'round': 1,
            'campaign_slogan': 'România frumoasă',
            'notable_events': 'A fost prima femeie cu un scor semnificativ la alegerile prezidențiale din România.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2014],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2014, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Anchetele DNA în timpul campaniei din 2014',
            'description': 'În timpul campaniei prezidențiale din 2014, Elena Udrea a fost vizată de anchete ale DNA, '
                          'ceea ce a ridicat întrebări despre motivațiile politice ale acestor anchete și despre impactul lor asupra procesului electoral.',
            'date': date(2014, 10, 25),
            'candidate': candidate,
            'election_year': election_years[2014],
            'impact': 'Impact semnificativ, afectând credibilitatea candidatei și rezultatele electorale.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def add_monica_macovei(self, election_years):
        """Adaugă pe Monica Macovei și participarea sa din 2014"""
        # Datele candidatului
        candidate_data = {
            'name': 'Monica Macovei',
            'birth_date': date(1959, 2, 4),
            'party': 'Independent',
            'photo_url': 'https://example.com/monica_macovei.jpg',
            'biography': 'Monica Macovei este o politiciană și juristă română care a ocupat funcția de ministru al Justiției '
                        'între 2004 și 2007. A fost europarlamentar între 2009 și 2019 și a candidat ca independentă la '
                        'alegerile prezidențiale din 2014.',
            'political_experience': 'Ministru al Justiției (2004-2007), Europarlamentar (2009-2019), Candidat prezidențial (2014)',
            'education': 'Facultatea de Drept a Universității din București, Central European University',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 401068,
            'votes_percentage': 4.44,
            'position': 5,
            'round': 1,
            'campaign_slogan': 'Curățenie în politică!',
            'notable_events': 'A fost prima campanie prezidențială din România în care rețelele sociale au avut un rol major pentru un candidat independent.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2014],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2014, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Finanțarea campaniei lui Monica Macovei',
            'description': 'În timpul campaniei prezidențiale din 2014, au existat controverse privind sursele de finanțare ale campaniei '
                          'Monicăi Macovei, existând acuzații că ar fi primit fonduri din exterior datorită legăturilor sale cu organizații non-guvernamentale.',
            'date': date(2014, 9, 30),
            'candidate': candidate,
            'election_year': election_years[2014],
            'impact': 'Impact redus, dar a alimentat teoriile care o prezentau ca fiind un candidat susținut din afara țării.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def update_kelemen_hunor(self, election_years):
        """Completează participarea lui Kelemen Hunor din 2014"""
        try:
            kelemen_hunor = PresidentialCandidate.objects.get(name='Kelemen Hunor')
            self.stdout.write(self.style.SUCCESS(f'Candidatul Kelemen Hunor există deja în baza de date.'))
            
            # Adaugă participarea din 2014 dacă nu există
            participation_data = {
                'votes_count': 329727,
                'votes_percentage': 3.47,
                'position': 6,
                'round': 1,
                'campaign_slogan': 'Respect pentru toți',
                'notable_events': 'A reprezentat comunitatea maghiară și a pus accentul pe drepturile minorităților.'
            }
            
            # Verifică dacă participarea există deja
            participation, created = ElectionParticipation.objects.get_or_create(
                candidate=kelemen_hunor,
                election_year=election_years[2014],
                round=participation_data['round'],
                defaults=participation_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Participarea lui Kelemen Hunor la alegerile din 2014, turul {participation.round} a fost adăugată.'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Participarea lui Kelemen Hunor la alegerile din 2014, turul {participation.round} există deja.'
                ))
                
            # Adaugă o controversă pentru 2014
            controversy_data = {
                'title': 'Declarațiile despre autonomia Ținutului Secuiesc',
                'description': 'În timpul campaniei prezidențiale din 2014, Kelemen Hunor a susținut autonomia Ținutului Secuiesc, '
                              'declarații care au generat reacții negative din partea celorlalți candidați și a unei părți a opiniei publice.',
                'date': date(2014, 10, 15),
                'candidate': kelemen_hunor,
                'election_year': election_years[2014],
                'impact': 'Impact semnificativ în rândul electoratului românesc, dar pozitiv în rândul electoratului maghiar.'
            }
            
            # Verifică dacă controversa există deja
            exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
            if not exists:
                Controversy.objects.create(**controversy_data)
                self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))
            
        except PresidentialCandidate.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Candidatul Kelemen Hunor nu există în baza de date. Nu se poate adăuga participarea.'))

    def add_calin_popescu_tariceanu(self, election_years):
        """Adaugă pe Călin Popescu-Tăriceanu și participarea sa din 2014"""
        # Datele candidatului
        candidate_data = {
            'name': 'Călin Popescu-Tăriceanu',
            'birth_date': date(1952, 1, 14),
            'party': 'Partidul Liberal Reformator',
            'photo_url': 'https://example.com/calin_popescu_tariceanu.jpg',
            'biography': 'Călin Popescu-Tăriceanu este un politician român care a ocupat funcția de prim-ministru al României '
                        'între 2004 și 2008. A fost președinte al Senatului între 2014 și 2019. A candidat la alegerile '
                        'prezidențiale din 2014 din partea Partidului Liberal Reformator.',
            'political_experience': 'Prim-ministru (2004-2008), Președinte al Senatului (2014-2019), Candidat prezidențial (2014)',
            'education': 'Facultatea de Hidrotehnică din cadrul Institutului de Construcții București',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 508572,
            'votes_percentage': 5.36,
            'position': 3,
            'round': 1,
            'campaign_slogan': 'România pe primul loc',
            'notable_events': 'A candidat după ce s-a separat de PNL, critică majoră la adresa lui Traian Băsescu și a statului paralel.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2014],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2014, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Ruperea de PNL înainte de prezidențiale',
            'description': 'Călin Popescu-Tăriceanu a refuzat să susțină candidatura lui Klaus Iohannis, părăsind PNL și '
                          'formând un nou partid pentru a candida el însuși la prezidențiale, ceea ce a fost văzut ca o mișcare '
                          'menită să fragmenteze electoratul de dreapta și să favorizeze indirect PSD.',
            'date': date(2014, 7, 1),
            'candidate': candidate,
            'election_year': election_years[2014],
            'impact': 'Impact moderat, afectând imaginea solidă a dreptei și relațiile din interiorul fostului USL.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def add_sebastian_popescu(self, election_years):
        """Adaugă pe Sebastian Popescu și participarea sa din 2019"""
        # Datele candidatului
        candidate_data = {
            'name': 'Sebastian-Constantin Popescu',
            'birth_date': date(1971, 6, 15),
            'party': 'Partidul Noua Românie',
            'photo_url': 'https://example.com/sebastian_popescu.jpg',
            'biography': 'Sebastian-Constantin Popescu este un politician român, președinte al Partidului Noua Românie. '
                        'A candidat la alegerile prezidențiale din 2019, promovând valori conservatoare și patriotice.',
            'political_experience': 'Fondator și președinte al Partidului Noua Românie, Candidat prezidențial (2019)',
            'education': 'Studii de inginerie',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 30850,
            'votes_percentage': 0.33,
            'position': 10,
            'round': 1,
            'campaign_slogan': 'România merită mai mult',
            'notable_events': 'Campanie axată pe valorile creștine și pe critici la adresa clasei politice tradiționale.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2019],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2019, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Susținerea viziunii tradiționaliste',
            'description': 'Sebastian-Constantin Popescu a stârnit controverse prin pozițiile sale puternic conservatoare '
                          'și tradiționaliste, inclusiv împotriva căsătoriilor între persoane de același sex și a politicilor '
                          'pro-avort, polarizând opiniile în timpul campaniei.',
            'date': date(2019, 10, 20),
            'candidate': candidate,
            'election_year': election_years[2019],
            'impact': 'Impact redus la nivel național, dar semnificativ în rândul electoratului conservator.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))

    def add_alexandru_cumpanasu(self, election_years):
        """Adaugă pe Alexandru Cumpănașu și participarea sa din 2019"""
        # Datele candidatului
        candidate_data = {
            'name': 'Alexandru Cumpănașu',
            'birth_date': date(1981, 2, 13),
            'party': 'Independent',
            'photo_url': 'https://example.com/alexandru_cumpanasu.jpg',
            'biography': 'Alexandru Cumpănașu este un activist civic și politician român care a candidat ca independent la '
                        'alegerile prezidențiale din 2019. A devenit cunoscut la nivel național în contextul cazului Caracal, '
                        'fiind unchiul uneia dintre victimele presupuse.',
            'political_experience': 'Președinte al unor ONG-uri, Candidat prezidențial (2019)',
            'education': 'Universitatea Națională de Apărare "Carol I"',
            'is_current': False
        }
        
        # Generăm slug
        candidate_data['slug'] = slugify(candidate_data['name'])
        
        # Verifică dacă candidatul există deja
        candidate, created = PresidentialCandidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults=candidate_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost creat.'))
        else:
            # Actualizăm candidatul dacă există deja
            for key, value in candidate_data.items():
                setattr(candidate, key, value)
            candidate.save()
            self.stdout.write(self.style.SUCCESS(f'Candidatul {candidate_data["name"]} a fost actualizat.'))
        
        # Adaugă participarea
        participation_data = {
            'votes_count': 141316,
            'votes_percentage': 1.53,
            'position': 7,
            'round': 1,
            'campaign_slogan': 'Lupta împotriva sistemului',
            'notable_events': 'Campanie puternic mediatizată, bazată pe retorica anti-sistem și pe emoția publică generată de cazul Caracal.'
        }
        
        # Verifică dacă participarea există deja
        participation, created = ElectionParticipation.objects.get_or_create(
            candidate=candidate,
            election_year=election_years[2019],
            round=participation_data['round'],
            defaults=participation_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Participarea lui {candidate.name} la alegerile din 2019, turul {participation.round} a fost adăugată.'
            ))
        
        # Adaugă o controversă
        controversy_data = {
            'title': 'Exploatarea mediatică a cazului Caracal',
            'description': 'Alexandru Cumpănașu a fost acuzat că a folosit tragedia de la Caracal, unde nepoata sa era una dintre '
                          'victimele presupuse, pentru a-și construi o platformă politică și a câștiga capital electoral, ceea ce a '
                          'generat dezbateri etice intense.',
            'date': date(2019, 8, 25),
            'candidate': candidate,
            'election_year': election_years[2019],
            'impact': 'Impact semnificativ, contribuind atât la notorietatea sa cât și la criticile la adresa sa.'
        }
        
        # Verifică dacă controversa există deja
        exists = Controversy.objects.filter(title=controversy_data['title'], date=controversy_data['date']).exists()
        if not exists:
            Controversy.objects.create(**controversy_data)
            self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))