from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import VoteResult
from vote.models import (
    VoteSettings, PresidentialVote, PresidentialRound2Vote, LocalVote, ParliamentaryVote,
    PresidentialCandidate, PresidentialRound2Candidate, ParliamentaryParty, LocalCandidate
)
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class VoteResultsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Returnează rezultatele voturilor"""
        # Obține parametrii din query
        location = request.query_params.get('location', 'romania')  # romania sau strainatate
        round_type = request.query_params.get('round', 'tur1_2024')  # tur1_2024, tur2_2024, tur_activ
        
        # Determină tipul de vot și perioada
        vote_type, start_date, end_date = self.get_vote_parameters(round_type)
        
        if not vote_type:
            return Response({
                'error': 'Tip de rundă invalid'
            }, status=400)
        
        # Pentru turul activ, calculăm rezultatele din datele reale de vot
        if round_type == 'tur_activ':
            return self.get_live_results(location, vote_type, start_date, end_date)
        
        # Pentru tururile istorice, folosim rezultatele preîncărcate sau calculăm din voturile istorice
        return self.get_historical_results(location, vote_type, start_date, end_date, round_type)
    
    def get_live_results(self, location, vote_type, start_date, end_date):
        """Calculează rezultatele live din voturile reale folosind candidații din vote app"""
        
        # Determină modelul de vot pe baza tipului
        if vote_type == 'prezidentiale':
            vote_model = PresidentialVote
            candidate_model = PresidentialCandidate
        elif vote_type == 'prezidentiale_tur2':
            vote_model = PresidentialRound2Vote
            candidate_model = PresidentialRound2Candidate
        elif vote_type == 'locale':
            vote_model = LocalVote
            candidate_model = LocalCandidate
        elif vote_type == 'parlamentare':
            vote_model = ParliamentaryVote
            candidate_model = ParliamentaryParty
        else:
            return Response({'error': f'Tip de vot nesuportat: {vote_type}'}, status=400)
        
        # Construiește query-ul de bază pentru voturi
        base_query = vote_model.objects.all()
        
        # Filtrează pe perioada de timp dacă există
        if start_date and end_date:
            base_query = base_query.filter(
                vote_datetime__gte=start_date,
                vote_datetime__lte=end_date
            )
        
        # Obține toate voturile cu candidații
        votes = base_query.select_related('user')
        if vote_type in ['prezidentiale', 'prezidentiale_tur2', 'locale']:
            votes = votes.select_related('candidate')
        elif vote_type == 'parlamentare':
            votes = votes.select_related('party')
        
        # Calculează rezultatele din voturile reale
        results = {
            'round_info': {
                'round_type': 'tur_activ',
                'location': location,
                'vote_type': vote_type,
                'period': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            },
            'total_votes': votes.count(),
            'results': self.calculate_real_vote_results(votes, vote_type),
            'vote_progression': self.calculate_vote_progression(votes, start_date) if start_date else [],
            'winner': self.determine_winner_from_votes(votes, vote_type),
            'is_final': self.is_voting_finished(start_date, end_date),
            'real_time_data': True
        }
        
        return Response(results)
    
    def calculate_real_vote_results(self, votes, vote_type):
        """Calculează rezultatele reale din voturile din baza de date"""
        total_votes = votes.count()
        
        if total_votes == 0:
            return []
        
        if vote_type == 'prezidentiale':
            return self.calculate_presidential_results_from_votes(votes, total_votes)
        elif vote_type == 'prezidentiale_tur2':
            return self.calculate_presidential_round2_results_from_votes(votes, total_votes)
        elif vote_type == 'parlamentare':
            return self.calculate_parliamentary_results_from_votes(votes, total_votes)
        elif vote_type == 'locale':
            return self.calculate_local_results_from_votes(votes, total_votes)
        
        return []
    
    def calculate_presidential_results_from_votes(self, votes, total_votes):
        """Calculează rezultatele prezidențiale din voturile reale"""
        # Grupează voturile pe candidați
        candidate_votes = votes.values(
            'candidate__id',
            'candidate__name', 
            'candidate__party',
            'candidate__order_nr'
        ).annotate(
            vote_count=Count('id')
        ).order_by('-vote_count')
        
        results = []
        for result in candidate_votes:
            if result['candidate__name']:  # Evită candidații NULL
                percentage = (result['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                results.append({
                    'candidate_id': result['candidate__id'],
                    'candidate_number': result['candidate__order_nr'] or 0,
                    'candidate_name': result['candidate__name'],
                    'party': result['candidate__party'] or 'Independent',
                    'votes': result['vote_count'],
                    'percentage': round(percentage, 2)
                })
        
        return results
    
    def calculate_presidential_round2_results_from_votes(self, votes, total_votes):
        """Calculează rezultatele turul 2 prezidențial din voturile reale"""
        # Similar cu prezidențialele, dar folosind PresidentialRound2Candidate
        candidate_votes = votes.values(
            'candidate__id',
            'candidate__name', 
            'candidate__party',
            'candidate__order_nr',
            'candidate__round1_votes',
            'candidate__round1_percentage'
        ).annotate(
            vote_count=Count('id')
        ).order_by('-vote_count')
        
        results = []
        for result in candidate_votes:
            if result['candidate__name']:
                percentage = (result['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                results.append({
                    'candidate_id': result['candidate__id'],
                    'candidate_number': result['candidate__order_nr'] or 0,
                    'candidate_name': result['candidate__name'],
                    'party': result['candidate__party'] or 'Independent',
                    'votes': result['vote_count'],
                    'percentage': round(percentage, 2),
                    'round1_votes': result['candidate__round1_votes'] or 0,
                    'round1_percentage': result['candidate__round1_percentage'] or 0
                })
        
        return results
    
    def calculate_parliamentary_results_from_votes(self, votes, total_votes):
        """Calculează rezultatele parlamentare din voturile reale"""
        party_votes = votes.values(
            'party__id',
            'party__name',
            'party__abbreviation',
            'party__order_nr'
        ).annotate(
            vote_count=Count('id')
        ).order_by('-vote_count')
        
        results = []
        for result in party_votes:
            if result['party__name']:
                percentage = (result['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                results.append({
                    'party_id': result['party__id'],
                    'party_number': result['party__order_nr'] or 0,
                    'party_name': result['party__name'],
                    'abbreviation': result['party__abbreviation'] or '',
                    'votes': result['vote_count'],
                    'percentage': round(percentage, 2)
                })
        
        return results
    
    def calculate_local_results_from_votes(self, votes, total_votes):
        """Calculează rezultatele locale din voturile reale"""
        # Grupează pe județe
        counties = votes.values_list('candidate__county', flat=True).distinct()
        
        results = []
        for county in counties:
            if county:
                county_votes = votes.filter(candidate__county=county)
                county_total = county_votes.count()
                
                if county_total > 0:
                    candidate_votes = county_votes.values(
                        'candidate__id',
                        'candidate__name',
                        'candidate__party',
                        'candidate__position'
                    ).annotate(
                        vote_count=Count('id')
                    ).order_by('-vote_count')
                    
                    candidates = []
                    for result in candidate_votes:
                        if result['candidate__name']:
                            percentage = (result['vote_count'] / county_total * 100)
                            candidates.append({
                                'candidate_id': result['candidate__id'],
                                'candidate_name': result['candidate__name'],
                                'party': result['candidate__party'] or 'Independent',
                                'position': result['candidate__position'] or 'primar',
                                'votes': result['vote_count'],
                                'percentage': round(percentage, 2)
                            })
                    
                    results.append({
                        'county': county,
                        'total_votes': county_total,
                        'candidates': candidates
                    })
        
        return results
    
    def determine_winner_from_votes(self, votes, vote_type):
        """Determină câștigătorul din voturile reale"""
        total_votes = votes.count()
        
        if total_votes == 0:
            return None
        
        if vote_type in ['prezidentiale', 'prezidentiale_tur2']:
            winner = votes.values(
                'candidate__name',
                'candidate__party'
            ).annotate(
                vote_count=Count('id')
            ).order_by('-vote_count').first()
            
            if winner and winner['candidate__name']:
                percentage = (winner['vote_count'] / total_votes * 100)
                return {
                    'type': 'candidate',
                    'name': winner['candidate__name'],
                    'party': winner['candidate__party'] or 'Independent',
                    'votes': winner['vote_count'],
                    'percentage': round(percentage, 2)
                }
        
        elif vote_type == 'parlamentare':
            winner = votes.values(
                'party__name',
                'party__abbreviation'
            ).annotate(
                vote_count=Count('id')
            ).order_by('-vote_count').first()
            
            if winner and winner['party__name']:
                percentage = (winner['vote_count'] / total_votes * 100)
                return {
                    'type': 'party',
                    'name': winner['party__name'],
                    'abbreviation': winner['party__abbreviation'] or '',
                    'votes': winner['vote_count'],
                    'percentage': round(percentage, 2)
                }
        
        return None
    
    def get_historical_results(self, location, vote_type, start_date, end_date, round_type):
        """Returnează rezultatele istorice"""
        
        # Încearcă să folosești rezultatele din VoteResult dacă există
        historical_results = VoteResult.objects.filter(
            location_type=location,
            vote_type=vote_type
        )
        
        if start_date and end_date:
            historical_results = historical_results.filter(
                vote_datetime__gte=start_date,
                vote_datetime__lte=end_date
            )
        
        # Dacă nu există rezultate în VoteResult, calculează din voturile istorice
        if not historical_results.exists():
            return self.calculate_from_historical_votes(location, vote_type, start_date, end_date, round_type)
        
        # Calculează rezultatele din VoteResult
        results = {
            'round_info': {
                'round_type': round_type,
                'location': location,
                'vote_type': vote_type,
                'period': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            },
            'total_votes': historical_results.count(),
            'results': self.get_vote_results_from_vote_result(historical_results, vote_type),
            'vote_progression': self.get_vote_progression(historical_results, start_date) if start_date else [],
            'winner': self.get_historical_winner_from_vote_result(historical_results, vote_type),
            'is_final': True,
            'real_time_data': False
        }
        
        return Response(results)
    
    def calculate_from_historical_votes(self, location, vote_type, start_date, end_date, round_type):
        """Calculează din voturile istorice dacă nu există în VoteResult"""
        
        # Folosește aceeași logică ca pentru live, dar cu filtru pe perioada istorică
        if vote_type == 'prezidentiale':
            vote_model = PresidentialVote
        elif vote_type == 'prezidentiale_tur2':
            vote_model = PresidentialRound2Vote
        elif vote_type == 'locale':
            vote_model = LocalVote
        elif vote_type == 'parlamentare':
            vote_model = ParliamentaryVote
        else:
            return Response({'error': f'Tip de vot nesuportat: {vote_type}'}, status=400)
        
        # Filtrează voturile pe perioada istorică
        historical_votes = vote_model.objects.all()
        if start_date and end_date:
            historical_votes = historical_votes.filter(
                vote_datetime__gte=start_date,
                vote_datetime__lte=end_date
            )
        
        # Calculează rezultatele
        results = {
            'round_info': {
                'round_type': round_type,
                'location': location,
                'vote_type': vote_type,
                'period': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            },
            'total_votes': historical_votes.count(),
            'results': self.calculate_real_vote_results(historical_votes, vote_type),
            'vote_progression': self.calculate_vote_progression(historical_votes, start_date) if start_date else [],
            'winner': self.determine_winner_from_votes(historical_votes, vote_type),
            'is_final': True,
            'real_time_data': False
        }
        
        return Response(results)
    
    def get_vote_results_from_vote_result(self, query, vote_type):
        """Calculează rezultatele din VoteResult"""
        if vote_type == 'prezidentiale':
            return self.get_presidential_results_from_vote_result(query)
        elif vote_type == 'prezidentiale_tur2':
            return self.get_presidential_round2_results_from_vote_result(query)
        elif vote_type == 'parlamentare':
            return self.get_parliamentary_results_from_vote_result(query)
        elif vote_type == 'locale':
            return self.get_local_results_from_vote_result(query)
        
        return []
    
    def get_presidential_results_from_vote_result(self, query):
        """Obține rezultatele prezidențiale din VoteResult"""
        results = query.filter(
            presidential_candidate__isnull=False
        ).values(
            'presidential_candidate__id',
            'presidential_candidate__name',
            'presidential_candidate__party',
            'presidential_candidate__order_nr'
        ).annotate(
            votes=Count('id')
        ).order_by('-votes')
        
        total_votes = query.filter(presidential_candidate__isnull=False).count()
        
        formatted_results = []
        for result in results:
            percentage = (result['votes'] / total_votes * 100) if total_votes > 0 else 0
            formatted_results.append({
                'candidate_id': result['presidential_candidate__id'],
                'candidate_number': result['presidential_candidate__order_nr'] or 0,
                'candidate_name': result['presidential_candidate__name'],
                'party': result['presidential_candidate__party'] or 'Independent',
                'votes': result['votes'],
                'percentage': round(percentage, 2)
            })
        
        return formatted_results
    
    def get_presidential_round2_results_from_vote_result(self, query):
        """Obține rezultatele turul 2 din VoteResult"""
        results = query.filter(
            presidential_round2_candidate__isnull=False
        ).values(
            'presidential_round2_candidate__id',
            'presidential_round2_candidate__name',
            'presidential_round2_candidate__party',
            'presidential_round2_candidate__order_nr',
            'presidential_round2_candidate__round1_votes',
            'presidential_round2_candidate__round1_percentage'
        ).annotate(
            votes=Count('id')
        ).order_by('-votes')
        
        total_votes = query.filter(presidential_round2_candidate__isnull=False).count()
        
        formatted_results = []
        for result in results:
            percentage = (result['votes'] / total_votes * 100) if total_votes > 0 else 0
            formatted_results.append({
                'candidate_id': result['presidential_round2_candidate__id'],
                'candidate_number': result['presidential_round2_candidate__order_nr'] or 0,
                'candidate_name': result['presidential_round2_candidate__name'],
                'party': result['presidential_round2_candidate__party'] or 'Independent',
                'votes': result['votes'],
                'percentage': round(percentage, 2),
                'round1_votes': result['presidential_round2_candidate__round1_votes'] or 0,
                'round1_percentage': result['presidential_round2_candidate__round1_percentage'] or 0
            })
        
        return formatted_results
    
    def get_parliamentary_results_from_vote_result(self, query):
        """Obține rezultatele parlamentare din VoteResult"""
        results = query.filter(
            parliamentary_party__isnull=False
        ).values(
            'parliamentary_party__id',
            'parliamentary_party__name',
            'parliamentary_party__abbreviation',
            'parliamentary_party__order_nr'
        ).annotate(
            votes=Count('id')
        ).order_by('-votes')
        
        total_votes = query.filter(parliamentary_party__isnull=False).count()
        
        formatted_results = []
        for result in results:
            percentage = (result['votes'] / total_votes * 100) if total_votes > 0 else 0
            formatted_results.append({
                'party_id': result['parliamentary_party__id'],
                'party_number': result['parliamentary_party__order_nr'] or 0,
                'party_name': result['parliamentary_party__name'],
                'abbreviation': result['parliamentary_party__abbreviation'] or '',
                'votes': result['votes'],
                'percentage': round(percentage, 2)
            })
        
        return formatted_results
    
    def get_local_results_from_vote_result(self, query):
        """Obține rezultatele locale din VoteResult"""
        counties = query.filter(
            local_candidate__isnull=False
        ).values_list('county', flat=True).distinct()
        
        results = []
        for county in counties:
            if county:
                county_query = query.filter(county=county, local_candidate__isnull=False)
                county_results = county_query.values(
                    'local_candidate__id',
                    'local_candidate__name',
                    'local_candidate__party',
                    'local_candidate__position'
                ).annotate(
                    votes=Count('id')
                ).order_by('-votes')
                
                county_total = county_query.count()
                
                candidates = []
                for result in county_results:
                    percentage = (result['votes'] / county_total * 100) if county_total > 0 else 0
                    candidates.append({
                        'candidate_id': result['local_candidate__id'],
                        'candidate_name': result['local_candidate__name'],
                        'party': result['local_candidate__party'] or 'Independent',
                        'position': result['local_candidate__position'],
                        'votes': result['votes'],
                        'percentage': round(percentage, 2)
                    })
                
                results.append({
                    'county': county,
                    'total_votes': county_total,
                    'candidates': candidates
                })
        
        return results
    
    def get_historical_winner_from_vote_result(self, query, vote_type):
        """Obține câștigătorul din VoteResult"""
        if vote_type == 'prezidentiale':
            winner = query.filter(
                presidential_candidate__isnull=False
            ).values(
                'presidential_candidate__name',
                'presidential_candidate__party'
            ).annotate(
                votes=Count('id')
            ).order_by('-votes').first()
            
            if winner:
                total_votes = query.filter(presidential_candidate__isnull=False).count()
                percentage = (winner['votes'] / total_votes * 100) if total_votes > 0 else 0
                return {
                    'type': 'candidate',
                    'name': winner['presidential_candidate__name'],
                    'party': winner['presidential_candidate__party'] or 'Independent',
                    'votes': winner['votes'],
                    'percentage': round(percentage, 2)
                }
        
        elif vote_type == 'prezidentiale_tur2':
            winner = query.filter(
                presidential_round2_candidate__isnull=False
            ).values(
                'presidential_round2_candidate__name',
                'presidential_round2_candidate__party'
            ).annotate(
                votes=Count('id')
            ).order_by('-votes').first()
            
            if winner:
                total_votes = query.filter(presidential_round2_candidate__isnull=False).count()
                percentage = (winner['votes'] / total_votes * 100) if total_votes > 0 else 0
                return {
                    'type': 'candidate',
                    'name': winner['presidential_round2_candidate__name'],
                    'party': winner['presidential_round2_candidate__party'] or 'Independent',
                    'votes': winner['votes'],
                    'percentage': round(percentage, 2)
                }
        
        elif vote_type == 'parlamentare':
            winner = query.filter(
                parliamentary_party__isnull=False
            ).values(
                'parliamentary_party__name',
                'parliamentary_party__abbreviation'
            ).annotate(
                votes=Count('id')
            ).order_by('-votes').first()
            
            if winner:
                total_votes = query.filter(parliamentary_party__isnull=False).count()
                percentage = (winner['votes'] / total_votes * 100) if total_votes > 0 else 0
                return {
                    'type': 'party',
                    'name': winner['parliamentary_party__name'],
                    'abbreviation': winner['parliamentary_party__abbreviation'] or '',
                    'votes': winner['votes'],
                    'percentage': round(percentage, 2)
                }
        
        return None
    
    def calculate_vote_progression(self, votes, start_date):
        """Calculează progresiunea voturilor pe intervale de timp"""
        if not start_date:
            return []
        
        end_date = start_date + timedelta(hours=14)
        intervals = []
        current_time = start_date
        
        while current_time < end_date:
            interval_end = current_time + timedelta(minutes=30)  # Intervale de 30 minute
            
            votes_in_interval = votes.filter(
                vote_datetime__gte=current_time,
                vote_datetime__lt=interval_end
            ).count()
            
            intervals.append({
                'time': current_time.strftime('%H:%M'),
                'votes': votes_in_interval,
                'cumulative': sum(interval['votes'] for interval in intervals) + votes_in_interval
            })
            
            current_time = interval_end
        
        return intervals
    
    def get_vote_progression(self, query, start_date):
        """Obține progresiunea voturilor din VoteResult"""
        return self.calculate_vote_progression(query, start_date)
    
    def is_voting_finished(self, start_date, end_date):
        """Verifică dacă votarea s-a terminat"""
        if not end_date:
            return False
        return timezone.now() >= end_date
    
    def get_vote_parameters(self, round_type):
        """Determină parametrii votului pe baza tipului de rundă"""
        now = timezone.now()
        
        if round_type == 'tur1_2024':
            return 'prezidentiale', \
                   timezone.make_aware(datetime(2024, 12, 8, 7, 0, 0)), \
                   timezone.make_aware(datetime(2024, 12, 8, 21, 0, 0))
        
        elif round_type == 'tur2_2024':
            return 'prezidentiale_tur2', \
                   timezone.make_aware(datetime(2024, 12, 22, 7, 0, 0)), \
                   timezone.make_aware(datetime(2024, 12, 22, 21, 0, 0))
        
        elif round_type == 'tur_activ':
            # Verifică ce vot este activ acum
            active_vote = VoteSettings.objects.filter(
                is_active=True,
                start_datetime__lte=now,
                end_datetime__gte=now
            ).first()
            
            if active_vote:
                return active_vote.vote_type, active_vote.start_datetime, active_vote.end_datetime
            else:
                # Dacă nu există vot activ, returnează date pentru ultimele 24 ore
                return 'prezidentiale', now - timedelta(hours=24), now
        
        return None, None, None

class LiveResultsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Returnează rezultate live pentru votul activ"""
        now = timezone.now()
        
        # Verifică dacă există un vot activ
        active_vote = VoteSettings.objects.filter(
            is_active=True,
            start_datetime__lte=now,
            end_datetime__gte=now
        ).first()
        
        if not active_vote:
            return Response({
                'error': 'Nu există un vot activ în acest moment'
            }, status=404)
        
        # Determină modelul de vot pe baza tipului
        if active_vote.vote_type == 'prezidentiale':
            vote_model = PresidentialVote
        elif active_vote.vote_type == 'prezidentiale_tur2':
            vote_model = PresidentialRound2Vote
        elif active_vote.vote_type == 'locale':
            vote_model = LocalVote
        elif active_vote.vote_type == 'parlamentare':
            vote_model = ParliamentaryVote
        else:
            return Response({
                'error': f'Tip de vot nesuportat: {active_vote.vote_type}'
            }, status=400)
        
        # Obține rezultate pentru ultimele 30 de minute
        last_30_min = now - timedelta(minutes=30)
        
        recent_votes = vote_model.objects.filter(
            vote_datetime__gte=last_30_min
        )
        
        all_votes_today = vote_model.objects.filter(
            vote_datetime__gte=active_vote.start_datetime
        )
        
        # Calculează rata de actualizare a rezultatelor
        result_updates = []
        for i in range(30):
            minute_start = last_30_min + timedelta(minutes=i)
            minute_end = minute_start + timedelta(minutes=1)
            
            votes_this_minute = recent_votes.filter(
                vote_datetime__gte=minute_start,
                vote_datetime__lt=minute_end
            ).count()
            
            result_updates.append({
                'minute': minute_start.strftime('%H:%M'),
                'new_votes': votes_this_minute
            })
        
        # Calculează timpul rămas până la închiderea votării
        time_remaining = (active_vote.end_datetime - now).total_seconds()
        
        return Response({
            'active_vote_type': active_vote.vote_type,
            'vote_start': active_vote.start_datetime,
            'vote_end': active_vote.end_datetime,
            'time_remaining': max(0, int(time_remaining)),
            'total_votes_today': all_votes_today.count(),
            'votes_last_30_min': recent_votes.count(),
            'result_updates': result_updates,
            'is_final': time_remaining <= 0
        })