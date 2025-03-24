from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import VoteSettings
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import VotingSection, LocalCandidate
from django.db.models import Q
import re
from .models import LocalVote


# Replace this view in your vote/views.py file

class VoteSettingsView(APIView):
    permission_classes = [AllowAny]  # Allow any user to access vote settings, even unauthenticated
    
    def get(self, request):
        """Returnează setările actuale de vot și starea butonului"""
        now = timezone.now()
        
        # Verifică dacă există un vot activ programat pentru momentul curent
        active_vote = VoteSettings.objects.filter(
            is_active=True,
            start_datetime__lte=now,
            end_datetime__gte=now
        ).first()
        
        if active_vote:
            return Response({
                'is_vote_active': True,
                'vote_type': active_vote.vote_type,
                'start_datetime': active_vote.start_datetime,
                'end_datetime': active_vote.end_datetime,
                'remaining_time': int((active_vote.end_datetime - now).total_seconds())
            })
        
        # Verifică dacă există un vot programat în viitor
        upcoming_vote = VoteSettings.objects.filter(
            is_active=True,
            start_datetime__gt=now
        ).order_by('start_datetime').first()
        
        if upcoming_vote:
            return Response({
                'is_vote_active': False,
                'upcoming_vote': {
                    'vote_type': upcoming_vote.vote_type,
                    'start_datetime': upcoming_vote.start_datetime,
                    'time_until_start': int((upcoming_vote.start_datetime - now).total_seconds())
                }
            })
        
        # Nu există niciun vot activ sau programat
        return Response({
            'is_vote_active': False,
            'message': 'Nu există sesiuni de vot active sau programate.'
        })

class AdminVoteSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Listează toate setările de vot"""
        vote_settings = VoteSettings.objects.all().order_by('-created_at')
        data = [{
            'id': setting.id,
            'vote_type': setting.vote_type,
            'is_active': setting.is_active,
            'start_datetime': setting.start_datetime,
            'end_datetime': setting.end_datetime,
            'created_at': setting.created_at
        } for setting in vote_settings]
        
        return Response(data)
    
    def post(self, request):
        """Creează o nouă configurație de vot"""
        required_fields = ['vote_type', 'start_datetime', 'end_datetime']
        
        # Verifică dacă toate câmpurile necesare sunt prezente
        if not all(field in request.data for field in required_fields):
            return Response({
                'message': 'Lipsesc câmpuri obligatorii',
                'required_fields': required_fields
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vote_settings = VoteSettings(
                vote_type=request.data['vote_type'],
                is_active=request.data.get('is_active', True),
                start_datetime=request.data['start_datetime'],
                end_datetime=request.data['end_datetime']
            )
            
            # Apelează clean() pentru a verifica suprapunerile
            vote_settings.clean()
            vote_settings.save()
            
            return Response({
                'id': vote_settings.id,
                'message': 'Configurația de vot a fost creată cu succes.'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'message': 'Eroare de validare',
                'errors': e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'message': f'Eroare la crearea configurației: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk=None):
        """Actualizează o configurație de vot existentă"""
        if not pk:
            return Response({
                'message': 'ID-ul configurației lipsește'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vote_settings = VoteSettings.objects.get(pk=pk)
        except VoteSettings.DoesNotExist:
            return Response({
                'message': 'Configurația nu a fost găsită'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Actualizează câmpurile
        if 'vote_type' in request.data:
            vote_settings.vote_type = request.data['vote_type']
        if 'is_active' in request.data:
            vote_settings.is_active = request.data['is_active']
        if 'start_datetime' in request.data:
            vote_settings.start_datetime = request.data['start_datetime']
        if 'end_datetime' in request.data:
            vote_settings.end_datetime = request.data['end_datetime']
        
        try:
            # Va apela clean() care verifică suprapunerile
            vote_settings.save()
            
            return Response({
                'message': 'Configurația a fost actualizată cu succes'
            })
        except ValidationError as e:
            return Response({
                'message': 'Eroare de validare',
                'errors': e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk=None):
        """Șterge o configurație de vot"""
        if not pk:
            return Response({
                'message': 'ID-ul configurației lipsește'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vote_settings = VoteSettings.objects.get(pk=pk)
            vote_settings.delete()
            return Response({
                'message': 'Configurația a fost ștearsă cu succes'
            })
        except VoteSettings.DoesNotExist:
            return Response({
                'message': 'Configurația nu a fost găsită'
            }, status=status.HTTP_404_NOT_FOUND)
        
class UserVotingEligibilityView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Verifică eligibilitatea utilizatorului pentru vot local"""
        user = request.user
        
        # Verifică dacă utilizatorul este autentificat cu buletin (are CNP)
        if not hasattr(user, 'cnp') or not user.cnp or not user.is_verified_by_id:
            return Response({
                'eligible': False,
                'message': 'Pentru a participa la votul local, trebuie să vă autentificați folosind buletinul.',
                'auth_type': 'email'
            }, status=status.HTTP_200_OK)
        
        # Utilizatorul este autentificat cu buletin
        return Response({
            'eligible': True,
            'message': 'Sunteți eligibil pentru a participa la votul local.',
            'auth_type': 'id_card',
            'user_info': {
                'cnp': user.cnp,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_200_OK)

class FindVotingSectionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Găsește secția de vot pentru utilizator pe baza adresei"""
        # Verifică dacă utilizatorul este autentificat cu buletin
        user = request.user
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'error': 'Autentificare cu buletinul necesară'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obține adresa din request
        address = request.data.get('address', '')
        city = request.data.get('city', '')
        county = request.data.get('county', '')
        
        if not all([address, city, county]):
            return Response({
                'error': 'Toate câmpurile sunt obligatorii: adresă, oraș, județ'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simplifică adresa pentru căutare
        address_simplified = re.sub(r'[^\w\s]', '', address.lower())
        
        # Căutăm secția de vot potrivită (simplificat)
        # În realitate, ar trebui să ai un algoritm mai complex sau o bază de date 
        # care să mapeze adresele la secții de vot
        voting_section = VotingSection.objects.filter(
            Q(county__iexact=county) & 
            Q(city__iexact=city)
        ).first()
        
        if not voting_section:
            # Dacă nu găsim o secție potrivită, returnăm o secție default pentru acel județ
            voting_section = VotingSection.objects.filter(county__iexact=county).first()
            
        if not voting_section:
            return Response({
                'error': 'Nu am putut identifica o secție de vot pentru adresa furnizată.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Returnăm informațiile despre secția de vot
        return Response({
            'section': {
                'id': voting_section.id,
                'section_id': voting_section.section_id,
                'name': voting_section.name,
                'address': voting_section.address,
                'city': voting_section.city,
                'county': voting_section.county
            }
        })

class LocalCandidatesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obține lista de candidați locali pentru zona utilizatorului"""
        # Obține parametrii din query string
        county = request.query_params.get('county', '')
        city = request.query_params.get('city', '')
        position = request.query_params.get('position', '')
        
        if not county or not city:
            return Response({
                'error': 'Județul și orașul sunt obligatorii'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtrează candidații
        candidates_query = LocalCandidate.objects.filter(
            county__iexact=county,
            city__iexact=city
        )
        
        if position:
            candidates_query = candidates_query.filter(position=position)
        
        candidates = candidates_query.values(
            'id', 'name', 'party', 'position', 'photo_url'
        )
        
        # Organizează candidații pe poziții
        positions = {}
        for candidate in candidates:
            pos = candidate['position']
            if pos not in positions:
                positions[pos] = []
            positions[pos].append(candidate)
        
        return Response({
            'positions': positions
        })
    
class SubmitLocalVoteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Înregistrează votul local al utilizatorului"""
        # Verifică dacă utilizatorul este autentificat cu buletin
        user = request.user
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'error': 'Autentificare cu buletinul necesară pentru a vota'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifică dacă utilizatorul a votat deja
        existing_vote = LocalVote.objects.filter(user=user).first()
        if existing_vote:
            return Response({
                'error': 'Ați votat deja în acest scrutin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obține datele din request
        candidate_id = request.data.get('candidate_id')
        voting_section_id = request.data.get('voting_section_id')
        
        if not candidate_id or not voting_section_id:
            return Response({
                'error': 'Candidatul și secția de vot sunt obligatorii'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            candidate = LocalCandidate.objects.get(pk=candidate_id)
            voting_section = VotingSection.objects.get(pk=voting_section_id)
        except (LocalCandidate.DoesNotExist, VotingSection.DoesNotExist):
            return Response({
                'error': 'Candidatul sau secția de vot nu există'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Înregistrează votul
        try:
            vote = LocalVote.objects.create(
                user=user,
                candidate=candidate,
                voting_section=voting_section
            )
            
            return Response({
                'message': 'Votul dvs. a fost înregistrat cu succes!',
                'vote_id': vote.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'A apărut o eroare la înregistrarea votului: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CheckUserVoteStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Verifică dacă utilizatorul a votat deja"""
        user = request.user
        
        # Verifică dacă utilizatorul este autentificat cu buletin
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'has_voted': False,
                'message': 'Utilizatorul nu este autentificat cu buletinul.'
            })
        
        # Verifică dacă utilizatorul a votat deja
        existing_votes = LocalVote.objects.filter(user=user)
        
        if existing_votes.exists():
            positions_voted = []
            for vote in existing_votes:
                positions_voted.append(vote.candidate.get_position_display())
            
            return Response({
                'has_voted': True,
                'positions_voted': positions_voted,
                'message': f'Ați votat deja pentru: {", ".join(positions_voted)}'
            })
        
        return Response({
            'has_voted': False,
            'message': 'Nu ați votat încă în acest scrutin.'
        })