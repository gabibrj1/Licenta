from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rezultate.utils import ResultsPopulator
from rezultate.models import VoteResult
from vote.models import PresidentialCandidate, PresidentialRound2Candidate, ParliamentaryParty
from statistici.models import VoteStatistics
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

User = get_user_model()

class Command(BaseCommand):
    help = 'Populează baza de date cu rezultate de vot pentru străinătate folosind candidații din vote app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vote-type',
            type=str,
            default='prezidentiale',
            help='Tipul de vot pentru care să se creeze rezultate (prezidentiale, prezidentiale_tur2, parlamentare)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Șterge rezultatele existente pentru străinătate înainte de populare',
        )

    def handle(self, *args, **options):
        vote_type = options['vote_type']
        location = 'strainatate'
        
        if options['clear']:
            # Șterge rezultatele existente pentru străinătate
            deleted_count = ResultsPopulator.clear_results(vote_type, location)
            self.stdout.write(
                self.style.WARNING(f'Au fost șterse {deleted_count} rezultate pentru străinătate.')
            )

        # Verifică candidații disponibili în vote app
        self.stdout.write('Verific candidații disponibili în vote app pentru străinătate...')
        
        if vote_type == 'prezidentiale':
            candidates_count = PresidentialCandidate.objects.count()
            self.stdout.write(f'Candidați prezidențiali disponibili: {candidates_count}')
        elif vote_type == 'prezidentiale_tur2':
            candidates_count = PresidentialRound2Candidate.objects.count()
            self.stdout.write(f'Candidați tur 2 disponibili: {candidates_count}')
        elif vote_type == 'parlamentare':
            candidates_count = ParliamentaryParty.objects.count()
            self.stdout.write(f'Partide parlamentare disponibile: {candidates_count}')
        
        if candidates_count == 0:
            self.stdout.write(
                self.style.ERROR(
                    f'Nu există candidați/partide pentru {vote_type} în vote app! '
                    'Adaugă candidați în aplicația vote mai întâi.'
                )
            )
            return

        # Verifică dacă există statistici pentru străinătate
        existing_stats = VoteStatistics.objects.filter(
            vote_type=vote_type,
            location_type=location
        )
        
        if not existing_stats.exists():
            self.stdout.write(
                self.style.ERROR(
                    f'Nu există statistici pentru {vote_type} în {location}. '
                    'Rulează mai întâi scriptul de populare a statisticilor pentru străinătate.'
                )
            )
            return

        # Populează rezultatele folosind candidații din vote app
        self.stdout.write(f'Populez rezultate pentru {vote_type} în {location} folosind candidații din vote app...')
        
        results = ResultsPopulator.populate_results_from_statistics(vote_type, location)
        
        self.stdout.write(
            self.style.SUCCESS(f'Au fost create {len(results)} rezultate pentru {vote_type} în străinătate.')
        )

        # Afișează un sumar al rezultatelor
        self.stdout.write('\n=== SUMAR REZULTATE STRĂINĂTATE ===')
        
        total_results = VoteResult.objects.filter(
            vote_type=vote_type,
            location_type=location
        ).count()
        self.stdout.write(f'Total rezultate pentru {vote_type} în {location}: {total_results}')
        
        if vote_type in ['prezidentiale', 'prezidentiale_tur2']:
            self.display_presidential_results_by_country(vote_type, location)
        elif vote_type == 'parlamentare':
            self.display_parliamentary_results_by_country(location)

        self.stdout.write(
            self.style.SUCCESS('\n✓ Popularea rezultatelor pentru străinătate s-a finalizat cu succes!')
        )

    def display_presidential_results_by_country(self, vote_type, location):
        """Afișează rezultatele prezidențiale pentru străinătate"""
        self.stdout.write('\nRezultate prezidențiale în străinătate (top candidați):')
        
        # Determină câmpul corect în funcție de tipul de vot
        if vote_type == 'prezidentiale':
            candidate_field = 'presidential_candidate'
            filter_field = f'{candidate_field}__isnull'
        else:  # prezidentiale_tur2
            candidate_field = 'presidential_round2_candidate'
            filter_field = f'{candidate_field}__isnull'
        
        # Rezultate generale
        results = VoteResult.objects.filter(
            vote_type=vote_type,
            location_type=location,
            **{filter_field: False}
        ).values(
            f'{candidate_field}__order_nr',
            f'{candidate_field}__name',
            f'{candidate_field}__party'
        ).annotate(
            votes=Count('id')
        ).order_by('-votes')[:8]
        
        total_votes = VoteResult.objects.filter(
            vote_type=vote_type,
            location_type=location,
            **{filter_field: False}
        ).count()
        
        for i, result in enumerate(results, 1):
            percentage = (result['votes'] / total_votes * 100) if total_votes > 0 else 0
            order_nr = result[f'{candidate_field}__order_nr'] or 0
            self.stdout.write(
                f"{i:2d}. {result[f'{candidate_field}__name']} "
                f"({result[f'{candidate_field}__party'] or 'Independent'}) "
                f"[#{order_nr}] - {result['votes']:,} voturi ({percentage:.2f}%)"
            )
        
        # Rezultate pe țări principale
        self.stdout.write('\nRezultate pe țări principale:')
        main_countries = ['Germania', 'Italia', 'Spania', 'Franța', 'Marea Britanie']
        
        for country in main_countries:
            country_total = VoteResult.objects.filter(
                vote_type=vote_type,
                location_type=location,
                county=country,
                **{filter_field: False}
            ).count()
            
            if country_total > 0:
                winner = VoteResult.objects.filter(
                    vote_type=vote_type,
                    location_type=location,
                    county=country,
                    **{filter_field: False}
                ).values(
                    f'{candidate_field}__name',
                    f'{candidate_field}__party'
                ).annotate(
                    votes=Count('id')
                ).order_by('-votes').first()
                
                if winner:
                    percentage = (winner['votes'] / country_total * 100)
                    self.stdout.write(
                        f"{country}: {winner[f'{candidate_field}__name']} "
                        f"({winner[f'{candidate_field}__party'] or 'Independent'}) - "
                        f"{winner['votes']:,}/{country_total:,} voturi ({percentage:.1f}%)"
                    )

    def display_parliamentary_results_by_country(self, location):
        """Afișează rezultatele parlamentare pentru străinătate"""
        self.stdout.write('\nRezultate parlamentare în străinătate:')
        
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