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