from django.core.management.base import BaseCommand
from django.db.models import Count
from vote.models import PresidentialVote, PresidentialCandidate, PresidentialRound2Candidate

class Command(BaseCommand):
    help = 'Creează candidații pentru turul 2 pe baza rezultatelor din turul 1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Selectează automat primii 2 candidați cu cele mai multe voturi',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Șterge candidații existenți din turul 2 înainte de a adăuga noii candidați',
        )

    def handle(self, *args, **options):
        # Șterge candidații existenți din turul 2 dacă se specifică
        if options['clear']:
            deleted_count = PresidentialRound2Candidate.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Au fost șterși {deleted_count} candidați existenți din turul 2.')
            )

        # Calculează rezultatele din turul 1
        results = PresidentialVote.objects.values(
            'candidate__id',
            'candidate__name', 
            'candidate__party',
            'candidate__photo_url',
            'candidate__description',
            'candidate__order_nr'
        ).annotate(
            vote_count=Count('id')
        ).order_by('-vote_count')

        if not results:
            self.stdout.write(
                self.style.ERROR('Nu există voturi înregistrate pentru turul 1 prezidențial.')
            )
            return

        # Afișează rezultatele
        self.stdout.write('\n=== REZULTATE TURUL 1 ===')
        total_votes = sum(result['vote_count'] for result in results)
        
        for i, result in enumerate(results, 1):
            percentage = (result['vote_count'] / total_votes * 100) if total_votes > 0 else 0
            self.stdout.write(
                f"{i}. {result['candidate__name']} ({result['candidate__party']}) - "
                f"{result['vote_count']} voturi ({percentage:.2f}%)"
            )

        if options['auto']:
            # Selectează automat primii 2
            if len(results) < 2:
                self.stdout.write(
                    self.style.ERROR('Nu sunt suficienți candidați în turul 1 pentru a crea turul 2.')
                )
                return
            
            top_2 = results[:2]
            self.create_round2_candidates(top_2, total_votes)
        else:
            # Selecție manuală
            self.stdout.write('\nSelectați candidații pentru turul 2:')
            
            if len(results) < 2:
                self.stdout.write(
                    self.style.ERROR('Nu sunt suficienți candidați pentru turul 2.')
                )
                return
            
            # Citește selecția utilizatorului
            selected_candidates = []
            for i in range(2):
                while True:
                    try:
                        choice = input(f'Selectați candidatul {i+1} (introduceți numărul 1-{len(results)}): ')
                        choice_idx = int(choice) - 1
                        
                        if 0 <= choice_idx < len(results):
                            candidate = results[choice_idx]
                            if candidate not in selected_candidates:
                                selected_candidates.append(candidate)
                                self.stdout.write(
                                    f'Selectat: {candidate["candidate__name"]} ({candidate["candidate__party"]})'
                                )
                                break
                            else:
                                self.stdout.write('Candidatul a fost deja selectat. Alegeți altul.')
                        else:
                            self.stdout.write('Selecție invalidă. Încercați din nou.')
                    except (ValueError, KeyboardInterrupt):
                        self.stdout.write('Selecție invalidă. Încercați din nou.')
            
            self.create_round2_candidates(selected_candidates, total_votes)

    def create_round2_candidates(self, candidates, total_votes):
        """Creează candidații în baza de date pentru turul 2"""
        created_count = 0
        
        for i, candidate_data in enumerate(candidates):
            # Calculează procentajul
            percentage = (candidate_data['vote_count'] / total_votes * 100) if total_votes > 0 else 0
            
            # Verifică dacă candidatul există deja
            existing = PresidentialRound2Candidate.objects.filter(
                name=candidate_data['candidate__name'],
                party=candidate_data['candidate__party']
            ).first()
            
            if existing:
                # Actualizează candidatul existent
                existing.round1_votes = candidate_data['vote_count']
                existing.round1_percentage = round(percentage, 2)
                existing.order_nr = i + 1
                existing.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Actualizat: {existing.name} - {existing.round1_votes} voturi ({existing.round1_percentage}%)'
                    )
                )
            else:
                # Creează candidat nou
                new_candidate = PresidentialRound2Candidate.objects.create(
                    name=candidate_data['candidate__name'],
                    party=candidate_data['candidate__party'],
                    photo_url=candidate_data['candidate__photo_url'] or '',
                    description=candidate_data['candidate__description'] or '',
                    order_nr=i + 1,
                    round1_votes=candidate_data['vote_count'],
                    round1_percentage=round(percentage, 2)
                )
                created_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Creat: {new_candidate.name} - {new_candidate.round1_votes} voturi ({new_candidate.round1_percentage}%)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Procesul s-a finalizat cu succes! {created_count} candidați noi creați pentru turul 2.'
            )
        )