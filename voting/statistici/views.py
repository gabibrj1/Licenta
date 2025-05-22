from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import VoteStatistics
from vote.models import VoteSettings, PresidentialVote, PresidentialRound2Vote, LocalVote, ParliamentaryVote
from django.contrib.auth import get_user_model
import logging
import re
from datetime import date

logger = logging.getLogger(__name__)
User = get_user_model()

class VoteStatisticsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Returnează statisticile de vot"""
        # Obține parametrii din query
        location = request.query_params.get('location', 'romania')  # romania sau strainatate
        round_type = request.query_params.get('round', 'tur1_2024')  # tur1_2024, tur2_2024, tur_activ
        
        # Determină tipul de vot și perioada
        vote_type, start_date, end_date = self.get_vote_parameters(round_type)
        
        if not vote_type:
            return Response({
                'error': 'Tip de rundă invalid'
            }, status=400)
        
        # Pentru turul activ, calculăm statisticile din datele reale de vot
        if round_type == 'tur_activ':
            return self.get_live_statistics(location, vote_type, start_date, end_date)
        
        # Pentru tururile istorice, folosim logica existentă
        return self.get_historical_statistics(location, vote_type, start_date, end_date, round_type)
    
    def get_live_statistics(self, location, vote_type, start_date, end_date):
        """Calculează statisticile live din voturile reale"""
        
        # Determină modelul de vot pe baza tipului
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
        
        # Construiește query-ul de bază
        base_query = vote_model.objects.all()
        
        # Filtrează pe perioada de timp dacă există
        if start_date and end_date:
            base_query = base_query.filter(
                vote_datetime__gte=start_date,
                vote_datetime__lte=end_date
            )
        
        # Pentru demonstrație, nu filtrăm pe locație pentru că nu avem acest câmp în voturile reale
        # În practică, ai putea adăuga logica de filtrare pe județ/oraș
        
        # Obține toate voturile
        votes = base_query.select_related('user')
        
        # Calculează statisticile
        statistics = {
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
            'age_distribution': self.calculate_age_distribution_from_votes(votes),
            'gender_distribution': self.calculate_gender_distribution_from_votes(votes),
            'environment_distribution': self.calculate_environment_distribution_from_votes(votes),
            'hourly_turnout': self.calculate_hourly_turnout_from_votes(votes, start_date) if start_date else [],
            'real_time_data': True
        }
        
        return Response(statistics)
    
    def get_historical_statistics(self, location, vote_type, start_date, end_date, round_type):
        """Returnează statisticile istorice din tabela VoteStatistics"""
        
        # Filtrează datele din VoteStatistics
        base_query = VoteStatistics.objects.filter(
            location_type=location,
            vote_type=vote_type
        )
        
        if start_date and end_date:
            base_query = base_query.filter(
                vote_datetime__gte=start_date,
                vote_datetime__lte=end_date
            )
        
        # Calculează statisticile
        statistics = {
            'round_info': {
                'round_type': round_type,
                'location': location,
                'vote_type': vote_type,
                'period': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            },
            'total_votes': base_query.count(),
            'age_distribution': self.get_age_distribution(base_query),
            'gender_distribution': self.get_gender_distribution(base_query),
            'environment_distribution': self.get_environment_distribution(base_query),
            'hourly_turnout': self.get_hourly_turnout(base_query, start_date) if start_date else [],
            'real_time_data': False
        }
        
        return Response(statistics)
    
    def calculate_age_distribution_from_votes(self, votes):
        """Calculează distribuția pe vârstă din voturile reale"""
        age_groups = {'18-24': 0, '25-34': 0, '35-44': 0, '45-64': 0, '65+': 0}
        total_votes = 0
        
        for vote in votes:
            if vote.user and vote.user.cnp:
                age = self.calculate_age_from_cnp(vote.user.cnp)
                if age:
                    age_group = self.get_age_group(age)
                    if age_group in age_groups:
                        age_groups[age_group] += 1
                        total_votes += 1
        
        # Convertește în format pentru răspuns
        result = []
        for age_group, count in age_groups.items():
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            result.append({
                'age_group': age_group,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return result
    
    def calculate_gender_distribution_from_votes(self, votes):
        """Calculează distribuția pe gen din voturile reale"""
        gender_counts = {'M': 0, 'F': 0}
        total_votes = 0
        
        for vote in votes:
            if vote.user and vote.user.cnp:
                gender = self.get_gender_from_cnp(vote.user.cnp)
                if gender in gender_counts:
                    gender_counts[gender] += 1
                    total_votes += 1
        
        # Convertește în format pentru răspuns
        result = []
        for gender, count in gender_counts.items():
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            gender_name = 'Bărbați' if gender == 'M' else 'Femei'
            result.append({
                'gender': gender,
                'gender_name': gender_name,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return result
    
    def calculate_environment_distribution_from_votes(self, votes):
        """Calculează distribuția pe mediu din voturile reale"""
        env_counts = {'urban': 0, 'rural': 0}
        total_votes = 0
        
        for vote in votes:
            if vote.user and vote.user.address:
                environment = self.determine_environment_from_address(vote.user.address)
                if environment in env_counts:
                    env_counts[environment] += 1
                    total_votes += 1
        
        # Convertește în format pentru răspuns
        result = []
        for env, count in env_counts.items():
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            env_name = 'Urban' if env == 'urban' else 'Rural'
            result.append({
                'environment': env,
                'environment_name': env_name,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return result
    
    def calculate_hourly_turnout_from_votes(self, votes, start_date):
        """Calculează afluxul pe intervale de 10 minute din voturile reale"""
        if not start_date:
            return []
        
        # Calculează end_date dacă nu este furnizat
        end_date = start_date + timedelta(hours=14)  # Presupunem o zi de vot de 14 ore
        
        # Generează intervalele de 10 minute
        intervals = []
        current_time = start_date
        
        while current_time < end_date:
            interval_end = current_time + timedelta(minutes=10)
            
            # Calculează numărul de voturi în acest interval
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
    
    def calculate_age_from_cnp(self, cnp):
        """Calculează vârsta din CNP"""
        if not cnp or len(cnp) != 13:
            return None
            
        try:
            # Prima cifră determină secolul și genul
            first_digit = int(cnp[0])
            
            # Determinarea secolului conform algoritmului CNP românesc
            if first_digit in [1, 2]:
                century = 1900  # Născuți între 1900-1999
            elif first_digit in [3, 4]:
                century = 1800  # Născuți între 1800-1899  
            elif first_digit in [5, 6]:
                century = 2000  # Născuți între 2000-2099
            elif first_digit in [7, 8]:
                century = 1900  # Străini rezidenți născuți între 1900-1999
            elif first_digit == 9:
                century = 2000  # Străini născuți între 2000-2099
            else:
                return None  # Cazuri speciale
            
            # Extragerea datei de naștere
            year = century + int(cnp[1:3])
            month = int(cnp[3:5])
            day = int(cnp[5:7])
            
            # Verificarea validității datei
            if month < 1 or month > 12 or day < 1 or day > 31:
                return None
                
            birth_date = date(year, month, day)
            
            # Calcularea vârstei
            today = date.today()
            age = today.year - birth_date.year
            
            # Ajustează vârsta dacă ziua de naștere nu a trecut încă în anul curent
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            
            return age
            
        except (ValueError, TypeError):
            return None
    
    def get_gender_from_cnp(self, cnp):
        """Extrage genul din CNP"""
        if not cnp or len(cnp) != 13:
            return None
            
        try:
            first_digit = int(cnp[0])
            # Pentru români: 1,3,5 = bărbați, 2,4,6 = femei
            if first_digit % 2 == 1:
                return 'M'
            else:
                return 'F'
        except (ValueError, TypeError):
            return None
    
    def get_age_group(self, age):
        """Determină grupa de vârstă"""
        if age is None:
            return None
        elif 18 <= age <= 24:
            return '18-24'
        elif 25 <= age <= 34:
            return '25-34'
        elif 35 <= age <= 44:
            return '35-44'
        elif 45 <= age <= 64:
            return '45-64'
        elif age >= 65:
            return '65+'
        else:
            return None
    
    def determine_environment_from_address(self, address):
        """Determină mediul (urban/rural) din adresă"""
        if not address:
            return None
            
        address_lower = address.lower()
        
        # Cuvinte cheie pentru urban
        urban_keywords = ['municipiu', 'oraș', 'oras', 'municipiul', 'orasul', 'sector', 'sectorul']
        # Cuvinte cheie pentru rural
        rural_keywords = ['comună', 'comuna', 'sat', 'satul', 'cătun', 'catun', 'cătunul', 'catunul']
        
        # Verifică cuvintele cheie urbane
        for keyword in urban_keywords:
            if keyword in address_lower:
                return 'urban'
        
        # Verifică cuvintele cheie rurale
        for keyword in rural_keywords:
            if keyword in address_lower:
                return 'rural'
        
        # Default: considerăm urban dacă nu găsim indicatori clari
        return 'urban'
    
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
    
    # Metodele existente pentru statisticile istorice rămân neschimbate
    def get_age_distribution(self, query):
        """Calculează distribuția pe grupe de vârstă"""
        age_groups = query.values('age_group').annotate(
            count=Count('id')
        ).order_by('age_group')
        
        total = query.count()
        
        result = []
        for group in age_groups:
            percentage = (group['count'] / total * 100) if total > 0 else 0
            result.append({
                'age_group': group['age_group'],
                'count': group['count'],
                'percentage': round(percentage, 2)
            })
        
        return result
    
    def get_gender_distribution(self, query):
        """Calculează distribuția pe gen"""
        gender_stats = query.values('gender').annotate(
            count=Count('id')
        )
        
        total = query.count()
        
        result = []
        for stat in gender_stats:
            percentage = (stat['count'] / total * 100) if total > 0 else 0
            gender_name = 'Bărbați' if stat['gender'] == 'M' else 'Femei'
            result.append({
                'gender': stat['gender'],
                'gender_name': gender_name,
                'count': stat['count'],
                'percentage': round(percentage, 2)
            })
        
        return result
    
    def get_environment_distribution(self, query):
        """Calculează distribuția pe mediu (urban/rural)"""
        # Filtrează doar înregistrările care au informații despre mediu
        env_query = query.filter(environment__isnull=False)
        
        env_stats = env_query.values('environment').annotate(
            count=Count('id')
        )
        
        total = env_query.count()
        
        result = []
        for stat in env_stats:
            percentage = (stat['count'] / total * 100) if total > 0 else 0
            env_name = 'Urban' if stat['environment'] == 'urban' else 'Rural'
            result.append({
                'environment': stat['environment'],
                'environment_name': env_name,
                'count': stat['count'],
                'percentage': round(percentage, 2)
            })
        
        return result
    
    def get_hourly_turnout(self, query, start_date):
        """Calculează afluxul pe intervale de 10 minute"""
        if not start_date:
            return []
        
        # Calculează end_date dacă nu este furnizat
        end_date = start_date + timedelta(hours=14)  # Presupunem o zi de vot de 14 ore
        
        # Generează intervalele de 10 minute
        intervals = []
        current_time = start_date
        
        while current_time < end_date:
            interval_end = current_time + timedelta(minutes=10)
            
            # Calculează numărul de voturi în acest interval
            votes_in_interval = query.filter(
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

class LiveStatisticsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Returnează statistici live pentru votul activ"""
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
        
        # Obține statistici pentru ultimele 30 de minute
        last_30_min = now - timedelta(minutes=30)
        
        recent_votes = vote_model.objects.filter(
            vote_datetime__gte=last_30_min
        )
        
        all_votes_today = vote_model.objects.filter(
            vote_datetime__gte=active_vote.start_datetime
        )
        
        # Calculează rata de vot per minut
        vote_rate_data = []
        for i in range(30):
            minute_start = last_30_min + timedelta(minutes=i)
            minute_end = minute_start + timedelta(minutes=1)
            
            votes_this_minute = recent_votes.filter(
                vote_datetime__gte=minute_start,
                vote_datetime__lt=minute_end
            ).count()
            
            vote_rate_data.append({
                'minute': minute_start.strftime('%H:%M'),
                'votes': votes_this_minute
            })
        
        return Response({
            'active_vote_type': active_vote.vote_type,
            'vote_start': active_vote.start_datetime,
            'vote_end': active_vote.end_datetime,
            'total_votes_today': all_votes_today.count(),
            'votes_last_30_min': recent_votes.count(),
            'vote_rate_per_minute': vote_rate_data
        })