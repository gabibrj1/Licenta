from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rezultate.utils import ResultsPopulator
from rezultate.models import VoteResult
from vote.models import PresidentialCandidate, PresidentialRound2Candidate, ParliamentaryParty, LocalCandidate
from statistici.models import VoteStatistics
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

User = get_user_model()

class Command(BaseCommand):
    help = 'Populează baza de date cu rezultate de vot folosind candidații din vote app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vote-type',
            type=str,
            default='prezidentiale',
            help='Tipul de vot pentru care să se creeze rezultate (prezidentiale, prezidentiale_tur2, parlamentare, locale)',
        )
        parser.add_argument(
            '--location',
            type=str,
            default='romania',
            help='Locația pentru care să se creeze rezultate (romania, strainatate)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Șterge rezultatele existente înainte de populare',
        )
        parser.add_argument(
            '--info',
            action='store_true',
            help='Afișează informații despre candidații disponibili în vote app',
        )

    def handle(self, *args, **options):
        vote_type = options['vote_type']
        location = options['location']
        
        if options['info']:
            self.show_candidates_info()
            return
        
        if options['clear']:
            # Șterge rezultatele existente
            deleted_count = ResultsPopulator.clear_results(vote_type, location)
            self.stdout.write(
                self.style.WARNING(f'Au fost șterse {deleted_count} rezultate existente.')
            )

        # Verifică candidații disponibili în vote app
        self.stdout.write('Verific candidații disponibili în vote app...')
        
        if vote_type == 'prezidentiale':
            candidates_count = PresidentialCandidate.objects.count()
            self.stdout.write(f'Candidați prezidențiali disponibili: {candidates_count}')
            if candidates_count == 0:
                self.stdout.write(
                    self.style.ERROR(
                        'Nu există candidați prezidențiali în vote app! '
                        'Adaugă candidați în aplicația vote mai întâi.'
                    )
                )
                return
        
        elif vote_type == 'prezidentiale_tur2':
            candidates_count = PresidentialRound2Candidate.objects.count()
            self.stdout.write(f'Candidați tur 2 disponibili: {candidates_count}')
            if candidates_count == 0:
                self.stdout.write(
                    self.style.ERROR(
                        'Nu există candidați pentru turul 2 în vote app! '
                        'Adaugă candidați în aplicația vote mai întâi.'
                    )
                )
                return
        
        elif vote_type == 'parlamentare':
            parties_count = ParliamentaryParty.objects.count()
            self.stdout.write(f'Partide parlamentare disponibile: {parties_count}')
            if parties_count == 0:
                self.stdout.write(
                    self.style.ERROR(
                        'Nu există partide parlamentare în vote app! '
                        'Adaugă partide în aplicația vote mai întâi.'
                    )
                )
                return
        
        elif vote_type == 'locale':
            candidates_count = LocalCandidate.objects.count()
            self.stdout.write(f'Candidați locali disponibili: {candidates_count}')
            if candidates_count == 0:
                self.stdout.write(
                    self.style.ERROR(
                        'Nu există candidați locali în vote app! '
                        'Adaugă candidați în aplicația vote mai întâi.'
                    )
                )
                return

        # Verifică dacă există statistici pentru tipul de vot specificat
        existing_stats = VoteStatistics.objects.filter(
            vote_type=vote_type,
            location_type=location
        )
        
        if not existing_stats.exists():
            self.stdout.write(
                self.style.ERROR(
                    f'Nu există statistici pentru {vote_type} în {location}. '
                    'Rulează mai întâi scriptul de populare a statisticilor.'
                )
            )
            return

        # Populează rezultatele pe baza statisticilor folosind candidații din vote app
        self.stdout.write(f'Populez rezultate pentru {vote_type} în {location} folosind candidații din vote app...')
        
        results = ResultsPopulator.populate_results_from_statistics(vote_type, location)
        
        self.stdout.write(
            self.style.SUCCESS(f'Au fost create {len(results)} rezultate pentru {vote_type}.')
        )

        # Afișează un sumar al rezultatelor
        self.stdout.write('\n=== SUMAR REZULTATE ===')
        
        total_results = VoteResult.objects.filter(
            vote_type=vote_type,
            location_type=location
        ).count()
        self.stdout.write(f'Total rezultate pentru {vote_type} în {location}: {total_results}')
        
        if vote_type == 'prezidentiale':
            self.display_presidential_results(location)
        elif vote_type == 'prezidentiale_tur2':
            self.display_presidential_round2_results(location)
        elif vote_type == 'parlamentare':
            self.display_parliamentary_results(location)
        elif vote_type == 'locale':
            self.display_local_results(location)

        self.stdout.write(
            self.style.SUCCESS('\n✓ Popularea rezultatelor s-a finalizat cu succes!')
        )

    def show_candidates_info(self):
        """Afișează informații despre candidații disponibili"""
        info = ResultsPopulator.get_available_candidates_info()
        
        self.stdout.write('\n=== CANDIDAȚI DISPONIBILI ÎN VOTE APP ===')
        
        self.stdout.write(f"Candidați prezidențiali: {info['presidential_candidates']}")
        self.stdout.write(f"Candidați tur 2: {info['presidential_round2_candidates']}")
        self.stdout.write(f"Partide parlamentare: {info['parliamentary_parties']}")
        self.stdout.write(f"Candidați locali: {info['local_candidates']}")
        
        if info['sample_presidential']:
            self.stdout.write('\nExemple candidați prezidențiali:')
            for candidate in info['sample_presidential']:
                self.stdout.write(f"  - {candidate['name']} ({candidate['party']}) [#{candidate['order_nr']}]")
        
        if info['sample_parliamentary']:
            self.stdout.write('\nExemple partide parlamentare:')
            for party in info['sample_parliamentary']:
                self.stdout.write(f"  - {party['abbreviation']} - {party['name']} [#{party['order_nr']}]")
        
        if info['sample_local']:
            self.stdout.write('\nExemple candidați locali:')
            for candidate in info['sample_local']:
                self.stdout.write(f"  - {candidate['name']} ({candidate['party']}) - {candidate['position']} în {candidate['county']}")

    def display_presidential_results(self, location):
        """Afișează un sumar al rezultatelor prezidențiale"""
        self.stdout.write('\nRezultate prezidențiale (top 10):')
        
        results = VoteResult.objects.filter(
            vote_type='prezidentiale',
            location_type=location,
            presidential_candidate__isnull=False
        ).values(
            'presidential_candidate__order_nr',
            'presidential_candidate__name',
            'presidential_candidate__party'
        ).annotate(
            votes=Count('id')
        ).order_by('-votes')[:10]
        
        total_votes = VoteResult.objects.filter(
            vote_type='prezidentiale',
            location_type=location,
            presidential_candidate__isnull=False
        ).count()
        
        for i, result in enumerate(results, 1):
            percentage = (result['votes'] / total_votes * 100) if total_votes > 0 else 0
            order_nr = result['presidential_candidate__order_nr'] or 0
            self.stdout.write(
                f"{i:2d}. {result['presidential_candidate__name']} "
                f"({result['presidential_candidate__party'] or 'Independent'}) "
                f"[#{order_nr}] - {result['votes']:,} voturi ({percentage:.2f}%)"
            )

    def display_presidential_round2_results(self, location):
        """Afișează un sumar al rezultatelor turul 2"""
        self.stdout.write('\nRezultate turul 2 prezidențial:')
        
        results = VoteResult.objects.filter(
            vote_type='prezidentiale_tur2',
            location_type=location,
            presidential_round2_candidate__isnull=False
        ).values(
            'presidential_round2_candidate__order_nr',
            'presidential_round2_candidate__name',
            'presidential_round2_candidate__party',
            'presidential_round2_candidate__round1_percentage'
        ).annotate(
            votes=Count('id')
        ).order_by('-votes')
        
        total_votes = VoteResult.objects.filter(
            vote_type='prezidentiale_tur2',
            location_type=location,
            presidential_round2_candidate__isnull=False
        ).count()
        
        for i, result in enumerate(results, 1):
            percentage = (result['votes'] / total_votes * 100) if total_votes > 0 else 0
            order_nr = result['presidential_round2_candidate__order_nr'] or 0
            round1_perc = result['presidential_round2_candidate__round1_percentage'] or 0
            self.stdout.write(
                f"{i:2d}. {result['presidential_round2_candidate__name']} "
                f"({result['presidential_round2_candidate__party'] or 'Independent'}) "
                f"[#{order_nr}] - {result['votes']:,} voturi ({percentage:.2f}%) "
                f"[Tur 1: {round1_perc:.2f}%]"
            )

    def display_parliamentary_results(self, location):
        """Afișează un sumar al rezultatelor parlamentare"""
        self.stdout.write('\nRezultate parlamentare:')
        
        results = VoteResult.objects.filter(
            vote_type='parlamentare',
            location_type=location,
            parliamentary_party__isnull=False
        ).values(
            'parliamentary_party__order_nr',
            'parliamentary_party__name',
            'parliamentary_party__abbreviation'
        ).annotate(
            votes=Count('id')
        ).order_by('-votes')
        
        total_votes = VoteResult.objects.filter(
            vote_type='parlamentare',
            location_type=location,
            parliamentary_party__isnull=False
        ).count()
        
        for i, result in enumerate(results, 1):
            percentage = (result['votes'] / total_votes * 100) if total_votes > 0 else 0
            order_nr = result['parliamentary_party__order_nr'] or 0
            self.stdout.write(
                f"{i:2d}. {result['parliamentary_party__abbreviation']} - "
                f"{result['parliamentary_party__name']} "
                f"[#{order_nr}] - {result['votes']:,} voturi ({percentage:.2f}%)"
            )

    def display_local_results(self, location):
        """Afișează un sumar al rezultatelor locale"""
        self.stdout.write('\nRezultate locale (primari - top 5 județe):')
        
        # Grupează pe județe și afișează câștigătorii
        counties = VoteResult.objects.filter(
            vote_type='locale',
            location_type=location,
            local_candidate__isnull=False,
            local_candidate__position='primar'
        ).values_list('county', flat=True).distinct()
        
        for county in list(counties)[:5]:  # Doar primele 5 județe
            if county:
                winner = VoteResult.objects.filter(
                    vote_type='locale',
                    location_type=location,
                    county=county,
                    local_candidate__position='primar'
                ).values(
                    'local_candidate__name',
                    'local_candidate__party'
                ).annotate(
                    votes=Count('id')
                ).order_by('-votes').first()
                
                if winner:
                    county_total = VoteResult.objects.filter(
                        vote_type='locale',
                        location_type=location,
                        county=county,
                        local_candidate__position='primar'
                    ).count()
                    
                    percentage = (winner['votes'] / county_total * 100) if county_total > 0 else 0
                    
                    self.stdout.write(
                        f"{county}: {winner['local_candidate__name']} "
                        f"({winner['local_candidate__party'] or 'Independent'}) - "
                        f"{winner['votes']:,} voturi ({percentage:.2f}%)"
                    )