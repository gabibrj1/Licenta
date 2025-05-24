from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import VotingPresence, PresenceSummary
from vote.models import VoteSettings, PresidentialVote, PresidentialRound2Vote, LocalVote, ParliamentaryVote
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class VotingPresenceView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Returnează datele de prezență la vot"""
        location = request.query_params.get('location', 'romania')
        round_type = request.query_params.get('round', 'tur1_2024')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        vote_type, start_date, end_date = self.get_vote_parameters(round_type)
        
        if not vote_type:
            return Response({'error': 'Tip de rundă invalid'}, status=400)
        
        if round_type == 'tur_activ':
            return self.get_live_presence(location, vote_type, start_date, end_date, page, page_size)
        
        return self.get_historical_presence(location, vote_type, start_date, end_date, page, page_size)
    
    def get_live_presence(self, location, vote_type, start_date, end_date, page, page_size):
        """Calculează prezența live"""
        
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
        
        votes_query = vote_model.objects.all()
        
        if start_date and end_date:
            votes_query = votes_query.filter(
                vote_datetime__gte=start_date,
                vote_datetime__lte=end_date
            )
        
        total_votes = votes_query.count()
        county_presence = self.calculate_live_county_presence(votes_query, location)
        urban_rural_data = self.get_urban_rural_comparison(location, vote_type, start_date, end_date)
        
        # Paginare
        total_counties = len(county_presence)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_counties = county_presence[start_idx:end_idx]
        
        # Statistici generale pentru live - diferite pentru România vs Străinătate
        if location == 'romania':
            general_stats = {
                'registered_permanent': 17988218,
                'total_voters': total_votes,
                'voters_permanent': total_votes,
                'voters_supplementary': 0,
                'voters_mobile': 0,
                'participation_rate': (total_votes / 17988218 * 100) if total_votes > 0 else 0
            }
        else:  # străinătate
            general_stats = {
                'registered_permanent': 0,
                'total_voters': total_votes,
                'voters_permanent': 0,
                'voters_supplementary': total_votes,
                'voters_correspondence': 0,
                'participation_rate': 0  # Nu se calculează pentru străinătate
            }
        
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
            'general_stats': general_stats,
            'urban_rural': urban_rural_data,
            'counties': paginated_counties,
            'pagination': {
                'current_page': page,
                'total_pages': (total_counties + page_size - 1) // page_size,
                'total_counties': total_counties,
                'page_size': page_size
            },
            'is_live': True,
            'last_updated': timezone.now().isoformat()
        }
        
        return Response(results)
    
    def calculate_live_county_presence(self, votes_query, location):
        """Calculează prezența pe județe/țări din voturile live"""
        county_stats = []
        total_votes = votes_query.count()
        
        if location == 'romania':
            # Pentru România - județul din profil sau distribuție pe județe
            historic_counties = VotingPresence.objects.filter(
                location_type='romania'
            ).values_list('county', flat=True).distinct()
            
            for county in historic_counties:
                if county != 'SR':  # Exclude SR din România
                    county_votes = max(1, total_votes // 42)
                    
                    county_stats.append({
                        'county': county,
                        'total_voters': county_votes,
                        'registered_permanent': 400000,
                        'participation_rate': (county_votes / 400000 * 100),
                        'urban_voters': county_votes // 2,
                        'rural_voters': county_votes // 2,
                        'men_voters': county_votes // 2,
                        'women_voters': county_votes // 2
                    })
        
        else:  # străinătate
            # Pentru străinătate - țările din datele istorice
            countries = VotingPresence.objects.filter(
                location_type='strainatate'
            ).values_list('county', flat=True).distinct()
            
            for country in countries:
                country_votes = max(1, total_votes // len(countries))
                
                county_stats.append({
                    'county': country,
                    'total_voters': country_votes,
                    'registered_permanent': 0,  # 0 pentru străinătate
                    'participation_rate': 0,  # Nu se calculează pentru străinătate
                    'urban_voters': country_votes,
                    'rural_voters': 0,
                    'men_voters': country_votes // 2,
                    'women_voters': country_votes // 2
                })
        
        return sorted(county_stats, key=lambda x: x['total_voters'], reverse=True)
    
    def get_historical_presence(self, location, vote_type, start_date, end_date, page, page_size):
        """Returnează prezența istorică"""
        
        presence_query = VotingPresence.objects.filter(
            vote_type=vote_type,
            location_type=location
        )
        
        if start_date and end_date:
            presence_query = presence_query.filter(
                vote_datetime__gte=start_date,
                vote_datetime__lte=end_date
            )
        
        general_stats = self.calculate_general_stats(presence_query, vote_type, location)
        urban_rural_data = self.get_urban_rural_comparison(location, vote_type, start_date, end_date)
        county_data = self.get_county_presence_data(presence_query, page, page_size)
        
        results = {
            'round_info': {
                'round_type': vote_type,
                'location': location,
                'vote_type': vote_type,
                'period': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            },
            'general_stats': general_stats,
            'urban_rural': urban_rural_data,
            'counties': county_data['counties'],
            'pagination': county_data['pagination'],
            'is_live': False,
            'last_updated': timezone.now().isoformat()
        }
        
        return Response(results)
    
    def calculate_general_stats(self, presence_query, vote_type, location):
        """Calculează statisticile generale"""
        
        if vote_type == 'prezidentiale' and location == 'romania':
            return {
                'registered_permanent': 17988218,
                'voters_permanent': 8416686,
                'voters_supplementary': 3127125,
                'voters_mobile': 94916,
                'total_voters': 11641866,
                'participation_rate': 64.7
            }
        elif vote_type == 'prezidentiale' and location == 'strainatate':
            return {
                'sections_count': 966,
                'registered_permanent': 0,
                'voters_permanent': 0,
                'voters_supplementary': 1642319,
                'voters_correspondence': 3139,
                'total_voters': 1645458,
                'participation_rate': 0  # Nu se calculează pentru străinătate
            }
        elif vote_type == 'prezidentiale_tur2':
            return {
                'registered_permanent': 17988218 if location == 'romania' else 0,
                'voters_permanent': 0,
                'voters_supplementary': 0,
                'voters_mobile': 0,
                'voters_correspondence': 0 if location == 'romania' else 0,
                'total_voters': 0,
                'participation_rate': 0,
                'note': 'Turul 2 a fost anulat'
            }
        else:
            # Calculează din datele reale
            aggregated = presence_query.aggregate(
                total_registered=Sum('registered_permanent'),
                total_voters=Sum('voters_permanent') + Sum('voters_supplementary') + Sum('voters_mobile'),
                total_permanent=Sum('voters_permanent'),
                total_supplementary=Sum('voters_supplementary'),
                total_mobile=Sum('voters_mobile')
            )
            
            total_voters = aggregated['total_voters'] or 0
            total_registered = aggregated['total_registered'] or 1
            
            stats = {
                'registered_permanent': total_registered,
                'voters_permanent': aggregated['total_permanent'] or 0,
                'voters_supplementary': aggregated['total_supplementary'] or 0,
                'total_voters': total_voters,
                'participation_rate': (total_voters / total_registered * 100) if total_registered > 0 else 0
            }
            
            if location == 'strainatate':
                stats['voters_correspondence'] = aggregated['total_mobile'] or 0
                stats['sections_count'] = presence_query.count()
            else:
                stats['voters_mobile'] = aggregated['total_mobile'] or 0
            
            return stats
    
    def get_urban_rural_comparison(self, location, vote_type, start_date, end_date):
        """Calculează comparația urban/rural"""
        
        query = VotingPresence.objects.filter(
            vote_type=vote_type,
            location_type=location
        )
        
        if start_date and end_date:
            query = query.filter(vote_datetime__gte=start_date, vote_datetime__lte=end_date)
        
        urban_data = query.filter(environment='urban').aggregate(
            total_voters=Sum('voters_permanent') + Sum('voters_supplementary') + Sum('voters_mobile'),
            total_registered=Sum('registered_permanent')
        )
        
        rural_data = query.filter(environment='rural').aggregate(
            total_voters=Sum('voters_permanent') + Sum('voters_supplementary') + Sum('voters_mobile'),
            total_registered=Sum('registered_permanent')
        )
        
        urban_voters = urban_data['total_voters'] or 0
        rural_voters = rural_data['total_voters'] or 0
        urban_registered = urban_data['total_registered'] or 1
        rural_registered = rural_data['total_registered'] or 1
        
        return {
            'urban': {
                'voters': urban_voters,
                'registered': urban_registered,
                'participation_rate': (urban_voters / urban_registered * 100) if urban_registered > 0 else 0
            },
            'rural': {
                'voters': rural_voters,
                'registered': rural_registered,
                'participation_rate': (rural_voters / rural_registered * 100) if rural_registered > 0 else 0
            },
            'comparison': {
                'urban_percentage': (urban_voters / (urban_voters + rural_voters) * 100) if (urban_voters + rural_voters) > 0 else 0,
                'rural_percentage': (rural_voters / (urban_voters + rural_voters) * 100) if (urban_voters + rural_voters) > 0 else 0
            }
        }
    
    def get_county_presence_data(self, presence_query, page, page_size):
        """Obține datele pe județe/țări cu paginare"""
        
        # Încearcă să folosească PresenceSummary
        if presence_query.exists():
            first_record = presence_query.first()
            county_summaries = PresenceSummary.objects.filter(
                vote_type=first_record.vote_type,
                location_type=first_record.location_type
            ).order_by('-total_voters')
        else:
            county_summaries = PresenceSummary.objects.none()
        
        # Dacă nu există sumare, calculează dinamic
        if not county_summaries.exists():
            county_summaries = self.calculate_county_summaries_dynamic(presence_query)
        
        # Paginare
        total_counties = len(county_summaries)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        if isinstance(county_summaries, list):
            paginated_counties = county_summaries[start_idx:end_idx]
        else:
            paginated_counties = list(county_summaries[start_idx:end_idx])
        
        # Formatează datele
        counties_data = []
        for summary in paginated_counties:
            if isinstance(summary, dict):
                counties_data.append(summary)
            else:
                counties_data.append({
                    'county': summary.county,
                    'total_voters': summary.total_voters,
                    'registered_permanent': summary.total_registered,
                    'participation_rate': summary.participation_rate,
                    'urban_voters': summary.urban_voters,
                    'rural_voters': summary.rural_voters,
                    'men_voters': summary.total_men,
                    'women_voters': summary.total_women
                })
        
        return {
            'counties': counties_data,
            'pagination': {
                'current_page': page,
                'total_pages': (total_counties + page_size - 1) // page_size,
                'total_counties': total_counties,
                'page_size': page_size
            }
        }
    
    def calculate_county_summaries_dynamic(self, presence_query):
        """Calculează sumarele dinamic"""
        
        counties = presence_query.values_list('county', flat=True).distinct()
        summaries = []
        
        for county in counties:
            county_data = presence_query.filter(county=county).aggregate(
                total_registered=Sum('registered_permanent'),
                total_voters=Sum('voters_permanent') + Sum('voters_supplementary') + Sum('voters_mobile'),
                total_men=Sum('men_18_24') + Sum('men_25_34') + Sum('men_35_44') + Sum('men_45_64') + Sum('men_65_plus'),
                total_women=Sum('women_18_24') + Sum('women_25_34') + Sum('women_35_44') + Sum('women_45_64') + Sum('women_65_plus')
            )
            
            urban_rural = presence_query.filter(county=county).values('environment').annotate(
                voters=Sum('voters_permanent') + Sum('voters_supplementary') + Sum('voters_mobile')
            )
            
            urban_voters = 0
            rural_voters = 0
            for data in urban_rural:
                if data['environment'] == 'urban':
                    urban_voters = data['voters'] or 0
                else:
                    rural_voters = data['voters'] or 0
            
            total_voters = county_data['total_voters'] or 0
            total_registered = county_data['total_registered'] or 1
            
            summaries.append({
                'county': county,
                'total_voters': total_voters,
                'registered_permanent': total_registered,
                'participation_rate': (total_voters / total_registered * 100) if total_registered > 0 else 0,
                'urban_voters': urban_voters,
                'rural_voters': rural_voters,
                'men_voters': county_data['total_men'] or 0,
                'women_voters': county_data['total_women'] or 0
            })
        
        return sorted(summaries, key=lambda x: x['total_voters'], reverse=True)
    
    def get_vote_parameters(self, round_type):
        """Determină parametrii votului"""
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
            active_vote = VoteSettings.objects.filter(
                is_active=True,
                start_datetime__lte=now,
                end_datetime__gte=now
            ).first()
            
            if active_vote:
                return active_vote.vote_type, active_vote.start_datetime, active_vote.end_datetime
            else:
                return 'prezidentiale', now - timedelta(hours=24), now
        
        return None, None, None

class LivePresenceView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Returnează statistici live pentru prezența la vot"""
        now = timezone.now()
        
        active_vote = VoteSettings.objects.filter(
            is_active=True,
            start_datetime__lte=now,
            end_datetime__gte=now
        ).first()
        
        if not active_vote:
            return Response({
                'error': 'Nu există un vot activ în acest moment'
            }, status=404)
        
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
        
        all_votes_today = vote_model.objects.filter(
            vote_datetime__gte=active_vote.start_datetime
        )
        
        last_hour_votes = vote_model.objects.filter(
            vote_datetime__gte=now - timedelta(hours=1)
        )
        
        # Evoluția pe ore
        hourly_evolution = []
        current_hour = active_vote.start_datetime.replace(minute=0, second=0, microsecond=0)
        
        while current_hour < now:
            hour_end = current_hour + timedelta(hours=1)
            hour_votes = vote_model.objects.filter(
                vote_datetime__gte=current_hour,
                vote_datetime__lt=hour_end
            ).count()
            
            hourly_evolution.append({
                'hour': current_hour.strftime('%H:%M'),
                'votes': hour_votes,
                'cumulative': sum(h['votes'] for h in hourly_evolution) + hour_votes
            })
            
            current_hour = hour_end
        
        time_remaining = (active_vote.end_datetime - now).total_seconds()
        
        return Response({
            'active_vote_type': active_vote.vote_type,
            'vote_start': active_vote.start_datetime,
            'vote_end': active_vote.end_datetime,
            'time_remaining': max(0, int(time_remaining)),
            'total_votes_today': all_votes_today.count(),
            'votes_last_hour': last_hour_votes.count(),
            'hourly_evolution': hourly_evolution,
            'estimated_final_turnout': self.estimate_final_turnout(all_votes_today.count(), time_remaining),
            'is_final': time_remaining <= 0
        })
    
    def estimate_final_turnout(self, current_votes, time_remaining_seconds):
        """Estimează prezența finală"""
        if time_remaining_seconds <= 0:
            return current_votes
        
        hours_elapsed = 14 - (time_remaining_seconds / 3600)
        if hours_elapsed > 0:
            votes_per_hour = current_votes / hours_elapsed
            estimated_final = current_votes + (votes_per_hour * (time_remaining_seconds / 3600))
            return int(estimated_final)
        
        return current_votes