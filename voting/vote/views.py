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
from .services_old import VotingSectionAIService
import logging
from .services.vote_monitoring import VoteMonitoringService
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
import numpy as np
from PIL import Image
from django.core.mail import EmailMessage
import uuid
from django.template.loader import render_to_string
from decouple import config
from django.conf import settings
from django.http import HttpResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
import os
from .models import PresidentialVote, PresidentialCandidate, ParliamentaryVote, ParliamentaryParty
from django.db import connection
from .models import VoteSystem, VoteOption, VoteCast
from .serializers import VoteSystemSerializer, VoteOptionSerializer, VoteCastSerializer, CreateVoteSystemSerializer
from .models import VoteToken
from .forms import EmailListForm
from django.core.mail import send_mail
from datetime import timedelta



logger = logging.getLogger(__name__)


# Inițializăm serviciul AI o singură dată pentru a evita încărcarea repetată a modelului
voting_section_ai = VotingSectionAIService()

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
        """Găsește secția de vot pentru utilizator pe baza adresei utilizând AI"""
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
        section_selection = request.data.get('section_selection')
        
        if not all([address, city, county]):
            return Response({
                'error': 'Toate câmpurile sunt obligatorii: adresă, oraș, județ'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convertim section_selection la int dacă există
        if section_selection is not None:
            try:
                section_selection = int(section_selection)
            except (ValueError, TypeError):
                section_selection = None
        
        # Log intrare în funcție
        logger.info(f"Căutare secție pentru utilizator {user.id} cu adresa: {county}, {city}, {address}")
        if section_selection is not None:
            logger.info(f"Utilizatorul a selectat manual secția cu indexul: {section_selection}")
        
        # Normalizăm județele la formatul de cod (AB, B, etc.)
        county_uppercase = county.upper()
        
        # Apelăm serviciul AI pentru a găsi secția de votare
        result = voting_section_ai.find_voting_section(
            county_uppercase, city.upper(), address, section_selection
        )
        
        if result.get('error'):
            logger.warning(f"Eroare la găsirea secției: {result.get('message')}")
            return Response({
                'error': result.get('message', 'Eroare la găsirea secției de votare')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificăm dacă s-au găsit multiple secții de votare
        if result.get('multiple_sections'):
            logger.info(f"S-au găsit {len(result.get('sections', []))} secții pentru adresa dată")
            return Response({
                'multiple_sections': True,
                'sections': result.get('sections', []),
                'street': result.get('street', ''),
                'method': result.get('method', 'unknown')
            })
        
        if result.get('success'):
            # Verificăm dacă secția există deja în baza de date
            section_data = result['section']
            voting_section = VotingSection.objects.filter(
                section_id=section_data['section_id'],
                county=section_data['county'],
                city=section_data['city']
            ).first()
            
            # Dacă nu există, o creăm
            if not voting_section:
                logger.info(f"Creăm secție nouă în baza de date: {section_data['name']}")
                
                # Pregătim datele pentru creare
                section_create_data = {
                    'section_id': section_data['section_id'],
                    'name': section_data['name'],
                    'address': section_data['address'],
                    'city': section_data['city'],
                    'county': section_data['county']
                }
                
                # Adăugăm câmpurile opționale dacă există
                if 'address_desc' in section_data and section_data['address_desc']:
                    section_create_data['address_desc'] = section_data['address_desc']
                
                if 'locality' in section_data and section_data['locality']:
                    section_create_data['locality'] = section_data['locality']
                
                voting_section = VotingSection.objects.create(**section_create_data)
            
            # Construim răspunsul
            response_data = {
                'section': {
                    'id': voting_section.id,
                    'section_id': voting_section.section_id,
                    'name': voting_section.name,
                    'address': voting_section.address,
                    'city': voting_section.city,
                    'county': voting_section.county,
                },
                'method': result.get('method', 'unknown')  # Metoda utilizată pentru identificare
            }
            
            # Adăugăm detalii suplimentare dacă există
            if hasattr(voting_section, 'address_desc') and voting_section.address_desc:
                response_data['section']['address_desc'] = voting_section.address_desc
            elif 'address_desc' in section_data and section_data['address_desc']:
                response_data['section']['address_desc'] = section_data['address_desc']
                
            if hasattr(voting_section, 'locality') and voting_section.locality:
                response_data['section']['locality'] = voting_section.locality
            elif 'locality' in section_data and section_data['locality']:
                response_data['section']['locality'] = section_data['locality']
                
            # Adăugăm detalii despre strada potrivită dacă există
            if 'matched_street' in section_data:
                response_data['matched_street'] = section_data['matched_street']
            
            logger.info(f"Secție găsită: {voting_section.name} prin metoda {result.get('method', 'unknown')}")
            return Response(response_data)
        
        # Cazul în care ceva nu a mers bine
        logger.error(f"Eroare neașteptată la găsirea secției pentru {county}, {city}, {address}")
        return Response({
            'error': 'Nu am putut identifica o secție de vot pentru adresa furnizată.'
        }, status=status.HTTP_404_NOT_FOUND)
    
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
    
User = get_user_model()

class VoteMonitoringView(APIView):
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitoring_service = VoteMonitoringService()
    
    def post(self, request):
        """Primește imagini pentru monitorizarea votului și verifică identitatea utilizatorului"""
        print("POST primit în VoteMonitoringView")
        user = request.user
        live_image = request.FILES.get('live_image')
        
        if not live_image:
            return Response(
                {"error": "Imaginea live este necesară pentru monitorizarea"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificăm dacă utilizatorul are imagine de buletin stocată
        if not user.id_card_image:
            return Response(
                {"error": "Nu există imagine de referință pentru acest utilizator"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Încărcăm imaginea de referință din buletin
            id_card_path = user.id_card_image.path if default_storage.exists(user.id_card_image.name) else None
            if not id_card_path:
                return Response({"error": "Nu există imaginea de referință în baza de date."}, status=404)
                
            # Pregătim imaginea de buletin
            id_card_image = Image.open(id_card_path).convert("RGB")
            id_card_array = np.array(id_card_image)
            
            # Extragem encoding-ul feței din buletin
            reference_encoding, error, _ = self.monitoring_service.detect_and_encode_face(id_card_array)
            if reference_encoding is None:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
            
            # Citim imaginea live
            live_image_data = live_image.read()
            
            # Verificăm identitatea
            match, message, num_faces = self.monitoring_service.verify_voter_identity(
                reference_encoding, 
                live_image_data
            )
            
            return Response({
                "match": match,
                "message": message,
                "num_faces": num_faces
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Eroare în monitorizarea votului: {e}")
            return Response(
                {"error": f"Eroare în procesarea imaginii: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ConfirmVoteAndSendReceiptView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Confirmă votul și trimite chitanța prin email"""
        user = request.user
        candidates_data = request.data.get('candidates', [])
        voting_section_id = request.data.get('voting_section_id')
        send_receipt = request.data.get('send_receipt', False)
        receipt_method = request.data.get('receipt_method', 'email')  # 'email' sau 'sms'
        contact_info = request.data.get('contact_info', '')  # email sau telefon furnizat de utilizator
        
        if not candidates_data or not voting_section_id:
            return Response({
                'error': 'Candidații și secția de vot sunt obligatorii'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            voting_section = VotingSection.objects.get(pk=voting_section_id)
        except VotingSection.DoesNotExist:
            return Response({
                'error': 'Secția de vot nu există'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validăm informațiile de contact dacă utilizatorul a solicitat confirmarea
        if send_receipt:
            if receipt_method == 'email':
                if not contact_info or '@' not in contact_info:
                    return Response({
                        'error': 'Pentru a primi confirmarea prin email, trebuie să furnizați o adresă de email validă.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif receipt_method == 'sms':
                if not contact_info or len(contact_info) < 10:
                    return Response({
                        'error': 'Pentru a primi confirmarea prin SMS, trebuie să furnizați un număr de telefon valid.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generăm un ID unic pentru vot
        vote_reference = str(uuid.uuid4())[:8].upper()
        
        # Înregistrăm voturile pentru toți candidații
        saved_votes = []
        saved_positions = []  # Ținem evidența pozițiilor pentru care s-a votat deja
        errors = []
        
        for candidate_data in candidates_data:
            candidate_id = candidate_data.get('id')
            
            try:
                candidate = LocalCandidate.objects.get(pk=candidate_id)
                position = candidate.position  # Folosim poziția din baza de date
                
                # Verifică dacă utilizatorul a votat deja pentru această poziție
                existing_vote = LocalVote.objects.filter(
                    user=user,
                    candidate__position=position
                ).first()
                
                if existing_vote:
                    position_display = candidate.get_position_display()
                    errors.append(f'Ați votat deja pentru poziția {position_display}')
                    continue
                
                if position in saved_positions:
                    position_display = candidate.get_position_display()
                    errors.append(f'Puteți vota doar un candidat pentru poziția {position_display}')
                    continue
                
                # Înregistrează votul individual pentru fiecare poziție
                vote = LocalVote.objects.create(
                    user=user,
                    candidate=candidate,
                    voting_section=voting_section,
                    vote_reference=vote_reference
                )
                saved_votes.append(vote)
                saved_positions.append(position)
                
                # Log pentru debugging
                logger.info(f"Vot înregistrat pentru poziția {candidate.get_position_display()} (ID: {vote.id})")
                
            except LocalCandidate.DoesNotExist:
                errors.append(f'Candidatul cu ID-ul {candidate_id} nu există')
                continue
            except Exception as e:
                logger.error(f"Eroare la salvarea votului: {str(e)}")
                errors.append(f'Eroare la înregistrarea votului: {str(e)}')
                continue
        
        # Dacă nu s-a salvat niciun vot, returnăm eroare
        if not saved_votes:
            return Response({
                'error': 'Nu s-a putut înregistra niciun vot',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Trimite chitanța de vot dacă utilizatorul a solicitat
        if send_receipt and saved_votes:
            try:
                if receipt_method == 'email':
                    email_success = self.send_vote_receipt_email(user, saved_votes, voting_section, vote_reference, contact_info)
                    if not email_success:
                        errors.append('Confirmarea de vot nu a putut fi trimisă prin email, dar votul a fost înregistrat')
            except Exception as e:
                logger.error(f"Eroare trimitere confirmare: {str(e)}")
                errors.append('A apărut o eroare la trimiterea confirmării, dar votul a fost înregistrat')
        
        return Response({
            'message': 'Votul dvs. a fost înregistrat cu succes!',
            'vote_reference': vote_reference,
            'votes_count': len(saved_votes),
            'errors': errors if errors else None
        }, status=status.HTTP_201_CREATED)
    
    def send_vote_receipt_email(self, user, votes, voting_section, vote_reference, email):
        """Trimite email cu chitanța pentru vot"""
        try:
            # Data și ora curentă
            vote_datetime = timezone.now().strftime("%d-%m-%Y %H:%M:%S")
            
            # Pregătim datele pentru template
            candidates_info = []
            for vote in votes:
                candidates_info.append({
                    'name': vote.candidate.name,
                    'party': vote.candidate.party,
                    'position': vote.candidate.get_position_display(),
                })

            # Construim url ul pentru descarcarea pdf-ului
            from django.urls import reverse
            from django.conf import settings
            backend_url = settings.BACKEND_URL
            pdf_url = f"{backend_url}{reverse('generate-vote-receipt-pdf')}?vote_reference={vote_reference}"
           
            context = {
                'user_name': f"{user.first_name} {user.last_name}",
                'vote_reference': vote_reference,
                'vote_datetime': vote_datetime,
                'candidates': candidates_info,
                'section_id': voting_section.section_id,
                'section_name': voting_section.name,
                'section_address': voting_section.address,
                'section_city': voting_section.city,
                'section_county': voting_section.county,
                'download_url': pdf_url
            }
            
            # Debug template paths
            from django.conf import settings
            logger.info(f"TEMPLATE_DIRS: {settings.TEMPLATES[0]['DIRS']}")
            logger.info(f"APP_DIRS enabled: {settings.TEMPLATES[0]['APP_DIRS']}")
            
            # Încearcă să renderizeze template-ul pentru email - încercăm diferite locații
            try:
                html_message = render_to_string('vote_receipt_email.html', context)
            except Exception as template_error:
                # Log pentru debugging
                logger.error(f"Eroare la găsirea template-ului vote_receipt_email.html: {template_error}")
                
                # Încercăm alte posibile locații pentru template
                try:
                    html_message = render_to_string('vote/templates/vote_receipt_email.html', context)
                except Exception as e:
                    # Creăm un mesaj HTML simplu dacă template-ul nu este găsit
                    logger.error(f"Nu s-a găsit nici template-ul alternativ: {e}")
                    html_message = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }}
                            .header {{ background-color: #007bff; color: white; padding: 10px; text-align: center; }}
                            .section {{ margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
                            .reference {{ font-size: 24px; font-weight: bold; color: #007bff; text-align: center; }}
                            .warning {{ color: #ff0000; font-weight: bold; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>SmartVote - Confirmare Vot</h1>
                            </div>
                            
                            <div class="section">
                                <h2>Bună ziua, {user.first_name} {user.last_name}</h2>
                                <p>Vă mulțumim pentru participarea la procesul electoral. Votul dumneavoastră a fost înregistrat cu succes.</p>
                                <p class="reference">Referință vot: {vote_reference}</p>
                                <p>Data și ora: {vote_datetime}</p>
                            </div>
                            
                            <div class="section">
                                <h3>Candidați votați:</h3>
                                <ul>
                                    {"".join([f"<li><strong>{c['position']}:</strong> {c['name']} ({c['party']})</li>" for c in candidates_info])}
                                </ul>
                            </div>
                            
                            <div class="section">
                                <h3>Secția de votare:</h3>
                                <p><strong>Număr secție:</strong> {voting_section.section_id}</p>
                                <p><strong>Nume secție:</strong> {voting_section.name}</p>
                                <p><strong>Adresă:</strong> {voting_section.address}</p>
                                <p><strong>Localitate:</strong> {voting_section.city}</p>
                                <p><strong>Județ:</strong> {voting_section.county}</p>
                            </div>
                            
                            <div class="footer">
                                <p class="warning">ATENȚIE: Acest mesaj este generat automat și confidențial. Vă rugăm să nu răspundeți la acest email.</p>
                                <p>Toate drepturile rezervate &copy; SmartVote 2024</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
            
            # Trimitem email-ul
            email_msg = EmailMessage(
                'Confirmare vot - SmartVote',
                html_message,
                config('EMAIL_FROM'),
                [email],  # Folosim adresa de email furnizată de utilizator
                reply_to=[config('EMAIL_FROM')],
            )
            email_msg.content_subtype = 'html'
            email_msg.send()
            
            logger.info(f"Chitanța de vot trimisă prin email pentru utilizatorul {user.id} la adresa {email}")
            return True
        except Exception as e:
            logger.error(f"Eroare la trimiterea chitanței prin email: {e}")
            return False
        
class GenerateVoteReceiptPDFView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generează un PDF cu confirmarea votului"""
        vote_reference = request.GET.get('vote_reference')
        if not vote_reference:
            return Response({
                'error': 'Referința votului este obligatorie'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Verifică dacă referința votului există
        votes = LocalVote.objects.filter(vote_reference=vote_reference)
        if not votes.exists():
            return Response({
                'error': 'Nu a fost găsit un vot cu această referință'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Obține primul vot pentru a extrage secția de vot
        first_vote = votes.first()
        voting_section = first_vote.voting_section
        
        # Pregătește datele pentru PDF
        candidates_info = []
        for vote in votes:
            candidates_info.append({
                'name': vote.candidate.name,
                'party': vote.candidate.party,
                'position': vote.candidate.get_position_display(),
            })
            
        # Generează PDF-ul
        buffer = io.BytesIO()
        self.create_pdf(buffer, first_vote.user, votes, candidates_info, voting_section, vote_reference)
        buffer.seek(0)
        
        # Returnează PDF-ul ca răspuns
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="confirmare_vot_{vote_reference}.pdf"'
        return response
    
    def create_pdf(self, buffer, user, votes, candidates_info, voting_section, vote_reference):
        """Creează documentul PDF cu confirmarea votului"""
        # Configurează documentul
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Configurarea fonturilor cu suport pentru diacritice
        try:
            font_path = os.path.join(settings.BASE_DIR, 'vote', 'static', 'fonts')
            dejavu_regular = os.path.join(font_path, 'DejaVuSans.ttf')
            dejavu_bold = os.path.join(font_path, 'DejaVuSans-Bold.ttf')
            
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_regular))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold))
            font_name = 'DejaVuSans'
            bold_font_name = 'DejaVuSans-Bold'
        except Exception as e:
            # Logăm eroarea și folosim fonturile implicite
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Eroare la încărcarea fonturilor: {e}")
            font_name = 'Helvetica'
            bold_font_name = 'Helvetica-Bold'
        
        # Stiluri
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CenterTitle',
            parent=styles['Heading1'],
            fontName=bold_font_name,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='CenterNormal',
            parent=styles['Normal'],
            fontName=font_name,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='NormalRomanian',
            parent=styles['Normal'],
            fontName=font_name,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='Heading3Romanian',
            parent=styles['Heading3'],
            fontName=bold_font_name,
            spaceAfter=6
        ))
        
        # Data și ora curentă
        vote_datetime = timezone.now().strftime("%d-%m-%Y %H:%M:%S")
        
        # Elemente PDF
        elements = []
        
        # Titlu
        elements.append(Paragraph("CONFIRMARE VOT - SMARTVOTE", styles['CenterTitle']))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Informații utilizator
        elements.append(Paragraph(f"Bună ziua, {user.first_name} {user.last_name}", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Vă mulțumim pentru participarea la procesul electoral. Votul dumneavoastră a fost înregistrat cu succes.", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Referință vot
        elements.append(Paragraph(f"Referință vot: {vote_reference}", styles['CenterNormal']))
        elements.append(Paragraph(f"Data și ora: {vote_datetime}", styles['CenterNormal']))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Candidați votați
        elements.append(Paragraph("Candidați votați:", styles['Heading3Romanian']))
        
        # Tabel pentru candidați
        data = [["Poziție", "Nume", "Partid"]]
        for candidate in candidates_info:
            data.append([candidate['position'], candidate['name'], candidate['party']])
        
        # Stilul pentru tabel
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),  # Folosește fontul cu suport pentru diacritice
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        candidates_table = Table(data, style=table_style)
        elements.append(candidates_table)
        elements.append(Spacer(1, 0.25 * inch))
        
        # Informații secție de vot
        elements.append(Paragraph("Secția de votare:", styles['Heading3Romanian']))
        elements.append(Paragraph(f"Număr secție: {voting_section.section_id}", styles['NormalRomanian']))
        elements.append(Paragraph(f"Nume secție: {voting_section.name}", styles['NormalRomanian']))
        elements.append(Paragraph(f"Adresă: {voting_section.address}", styles['NormalRomanian']))
        elements.append(Paragraph(f"Localitate: {voting_section.city}", styles['NormalRomanian']))
        elements.append(Paragraph(f"Județ: {voting_section.county}", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Avertisment și footer
        elements.append(Paragraph("ATENȚIE: Acest document este confidențial și servește drept confirmare a votului dumneavoastră.", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Toate drepturile rezervate © SmartVote 2024", styles['CenterNormal']))
        
        # Generează PDF-ul
        doc.build(elements)

class UserPresidentialVotingEligibilityView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Verifică eligibilitatea utilizatorului pentru vot prezidențial"""
        user = request.user
        
        # Verifică dacă utilizatorul este autentificat cu buletin (are CNP)
        if not hasattr(user, 'cnp') or not user.cnp or not user.is_verified_by_id:
            return Response({
                'eligible': False,
                'message': 'Pentru a participa la votul prezidențial, trebuie să vă autentificați folosind buletinul.',
                'auth_type': 'email'
            }, status=status.HTTP_200_OK)
        
        # Utilizatorul este autentificat cu buletin
        return Response({
            'eligible': True,
            'message': 'Sunteți eligibil pentru a participa la votul prezidențial.',
            'auth_type': 'id_card',
            'user_info': {
                'cnp': user.cnp,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_200_OK)

class PresidentialCandidatesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obține lista de candidați prezidențiali"""
        try:
            # Verifică ce nume de coloană este folosit pentru ordinea candidaților
            with connection.cursor() as cursor:
                cursor.execute("DESCRIBE vote_presidentialcandidate")
                columns = [col[0] for col in cursor.fetchall()]
                
                # Determină numele corect al coloanei pentru sortare
                order_column = 'order_nr' if 'order_nr' in columns else 'order'
            
            # Construim query-ul utilizând ORM în funcție de coloana disponibilă
            query = PresidentialCandidate.objects.all()
            
            # Adăugăm criteriul de ordonare în funcție de coloana existentă
            if order_column in columns:
                query = query.order_by(order_column)
            
            # Extragem valorile necesare
            candidates = query.values(
                'id', 'name', 'party', 'photo_url', 'description'
            )
            
            return Response({
                'candidates': candidates
            })
            
        except Exception as e:
            # Log pentru debugging
            logger.error(f"Eroare la obținerea candidaților prezidențiali: {str(e)}")
            
            # Încearcă o abordare mai simplă, fără ordonare
            try:
                candidates = PresidentialCandidate.objects.all().values(
                    'id', 'name', 'party', 'photo_url', 'description'
                )
                
                return Response({
                    'candidates': candidates
                })
            except Exception as fallback_error:
                logger.error(f"Eroare la fallback pentru candidații prezidențiali: {str(fallback_error)}")
                return Response({
                    'error': 'Nu s-au putut obține candidații prezidențiali',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckPresidentialVoteStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Verifică dacă utilizatorul a votat deja la alegerile prezidențiale"""
        user = request.user
        
        # Verifică dacă utilizatorul este autentificat cu buletin
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'has_voted': False,
                'message': 'Utilizatorul nu este autentificat cu buletinul.'
            })
        
        # Verifică dacă utilizatorul a votat deja
        existing_vote = PresidentialVote.objects.filter(user=user).first()
        
        if existing_vote:
            return Response({
                'has_voted': True,
                'message': 'Ați votat deja în acest scrutin prezidențial.',
                'candidate_name': existing_vote.candidate.name,
                'party': existing_vote.candidate.party
            })
        
        return Response({
            'has_voted': False,
            'message': 'Nu ați votat încă în acest scrutin prezidențial.'
        })

class SubmitPresidentialVoteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Înregistrează votul prezidențial și trimite confirmarea, dacă este solicitată"""
        user = request.user
        candidate_id = request.data.get('candidate_id')
        send_receipt = request.data.get('send_receipt', False)
        receipt_method = request.data.get('receipt_method', 'email')
        contact_info = request.data.get('contact_info', '')
        
        # Verifică dacă utilizatorul este autentificat cu buletin
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'error': 'Autentificare cu buletin necesară pentru a vota'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifică dacă utilizatorul a votat deja
        existing_vote = PresidentialVote.objects.filter(user=user).first()
        if existing_vote:
            return Response({
                'error': 'Ați votat deja în acest scrutin prezidențial'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not candidate_id:
            return Response({
                'error': 'Trebuie să selectați un candidat'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            candidate = PresidentialCandidate.objects.get(pk=candidate_id)
        except PresidentialCandidate.DoesNotExist:
            return Response({
                'error': 'Candidatul selectat nu există'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validăm informațiile de contact dacă utilizatorul a solicitat confirmarea
        if send_receipt:
            if receipt_method == 'email':
                if not contact_info or '@' not in contact_info:
                    return Response({
                        'error': 'Pentru a primi confirmarea prin email, trebuie să furnizați o adresă de email validă.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif receipt_method == 'sms':
                if not contact_info or len(contact_info) < 10:
                    return Response({
                        'error': 'Pentru a primi confirmarea prin SMS, trebuie să furnizați un număr de telefon valid.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generăm un ID unic pentru vot
        vote_reference = str(uuid.uuid4())[:8].upper()
        
        # Înregistrăm votul
        try:
            vote = PresidentialVote.objects.create(
                user=user,
                candidate=candidate,
                vote_reference=vote_reference
            )
            
            # Trimite chitanța de vot dacă utilizatorul a solicitat
            if send_receipt:
                try:
                    if receipt_method == 'email':
                        email_success = self.send_vote_receipt_email(user, vote, contact_info)
                        if not email_success:
                            return Response({
                                'message': 'Votul a fost înregistrat, dar confirmarea prin email nu a putut fi trimisă.',
                                'vote_reference': vote_reference
                            }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    logger.error(f"Eroare trimitere confirmare: {str(e)}")
                    return Response({
                        'message': 'Votul a fost înregistrat, dar a apărut o eroare la trimiterea confirmării.',
                        'vote_reference': vote_reference
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'message': 'Votul dvs. a fost înregistrat cu succes!',
                'vote_reference': vote_reference
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'A apărut o eroare la înregistrarea votului: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def send_vote_receipt_email(self, user, vote, email):
        """Trimite email cu chitanța pentru vot prezidențial"""
        try:
            # Data și ora curentă
            vote_datetime = vote.vote_datetime.strftime("%d-%m-%Y %H:%M:%S")
            
            # Pregătim datele pentru template
            candidate_info = {
                'name': vote.candidate.name,
                'party': vote.candidate.party,
                'position': 'Președinte al României'
            }

            # Construim URL-ul pentru descărcarea PDF-ului 
            from django.urls import reverse
            from django.conf import settings
            
            backend_url = settings.BACKEND_URL.rstrip('/')  # Eliminăm trailing slash dacă există
            pdf_url = f"{backend_url}{reverse('generate-presidential-vote-receipt-pdf')}?vote_reference={vote.vote_reference}"
           
            context = {
                'user_name': f"{user.first_name} {user.last_name}",
                'vote_reference': vote.vote_reference,
                'vote_datetime': vote_datetime,
                'candidate': candidate_info,
                'download_url': pdf_url  # Adăugăm URL-ul de descărcare PDF
            }
            
            # Renderizăm template-ul pentru email
            try:
                html_message = render_to_string('presidential_vote_receipt_email.html', context)
            except Exception as template_error:
                # Fallback la un mesaj HTML simplu
                logger.error(f"Eroare la găsirea template-ului: {template_error}")
                html_message = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }}
                        .header {{ background-color: #007bff; color: white; padding: 10px; text-align: center; }}
                        .download-btn {{ display: inline-block; background-color: #0080ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>SmartVote - Confirmare Vot Prezidențial</h1>
                        </div>
                        
                        <div class="section">
                            <h2>Bună ziua, {user.first_name} {user.last_name}</h2>
                            <p>Vă mulțumim pentru participarea la procesul electoral. Votul dumneavoastră pentru alegerea Președintelui României a fost înregistrat cu succes.</p>
                            <p>Referință vot: {vote.vote_reference}</p>
                            <p>Data și ora: {vote_datetime}</p>
                        </div>
                        
                        <div class="section">
                            <h3>Candidatul votat:</h3>
                            <p><strong>Președinte:</strong> {vote.candidate.name} ({vote.candidate.party})</p>
                            
                            <a href="{pdf_url}" class="download-btn">Descarcă confirmarea în format PDF</a>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            # Trimitem email-ul
            email_msg = EmailMessage(
                'Confirmare vot prezidențial - SmartVote',
                html_message,
                config('EMAIL_FROM'),
                [email],
                reply_to=[config('EMAIL_FROM')],
            )
            email_msg.content_subtype = 'html'
            email_msg.send()
            
            logger.info(f"Chitanța de vot prezidențial trimisă prin email pentru utilizatorul {user.id} la adresa {email}")
            return True
        except Exception as e:
            logger.error(f"Eroare la trimiterea chitanței prin email: {e}")
            return False

class GeneratePresidentialVoteReceiptPDFView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generează un PDF cu confirmarea votului prezidențial"""
        vote_reference = request.GET.get('vote_reference')
        if not vote_reference:
            return Response({
                'error': 'Referința votului este obligatorie'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Verifică dacă referința votului există
        vote = PresidentialVote.objects.filter(vote_reference=vote_reference).first()
        if not vote:
            return Response({
                'error': 'Nu a fost găsit un vot cu această referință'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Generează PDF-ul
        buffer = io.BytesIO()
        self.create_pdf(buffer, vote.user, vote)
        buffer.seek(0)
        
        # Returnează PDF-ul ca răspuns
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="confirmare_vot_prezidential_{vote_reference}.pdf"'
        return response
    
    def create_pdf(self, buffer, user, vote):
        """Creează documentul PDF cu confirmarea votului prezidențial"""
        # Configurează documentul
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Configurarea fonturilor cu suport pentru diacritice
        try:
            font_path = os.path.join(settings.BASE_DIR, 'vote', 'static', 'fonts')
            dejavu_regular = os.path.join(font_path, 'DejaVuSans.ttf')
            dejavu_bold = os.path.join(font_path, 'DejaVuSans-Bold.ttf')
            
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_regular))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold))
            font_name = 'DejaVuSans'
            bold_font_name = 'DejaVuSans-Bold'
        except Exception as e:
            # Folosim fonturile implicite în caz de eroare
            logger.error(f"Eroare la încărcarea fonturilor: {e}")
            font_name = 'Helvetica'
            bold_font_name = 'Helvetica-Bold'
        
        # Stiluri
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CenterTitle',
            parent=styles['Heading1'],
            fontName=bold_font_name,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='CenterNormal',
            parent=styles['Normal'],
            fontName=font_name,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='NormalRomanian',
            parent=styles['Normal'],
            fontName=font_name,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='Heading3Romanian',
            parent=styles['Heading3'],
            fontName=bold_font_name,
            spaceAfter=6
        ))
        
        # Elemente PDF
        elements = []
        
        # Titlu
        elements.append(Paragraph("CONFIRMARE VOT PREZIDENȚIAL - SMARTVOTE", styles['CenterTitle']))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Informații utilizator
        elements.append(Paragraph(f"Bună ziua, {user.first_name} {user.last_name}", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Vă mulțumim pentru participarea la procesul electoral. Votul dumneavoastră pentru alegerea Președintelui României a fost înregistrat cu succes.", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Referință vot
        elements.append(Paragraph(f"Referință vot: {vote.vote_reference}", styles['CenterNormal']))
        elements.append(Paragraph(f"Data și ora: {vote.vote_datetime.strftime('%d-%m-%Y %H:%M:%S')}", styles['CenterNormal']))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Candidatul votat
        elements.append(Paragraph("Candidatul votat:", styles['Heading3Romanian']))
        
        # Tabel pentru candidat
        data = [["Funcție", "Nume", "Partid"]]
        data.append(["Președinte al României", vote.candidate.name, vote.candidate.party])
        
        # Stilul pentru tabel
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        candidate_table = Table(data, style=table_style)
        elements.append(candidate_table)
        elements.append(Spacer(1, 0.25 * inch))
        
        # Avertisment și footer
        elements.append(Paragraph("ATENȚIE: Acest document este confidențial și servește drept confirmare a votului dumneavoastră.", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Toate drepturile rezervate © SmartVote 2024", styles['CenterNormal']))
        
        # Generează PDF-ul
        doc.build(elements)

#view pentru alegerile parlamentare
class UserParliamentaryVotingEligibilityView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Verifică eligibilitatea utilizatorului pentru vot parlamentar"""
        user = request.user
        
        # Verifică dacă utilizatorul este autentificat cu buletin (are CNP)
        if not hasattr(user, 'cnp') or not user.cnp or not user.is_verified_by_id:
            return Response({
                'eligible': False,
                'message': 'Pentru a participa la votul parlamentar, trebuie să vă autentificați folosind buletinul.',
                'auth_type': 'email'
            }, status=status.HTTP_200_OK)
        
        # Utilizatorul este autentificat cu buletin
        return Response({
            'eligible': True,
            'message': 'Sunteți eligibil pentru a participa la votul parlamentar.',
            'auth_type': 'id_card',
            'user_info': {
                'cnp': user.cnp,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_200_OK)

class ParliamentaryPartiesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obține lista de partide parlamentare"""
        try:
            # Verifică ce nume de coloană este folosit pentru ordinea partidelor
            with connection.cursor() as cursor:
                cursor.execute("DESCRIBE vote_parliamentaryparty")
                columns = [col[0] for col in cursor.fetchall()]
                
                # Determină numele corect al coloanei pentru sortare
                order_column = 'order_nr' if 'order_nr' in columns else 'order'
            
            # Construim query-ul utilizând ORM în funcție de coloana disponibilă
            query = ParliamentaryParty.objects.all()
            
            # Adăugăm criteriul de ordonare în funcție de coloana existentă
            if order_column in columns:
                query = query.order_by(order_column)
            
            # Extragem valorile necesare
            parties = query.values(
                'id', 'name', 'abbreviation', 'logo_url', 'description'
            )
            
            return Response({
                'parties': parties
            })
            
        except Exception as e:
            # Log pentru debugging
            logger.error(f"Eroare la obținerea partidelor parlamentare: {str(e)}")
            
            # Încearcă o abordare mai simplă, fără ordonare
            try:
                parties = ParliamentaryParty.objects.all().values(
                    'id', 'name', 'abbreviation', 'logo_url', 'description'
                )
                
                return Response({
                    'parties': parties
                })
            except Exception as fallback_error:
                logger.error(f"Eroare la fallback pentru partidele parlamentare: {str(fallback_error)}")
                return Response({
                    'error': 'Nu s-au putut obține partidele parlamentare',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckParliamentaryVoteStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Verifică dacă utilizatorul a votat deja la alegerile parlamentare"""
        user = request.user
        
        # Verifică dacă utilizatorul este autentificat cu buletin
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'has_voted': False,
                'message': 'Utilizatorul nu este autentificat cu buletinul.'
            })
        
        # Verifică dacă utilizatorul a votat deja
        existing_vote = ParliamentaryVote.objects.filter(user=user).first()
        
        if existing_vote:
            return Response({
                'has_voted': True,
                'message': 'Ați votat deja în acest scrutin parlamentar.',
                'party_name': existing_vote.party.name,
                'abbreviation': existing_vote.party.abbreviation
            })
        
        return Response({
            'has_voted': False,
            'message': 'Nu ați votat încă în acest scrutin parlamentar.'
        })

class SubmitParliamentaryVoteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Înregistrează votul parlamentar și trimite confirmarea, dacă este solicitată"""
        user = request.user
        party_id = request.data.get('party_id')
        send_receipt = request.data.get('send_receipt', False)
        receipt_method = request.data.get('receipt_method', 'email')
        contact_info = request.data.get('contact_info', '')
        
        # Verifică dacă utilizatorul este autentificat cu buletin
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'error': 'Autentificare cu buletin necesară pentru a vota'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifică dacă utilizatorul a votat deja
        existing_vote = ParliamentaryVote.objects.filter(user=user).first()
        if existing_vote:
            return Response({
                'error': 'Ați votat deja în acest scrutin parlamentar'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not party_id:
            return Response({
                'error': 'Trebuie să selectați un partid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            party = ParliamentaryParty.objects.get(pk=party_id)
        except ParliamentaryParty.DoesNotExist:
            return Response({
                'error': 'Partidul selectat nu există'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validăm informațiile de contact dacă utilizatorul a solicitat confirmarea
        if send_receipt:
            if receipt_method == 'email':
                if not contact_info or '@' not in contact_info:
                    return Response({
                        'error': 'Pentru a primi confirmarea prin email, trebuie să furnizați o adresă de email validă.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif receipt_method == 'sms':
                if not contact_info or len(contact_info) < 10:
                    return Response({
                        'error': 'Pentru a primi confirmarea prin SMS, trebuie să furnizați un număr de telefon valid.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generăm un ID unic pentru vot
        vote_reference = str(uuid.uuid4())[:8].upper()
        
        # Înregistrăm votul
        try:
            vote = ParliamentaryVote.objects.create(
                user=user,
                party=party,
                vote_reference=vote_reference
            )
            
            # Trimite chitanța de vot dacă utilizatorul a solicitat
            if send_receipt:
                try:
                    if receipt_method == 'email':
                        email_success = self.send_vote_receipt_email(user, vote, contact_info)
                        if not email_success:
                            return Response({
                                'message': 'Votul a fost înregistrat, dar confirmarea prin email nu a putut fi trimisă.',
                                'vote_reference': vote_reference
                            }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    logger.error(f"Eroare trimitere confirmare: {str(e)}")
                    return Response({
                        'message': 'Votul a fost înregistrat, dar a apărut o eroare la trimiterea confirmării.',
                        'vote_reference': vote_reference
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'message': 'Votul dvs. a fost înregistrat cu succes!',
                'vote_reference': vote_reference
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'A apărut o eroare la înregistrarea votului: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def send_vote_receipt_email(self, user, vote, email):
        """Trimite email cu chitanța pentru vot parlamentar"""
        try:
            # Data și ora curentă
            vote_datetime = vote.vote_datetime.strftime("%d-%m-%Y %H:%M:%S")
            
            # Pregătim datele pentru template
            party_info = {
                'name': vote.party.name,
                'abbreviation': vote.party.abbreviation if vote.party.abbreviation else ""
            }

            # Construim URL-ul pentru descărcarea PDF-ului 
            from django.urls import reverse
            from django.conf import settings
            
            backend_url = settings.BACKEND_URL.rstrip('/')  # Eliminăm trailing slash dacă există
            pdf_url = f"{backend_url}{reverse('generate-parliamentary-vote-receipt-pdf')}?vote_reference={vote.vote_reference}"
           
            context = {
                'user_name': f"{user.first_name} {user.last_name}",
                'vote_reference': vote.vote_reference,
                'vote_datetime': vote_datetime,
                'party': party_info,
                'download_url': pdf_url  # Adăugăm URL-ul de descărcare PDF
            }
            
            # Renderizăm template-ul pentru email
            try:
                html_message = render_to_string('parliamentary_vote_receipt_email.html', context)
            except Exception as template_error:
                # Fallback la un mesaj HTML simplu
                logger.error(f"Eroare la găsirea template-ului: {template_error}")
                html_message = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }}
                        .header {{ background-color: #007bff; color: white; padding: 10px; text-align: center; }}
                        .download-btn {{ display: inline-block; background-color: #0080ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>SmartVote - Confirmare Vot Parlamentar</h1>
                        </div>
                        
                        <div class="section">
                            <h2>Bună ziua, {user.first_name} {user.last_name}</h2>
                            <p>Vă mulțumim pentru participarea la procesul electoral. Votul dumneavoastră pentru alegerea Parlamentului României a fost înregistrat cu succes.</p>
                            <p>Referință vot: {vote.vote_reference}</p>
                            <p>Data și ora: {vote_datetime}</p>
                        </div>
                        
                        <div class="section">
                            <h3>Partidul votat:</h3>
                            <p><strong>Partid:</strong> {vote.party.name} {vote.party.abbreviation if vote.party.abbreviation else ""}</p>
                            
                            <a href="{pdf_url}" class="download-btn">Descarcă confirmarea în format PDF</a>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            # Trimitem email-ul
            email_msg = EmailMessage(
                'Confirmare vot parlamentar - SmartVote',
                html_message,
                config('EMAIL_FROM'),
                [email],
                reply_to=[config('EMAIL_FROM')],
            )
            email_msg.content_subtype = 'html'
            email_msg.send()
            
            logger.info(f"Chitanța de vot parlamentar trimisă prin email pentru utilizatorul {user.id} la adresa {email}")
            return True
        except Exception as e:
            logger.error(f"Eroare la trimiterea chitanței prin email: {e}")
            return False

class GenerateParliamentaryVoteReceiptPDFView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generează un PDF cu confirmarea votului parlamentar"""
        vote_reference = request.GET.get('vote_reference')
        if not vote_reference:
            return Response({
                'error': 'Referința votului este obligatorie'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Verifică dacă referința votului există
        vote = ParliamentaryVote.objects.filter(vote_reference=vote_reference).first()
        if not vote:
            return Response({
                'error': 'Nu a fost găsit un vot cu această referință'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Generează PDF-ul
        buffer = io.BytesIO()
        self.create_pdf(buffer, vote.user, vote)
        buffer.seek(0)
        
        # Returnează PDF-ul ca răspuns
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="confirmare_vot_parlamentar_{vote_reference}.pdf"'
        return response
    
    def create_pdf(self, buffer, user, vote):
        """Creează documentul PDF cu confirmarea votului parlamentar"""
        # Configurează documentul
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Configurarea fonturilor cu suport pentru diacritice
        try:
            font_path = os.path.join(settings.BASE_DIR, 'vote', 'static', 'fonts')
            dejavu_regular = os.path.join(font_path, 'DejaVuSans.ttf')
            dejavu_bold = os.path.join(font_path, 'DejaVuSans-Bold.ttf')
            
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_regular))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold))
            font_name = 'DejaVuSans'
            bold_font_name = 'DejaVuSans-Bold'
        except Exception as e:
            # Folosim fonturile implicite în caz de eroare
            logger.error(f"Eroare la încărcarea fonturilor: {e}")
            font_name = 'Helvetica'
            bold_font_name = 'Helvetica-Bold'
        
        # Stiluri
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CenterTitle',
            parent=styles['Heading1'],
            fontName=bold_font_name,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='CenterNormal',
            parent=styles['Normal'],
            fontName=font_name,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='NormalRomanian',
            parent=styles['Normal'],
            fontName=font_name,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='Heading3Romanian',
            parent=styles['Heading3'],
            fontName=bold_font_name,
            spaceAfter=6
        ))
        
        # Elemente PDF
        elements = []
        
        # Titlu
        elements.append(Paragraph("CONFIRMARE VOT PARLAMENTAR - SMARTVOTE", styles['CenterTitle']))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Informații utilizator
        elements.append(Paragraph(f"Bună ziua, {user.first_name} {user.last_name}", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Vă mulțumim pentru participarea la procesul electoral. Votul dumneavoastră pentru alegerea Parlamentului României a fost înregistrat cu succes.", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Referință vot
        elements.append(Paragraph(f"Referință vot: {vote.vote_reference}", styles['CenterNormal']))
        elements.append(Paragraph(f"Data și ora: {vote.vote_datetime.strftime('%d-%m-%Y %H:%M:%S')}", styles['CenterNormal']))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Partidul votat
        elements.append(Paragraph("Partidul votat:", styles['Heading3Romanian']))
        
        # Tabel pentru partid
        data = [["Funcție", "Nume Partid", "Abreviere"]]
        data.append(["Parlament al României", vote.party.name, vote.party.abbreviation if vote.party.abbreviation else "-"])
        
        # Stilul pentru tabel
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        party_table = Table(data, style=table_style)
        elements.append(party_table)
        elements.append(Spacer(1, 0.25 * inch))
        
        # Avertisment și footer
        elements.append(Paragraph("ATENȚIE: Acest document este confidențial și servește drept confirmare a votului dumneavoastră.", styles['NormalRomanian']))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Toate drepturile rezervate © SmartVote 2024", styles['CenterNormal']))
        
        # Generează PDF-ul
        doc.build(elements)

# view pentru creearea propriului sistem de vot
class CreateVoteSystemView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Cream un serializator cu datele din request
        serializer = CreateVoteSystemSerializer(data=request.data)
        
        if serializer.is_valid():
            # Salvăm sistemul de vot
            vote_system = serializer.save(creator=request.user)
            
            # Returnăm datele sistemului creat
            return Response({
                'success': True,
                'message': 'Sistem de vot creat cu succes!',
                'system_id': vote_system.id
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserVoteSystemsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Obținem toate sistemele de vot create de utilizatorul curent
        vote_systems = VoteSystem.objects.filter(creator=request.user)
        
        # Actualizăm status-ul pentru fiecare sistem
        for system in vote_systems:
            system.update_status()
        
        # Serializăm datele
        serializer = VoteSystemSerializer(vote_systems, many=True)
        
        return Response(serializer.data)


class VoteSystemDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă utilizatorul are dreptul să vadă sistemul
            if vote_system.creator != request.user:
                return Response({
                    'error': 'Nu aveți permisiunea de a vedea acest sistem de vot.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Actualizăm status-ul
            vote_system.update_status()
            
            # Serializăm datele
            serializer = VoteSystemSerializer(vote_system)
            
            return Response(serializer.data)
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă utilizatorul are dreptul să modifice sistemul
            if vote_system.creator != request.user:
                return Response({
                    'error': 'Nu aveți permisiunea de a modifica acest sistem de vot.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Verificăm dacă sistemul poate fi modificat
            if vote_system.status != 'pending':
                return Response({
                    'error': 'Acest sistem nu mai poate fi modificat deoarece a început sau s-a încheiat.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Actualizăm datele
            serializer = CreateVoteSystemSerializer(vote_system, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                return Response({
                    'success': True,
                    'message': 'Sistem de vot actualizat cu succes!'
                })
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă utilizatorul are dreptul să șteargă sistemul
            if vote_system.creator != request.user:
                return Response({
                    'error': 'Nu aveți permisiunea de a șterge acest sistem de vot.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Ștergem sistemul
            vote_system.delete()
            
            return Response({
                'success': True,
                'message': 'Sistem de vot șters cu succes!'
            })
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)


class SubmitVoteView(APIView):
    def post(self, request, system_id):
        try:
            # Log pentru debugging
            print(f"Date primite: {request.data}")
            
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă sistemul este activ
            if vote_system.status != 'active':
                return Response({
                    'error': 'Acest sistem de vot nu este activ în acest moment.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obținem opțiunea pentru care s-a votat
            option_id = request.data.get('option_id')
            
            if not option_id:
                return Response({
                    'error': 'Trebuie să selectați o opțiune pentru a vota.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                option = VoteOption.objects.get(id=option_id, vote_system=vote_system)
            except VoteOption.DoesNotExist:
                return Response({
                    'error': 'Opțiunea selectată nu există pentru acest sistem de vot.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verificăm dacă utilizatorul a votat deja
            if request.user.is_authenticated:
                if VoteCast.objects.filter(vote_system=vote_system, user=request.user).exists():
                    return Response({
                        'error': 'Ați votat deja în acest sistem de vot.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Creăm votul pentru utilizator autentificat
                vote = VoteCast.objects.create(
                    vote_system=vote_system,
                    option=option,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            else:
                # Pentru voturile anonime, folosim o combinație IP + User Agent
                anonymous_id = self.generate_anonymous_id(request)
                
                if vote_system.rules.get('allow_anonymous_voting', False) is False:
                    return Response({
                        'error': 'Acest sistem de vot nu permite votul anonim. Vă rugăm să vă autentificați.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                if VoteCast.objects.filter(vote_system=vote_system, anonymous_id=anonymous_id).exists():
                    return Response({
                        'error': 'Se pare că ați votat deja în acest sistem de vot.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Creăm votul anonim
                vote = VoteCast.objects.create(
                    vote_system=vote_system,
                    option=option,
                    anonymous_id=anonymous_id,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            return Response({
                'success': True,
                'message': 'Votul dvs. a fost înregistrat cu succes!'
            })
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def generate_anonymous_id(self, request):
        """Generează un ID anonim bazat pe IP și User Agent"""
        import hashlib
        
        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        combined = f"{ip}:{user_agent}"
        return hashlib.md5(combined.encode()).hexdigest()
    
class AdminVerifyVoteSystemView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Obținem acțiunea
            action = request.data.get('action')
            reason = request.data.get('reason', '')
            
            if action == 'approve':
                vote_system.admin_verified = True
                vote_system.status = 'active'
                vote_system.verification_date = timezone.now()
                message = 'Sistem de vot aprobat cu succes!'
            elif action == 'reject':
                vote_system.status = 'rejected'
                vote_system.rejection_reason = reason
                vote_system.verification_date = timezone.now()
                message = 'Sistem de vot respins.'
            else:
                return Response({
                    'error': 'Acțiune invalidă. Folosiți "approve" sau "reject".'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            vote_system.save()
            
            return Response({
                'success': True,
                'message': message
            })
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
        
# clase pentru votul public        
class PublicVoteSystemView(APIView):
    permission_classes = [AllowAny]  # Permite accesul tuturor utilizatorilor
    
    def get(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă sistemul este activ sau finalizat
            if vote_system.status not in ['active', 'completed']:
                return Response({
                    'error': 'Acest sistem de vot nu este disponibil pentru vizualizare publică.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Actualizăm status-ul
            vote_system.update_status()
            
            # Serializăm datele
            serializer = VoteSystemSerializer(vote_system)
            
            return Response(serializer.data)
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)

class PublicSubmitVoteView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, system_id):
        try:
            # Logging pentru debugging
            print(f"Date primite în PublicSubmitVoteView: {request.data}")
            
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă sistemul este activ
            vote_system.update_status()
            
            if vote_system.status != 'active':
                return Response({
                    'error': 'Acest sistem de vot nu este activ în acest moment.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificăm dacă sistemul necesită verificare prin email
            if vote_system.require_email_verification:
                # Obținem token-ul și email-ul din request
                token_value = request.data.get('token')
                email = request.data.get('email')
                
                print(f"Verificare token: {token_value}, email: {email}")
                
                if not token_value or not email:
                    return Response({
                        'error': 'Token-ul și adresa de email sunt necesare pentru acest sistem de vot.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Căutăm token-ul în baza de date
                try:
                    token = VoteToken.objects.get(
                        vote_system=vote_system, 
                        token=token_value,
                        email=email
                    )
                    
                    # Verificăm dacă token-ul este valid
                    if token.used:
                        return Response({
                            'error': 'Acest token a fost deja folosit.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    if token.expires_at < timezone.now():
                        return Response({
                            'error': 'Acest token a expirat.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                except VoteToken.DoesNotExist:
                    return Response({
                        'error': 'Token invalid sau adresă de email incorectă.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obținem opțiunea pentru care s-a votat
            option_id = request.data.get('option_id')
            
            if not option_id:
                print("Eroare: Lipsește option_id din request")
                return Response({
                    'error': 'Trebuie să selectați o opțiune pentru a vota.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                option = VoteOption.objects.get(id=option_id, vote_system=vote_system)
                print(f"Opțiune găsită: {option.id} - {option.title}")
            except VoteOption.DoesNotExist:
                return Response({
                    'error': 'Opțiunea selectată nu există pentru acest sistem de vot.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verificăm dacă există deja un vot cu același anonymous_id
            ip_address = self.get_client_ip(request)
            anonymous_id = self.generate_anonymous_id(request)
            
            # Verificăm dacă există deja un vot pentru acest anonymous_id
            existing_vote = VoteCast.objects.filter(
                vote_system=vote_system,
                anonymous_id=anonymous_id
            ).first()
            
            if existing_vote:
                return Response({
                    'error': 'Se pare că ați votat deja în acest sistem de vot.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Creăm votul anonim
            vote = VoteCast.objects.create(
                vote_system=vote_system,
                option=option,
                anonymous_id=anonymous_id,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            print(f"Vot creat cu succes: ID {vote.id} pentru opțiunea {option.title}")
            
            # Dacă sistemul necesită verificare prin email, marcăm token-ul ca folosit
            if vote_system.require_email_verification and 'token' in locals():
                token.used = True
                token.used_at = timezone.now()
                token.ip_address = ip_address
                token.save()
                print(f"Token marcat ca folosit: {token.token}")
            
            # Generăm un token de confirmare pentru vot
            vote_confirmation = self.generate_vote_confirmation(vote.id)
            
            return Response({
                'success': True,
                'message': 'Votul dvs. a fost înregistrat cu succes!',
                'vote_confirmation': vote_confirmation
            })
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Eroare generală în PublicSubmitVoteView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Eroare internă: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Obține adresa IP a clientului"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def generate_anonymous_id(self, request):
        """Generează un ID anonim bazat pe IP și User Agent"""
        import hashlib
        
        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        combined = f"{ip}:{user_agent}"
        return hashlib.md5(combined.encode()).hexdigest()
        
    def generate_vote_confirmation(self, vote_id):
        """Generează un token de confirmare pentru vot"""
        import hashlib
        import time
        
        salt = str(time.time())
        token_input = f"{vote_id}:{salt}"
        return hashlib.sha256(token_input.encode()).hexdigest()

# Adaugă această clasă pentru rezultatele publice
class PublicVoteResultsView(APIView):
    permission_classes = [AllowAny]  # Permite accesul tuturor utilizatorilor
    
    def get(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă rezultatele pot fi afișate public
            result_visibility = vote_system.rules.get('result_visibility', 'after_end')
            current_time = timezone.now()
            
            if result_visibility == 'hidden':
                return Response({
                    'error': 'Rezultatele acestui vot nu sunt disponibile public.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if result_visibility == 'after_end' and current_time < vote_system.end_date:
                return Response({
                    'error': 'Rezultatele vor fi disponibile după încheierea perioadei de vot.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Serializăm datele
            serializer = VoteSystemSerializer(vote_system)
            
            return Response(serializer.data)
        
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
        
class ManageVoterEmailsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă utilizatorul are dreptul să modifice sistemul
            if vote_system.creator != request.user:
                return Response({
                    'error': 'Nu aveți permisiunea de a modifica acest sistem de vot.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Procesăm lista de emailuri
            emails_data = request.data.get('emails', '')
            
            # Debug pentru a vedea ce se primește
            print(f"Datele primite pentru email-uri: {emails_data}")
            
            form = EmailListForm({'emails': emails_data})
            
            if form.is_valid():
                emails = form.cleaned_data['emails']
                
                # Debug pentru a vedea ce rezultă după procesare
                print(f"Email-uri procesate: {emails}")
                
                # Actualizăm sistemul de vot cu opțiunea de verificare prin email
                vote_system.require_email_verification = True
                vote_system.allowed_emails = ','.join(emails)
                vote_system.save()
                
                # Returnăm răspunsul
                return Response({
                    'success': True,
                    'message': f'Au fost adăugate {len(emails)} adrese de email.',
                    'emails_count': len(emails)
                })
            else:
                print(f"Erori validare email-uri: {form.errors}")
                return Response({
                    'success': False,
                    'errors': form.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Eroare generală în ManageVoterEmailsView: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SendVoteTokensView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă utilizatorul are dreptul să modifice sistemul
            if vote_system.creator != request.user:
                return Response({
                    'error': 'Nu aveți permisiunea de a gestiona acest sistem de vot.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Verificăm dacă sunt adrese de email configurate
            if not vote_system.allowed_emails:
                return Response({
                    'error': 'Nu există adrese de email configurate pentru acest sistem de vot.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obținem lista de emailuri
            emails = [email.strip() for email in vote_system.allowed_emails.split(',') if email.strip()]
            
            # Generăm și trimitem token-uri pentru fiecare email
            tokens_created = 0
            emails_sent = 0
            
            # Folosește întotdeauna IP-ul de rețea pentru link-urile din email
            network_ip = getattr(settings, 'NETWORK_IP', '192.168.29.140')
            frontend_url = f"http://{network_ip}:4200"
            
            print(f"Folosim URL de rețea pentru email: {frontend_url}")
            
            for email in emails:
                # Verificăm dacă există deja un token pentru acest email
                token, created = VoteToken.objects.get_or_create(
                    vote_system=vote_system,
                    email=email,
                    defaults={
                        'token': VoteToken.generate_token(),
                        'expires_at': timezone.now() + timedelta(minutes=3)
                    }
                )
                
                # Dacă token-ul a fost deja folosit sau a expirat, generăm unul nou
                if not token.is_valid():
                    token.token = VoteToken.generate_token()
                    token.expires_at = timezone.now() + timedelta(minutes=3)
                    token.used = False
                    token.used_at = None
                    token.save()
                
                if created or not token.is_valid():
                    tokens_created += 1
                
                # Generăm URL-ul pentru pagina de vot folosind IP-ul de rețea
                vote_url = f"{frontend_url}/vote/{vote_system.id}?token={token.token}&email={email}"
                print(f"URL generat pentru email: {vote_url}")
                
                # Trimitem email-ul cu token-ul
                try:
                    # Pregătim contextul pentru șablon
                    context = {
                        'vote_system': vote_system,
                        'token': token.token,
                        'expires_at': token.expires_at,
                        'vote_url': vote_url  # URL-ul complet cu IP-ul de rețea
                    }
                    
                    # Încercăm să folosim template-urile, dar avem și o variantă de backup
                    try:
                        html_message = render_to_string('vote_token.html', context)
                        plain_message = render_to_string('vote_token_plain.txt', context)
                    except Exception as template_error:
                        print(f"Eroare la randarea template-ului: {str(template_error)}")
                        
                        # Folosim un string HTML direct cu URL-ul de rețea
                        html_message = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Codul tău de vot pentru {vote_system.name}</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                                .container {{ border: 1px solid #ddd; border-radius: 5px; padding: 20px; background-color: #f9f9f9; }}
                                .header {{ text-align: center; margin-bottom: 20px; }}
                                .token {{ background-color: #e9f7fe; color: #0078d4; font-size: 24px; font-weight: bold; text-align: center; padding: 15px; margin: 20px 0; border-radius: 5px; letter-spacing: 2px; }}
                                .info {{ margin-bottom: 15px; }}
                                .footer {{ font-size: 12px; color: #777; margin-top: 30px; text-align: center; }}
                                .button {{ display: inline-block; background-color: #0078d4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h1>SmartVote</h1>
                                    <h2>Codul tău de vot</h2>
                                </div>
                                
                                <div class="info">
                                    <p>Dragă participant,</p>
                                    <p>Ai fost invitat să participi la votul: <strong>{vote_system.name}</strong>.</p>
                                    <p>Pentru a-ți valida votul, te rugăm să folosești codul de mai jos:</p>
                                </div>
                                
                                <div class="token">
                                    {token.token}
                                </div>
                                
                                <div class="info">
                                    <p><strong>Important:</strong> Acest cod este valabil doar pentru 3 minute și poate fi folosit o singură dată.</p>
                                    <p>Expiră la: {token.expires_at.strftime('%d.%m.%Y %H:%M:%S')}</p>
                                    
                                    <p>Pentru a vota, accesează link-ul de mai jos și introdu codul când ți se solicită:</p>
                                    <div style="text-align: center;">
                                        <a href="{vote_url}" class="button">Accesează pagina de vot</a>
                                    </div>
                                </div>
                                
                                <div class="footer">
                                    <p>Acest email a fost trimis automat. Te rugăm să nu răspunzi la acest mesaj.</p>
                                    <p>&copy; 2023 SmartVote. Toate drepturile rezervate.</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        plain_message = f"""
                        SmartVote - Codul tău de vot
                        
                        Dragă participant,
                        
                        Ai fost invitat să participi la votul: {vote_system.name}.
                        
                        Pentru a-ți valida votul, te rugăm să folosești următorul cod:
                        
                        {token.token}
                        
                        Important: Acest cod este valabil doar pentru 3 minute și poate fi folosit o singură dată.
                        Expiră la: {token.expires_at.strftime('%d.%m.%Y %H:%M:%S')}
                        
                        Pentru a vota, accesează link-ul de mai jos și introdu codul când ți se solicită:
                        {vote_url}
                        
                        Acest email a fost trimis automat. Te rugăm să nu răspunzi la acest mesaj.
                        
                        © 2023 SmartVote. Toate drepturile rezervate.
                        """
                    
                    # Trimitem email-ul
                    send_mail(
                        subject=f"[SmartVote] Codul tău de vot pentru {vote_system.name}",
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False
                    )
                    print(f"Email trimis cu succes către {email} cu link: {vote_url}")
                    emails_sent += 1
                    
                except Exception as e:
                    print(f"Eroare la trimiterea email-ului către {email}: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            return Response({
                'success': True,
                'message': f'Au fost trimise {emails_sent} email-uri cu coduri de vot.',
                'tokens_created': tokens_created,
                'emails_sent': emails_sent
            })
            
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Eroare generală în SendVoteTokensView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VerifyVoteTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, system_id):
        try:
            # Obținem sistemul de vot
            vote_system = VoteSystem.objects.get(id=system_id)
            
            # Verificăm dacă sistemul necesită verificare prin email
            if not vote_system.require_email_verification:
                return Response({
                    'valid': True,
                    'message': 'Acest sistem de vot nu necesită verificare prin email.'
                })
            
            # Obținem token-ul și email-ul din request
            token_value = request.data.get('token')
            email = request.data.get('email')
            
            print(f"Verificare token: {token_value}, email: {email}")
            
            if not token_value or not email:
                return Response({
                    'valid': False,
                    'message': 'Token-ul și adresa de email sunt necesare.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Căutăm token-ul în baza de date
            try:
                token = VoteToken.objects.get(
                    vote_system=vote_system, 
                    token=token_value,
                    email=email
                )
                
                # Verificăm dacă token-ul este valid
                if token.used:
                    return Response({
                        'valid': False,
                        'message': 'Acest token a fost deja folosit.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if token.expires_at < timezone.now():
                    return Response({
                        'valid': False,
                        'message': 'Acest token a expirat.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # La acest punct, token-ul este valid
                # Returnăm token-ul original (important!)
                return Response({
                    'valid': True,
                    'session_token': token.token,  # Folosim token-ul original
                    'message': 'Token valid. Puteți continua cu votul.'
                })
                
            except VoteToken.DoesNotExist:
                return Response({
                    'valid': False,
                    'message': 'Token invalid sau adresă de email incorectă.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except VoteSystem.DoesNotExist:
            return Response({
                'error': 'Sistemul de vot nu a fost găsit.'
            }, status=status.HTTP_404_NOT_FOUND)
        
class CheckActiveVoteSystemView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Verificăm dacă utilizatorul are deja un sistem de vot activ sau în așteptare
        active_systems = VoteSystem.objects.filter(
            creator=request.user,
            status__in=['active', 'pending']
        ).order_by('-created_at')
        
        if active_systems.exists():
            # Actualizăm status-ul primului sistem găsit
            active_system = active_systems.first()
            active_system.update_status()
            
            # Serializăm și returnăm sistemul activ
            serializer = VoteSystemSerializer(active_system)
            return Response({
                'has_active_system': True,
                'system': serializer.data
            })
        
        return Response({
            'has_active_system': False,
            'system': None
        })