from django.shortcuts import render, redirect
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from django.core.mail import send_mail
from django.http import JsonResponse
from .forms import RegistrationForm, IDCardForm
from .models import User
from .serializers import UserSerializer
from django.views.decorators.csrf import csrf_exempt
#from .utils import extract_text_from_image, is_valid_id_card, parse_id_card
import random, jwt, datetime, json
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from allauth.socialaccount.models import SocialAccount  
from django.shortcuts import render
from decouple import config
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from transformers import pipeline
import re
import os
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from .utils import IDCardProcessor
from PIL import Image
import pytesseract
from .utils import IDCardDetector
import cv2
from .utils import ImageManipulator
from .utils import extract_text, load_valid_keywords
from .utils import LocalityMatcher
import logging
from .utils import ImageScanner
import tracemalloc # pentru a monitoriza consumul de memorie
import gc # pentru a elibera manual memoria utilizata de imaginile temporare
import face_recognition
import numpy as np
import io
from ultralytics import YOLO 
import concurrent.futures
from .serializers import IDCardRegistrationSerializer
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from .utils import verify_recaptcha
import pyotp
from account_settings.models import AccountSettings
from .utils import ProcessorCNP
from security.utils import create_security_event, log_captcha_attempt, log_2fa_event, log_gdpr_event
from django.utils import timezone
from core.ai_services import face_recognition_service, id_card_service


logger = logging.getLogger(__name__)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_endpoint(request):
    return Response({
        'status': 'OK',
        'method': request.method,
        'user_authenticated': request.user.is_authenticated,
        'timestamp': timezone.now().isoformat()
    })

class RegisterWithIDCardView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = IDCardRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # Verifică dacă utilizatorul este major
            cnp = serializer.validated_data.get("cnp")
            if cnp:
                processor_cnp = ProcessorCNP()
                if not processor_cnp.este_major(cnp):
                    create_security_event(
                        user=None,  # Nu avem utilizator la acest pas
                        event_type='profile_update',
                        description=f"Încercare înregistrare minor cu CNP: {cnp[:3]}***",
                        drequest=request,
                        risk_level='high'
                    )
                    return Response(
                        {'error': 'Înregistrarea este permisă doar persoanelor majore (peste 18 ani).'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Verificăm dacă utilizatorul există deja
            cnp = serializer.validated_data.get("cnp")
            email = serializer.validated_data.get("email")

            existing_user = None
            if cnp:
                existing_user = User.objects.filter(cnp=cnp).first()
            elif email:
                existing_user = User.objects.filter(email=email).first()

            if existing_user:
                create_security_event(
                    user=existing_user,
                    event_type='profile_update',
                    description=f"Încercare înregistrare dublă pentru {email or 'CNP: ' + cnp[:3] + '***'}",
                    drequest=request,
                    risk_level='medium'
                )
                return Response({'error': 'Utilizatorul există deja. Încearcă să te autentifici.'}, status=status.HTTP_400_BAD_REQUEST)

            # Cream un nou utilizator
            user = serializer.save(is_active=False, is_verified_by_id=True)  # 🔹 Initial, contul este inactiv

            create_security_event(
                user=user,
                event_type='profile_update',
                description=f"Cont nou creat cu buletin pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
                request=request,
                additional_data={
                    'registration_method': 'id_card',
                    'has_email': bool(user.email),
                    'is_verified_by_id': True
                },
            )
            log_gdpr_event(
                user=user,
                action='id_card_registration_consent',
                request=request
            )
           
           
            # Salvam imaginea buletinului daca este incarcata
            image = request.FILES.get('id_card_image')
            if image:
                user.id_card_image.save(f'id_cards/{user.id}_{image.name}', image, save=True)

                create_security_event(
                    user=user,
                    event_type='id_card_scan_success',
                    description=f"Imagine buletin salvată pentru {user.cnp[:3]}***",
                    request=request,
                    risk_level='low'
                )

                # Log pentru scanarea reusita a buletinului
                create_security_event(
                    user=user,
                    event_type='id_card_scan_success', 
                    description=f"Scanare buletin reușită pentru utilizator {user.cnp[:3]}***",
                    request=request,
                    additional_data={
                        'image_uploaded': True,
                        'registration_method': 'id_card'
                    },
                    risk_level='low'
                )


            return Response({'message': 'Înregistrare cu buletinul completată cu succes!'}, status=status.HTTP_201_CREATED)

        create_security_event(
            user=None,  
            event_type='profile_update',
            description="Încercare eșuată de înregistrare cu buletin - erori de validare",
            request=request,
            additional_data={'errors': serializer.errors},
            risk_level='medium'
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Calea catre modelul de anti - spoofing
MODEL_PATH = r"C:\Users\brj\Desktop\voting\media\models\l_version_1_300.pt"

class FaceRecognitionView(APIView):
    permission_classes = [AllowAny]
    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     # Incarca modelul YOLO pentru detectarea spoofing-ului
    #     self.model = YOLO(MODEL_PATH)

    def detect_spoofing(self, image_array):
        """Verifica daca imaginea este reala sau falsa folosind YOLO."""
        try:
            # Redimensionare imagine pentru procesare mai rapidă
            h, w = image_array.shape[:2]
            scale = min(1.0, 640 / max(h, w))
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                image_array = cv2.resize(image_array, (new_w, new_h))

            # Normalizare imagine si detectie spoofing cu YOLO 
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            normalized = cv2.equalizeHist(gray)
            image_array = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)

            # Optimizare inferență YOLO
            results = self.model(image_array, stream=True, verbose=False, conf=0.6)

            for r in results:
                for box in r.boxes:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())  # 0 = fake, 1 = real
                    
                    logger.info(f"Detectare spoofing - Scor: {conf}, Clasificare: {cls}")
                    
                    return cls == 1  # Returăm imediat primul rezultat care depășește pragul

            return False
        except Exception as e:
            logger.error(f"Eroare la detectarea spoofing-ului: {e}")
            return False

    def detect_and_encode_face(self, image_array):
        """Detecteaza si extrage encoding-ul fetei."""
        try:
            # Redimensionează imaginea pentru procesare mai rapidă
            h, w = image_array.shape[:2]
            scale = min(1.0, 480 / max(h, w))
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                small_image = cv2.resize(image_array, (new_w, new_h))
            else:
                small_image = image_array.copy()
            
            # Folosește doar HOG pentru detectare, care este mai rapid
            face_locations = face_recognition.face_locations(small_image, model="hog")

            if len(face_locations) == 0:
                return None, "Nicio fata detectata in imagine. Verificati pozitia si iluminarea."

            if len(face_locations) > 1:
                return None, "S-au detectat mai multe fete. Procesul necesita o singura fata."

            # Dacă am redimensionat, ajustăm locațiile fețelor înapoi la dimensiunea originală
            if scale < 1.0:
                adjusted_locations = []
                for top, right, bottom, left in face_locations:
                    adjusted_locations.append(
                        (int(top / scale), int(right / scale), 
                         int(bottom / scale), int(left / scale))
                    )
                face_encodings = face_recognition.face_encodings(image_array, known_face_locations=adjusted_locations)
            else:
                face_encodings = face_recognition.face_encodings(image_array, known_face_locations=face_locations)

            if len(face_encodings) == 0:
                return None, "Codificarea fetei a esuat"

            return face_encodings[0], None
        except Exception as e:
            logger.error(f"Eroare la detectarea/codificarea fetei: {e}")
            return None, f"Eroare la detectarea fetei: {e}"

    def compare_faces(self, id_card_array, live_array):
        """Compara fetele doar daca imaginea live este autentica."""
        try:
            # Executăm detectarea spoofing-ului și encoding-ul feței simultan pentru a economisi timp
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                spoofing_future = executor.submit(self.detect_spoofing, live_array)
                id_card_future = executor.submit(self.detect_and_encode_face, id_card_array)
                
                # Așteaptă finalizarea verificării spoofing
                is_real = spoofing_future.result()
                if not is_real:
                    return False, "Frauda detectata: folositi o imagine reala!"
                
                # Obține rezultatele encoding-ului feței din ID
                id_card_encoding, id_card_error = id_card_future.result()
                if id_card_encoding is None:
                    return False, id_card_error
                
                # Acum face encoding pentru imaginea live
                live_encoding, live_error = self.detect_and_encode_face(live_array)
                if live_encoding is None:
                    return False, live_error

            # Compararea fețelor
            face_distance = np.linalg.norm(id_card_encoding - live_encoding)
            match = face_distance < 0.6

            return match, "Identificare reusita!" if match else "Fetele nu se potrivesc."
        except Exception as e:
            logger.error(f"Eroare la compararea fetelor: {e}")
            return False, f"Eroare la compararea fetelor: {e}"

    def post(self, request):
        """Primeste imaginile si verifica autenticitatea + compara fetele."""
        try:
            id_card_image = request.FILES.get('id_card_image')
            live_image = request.FILES.get('live_image')

            if not id_card_image or not live_image:
                return Response({'error': 'Fisiere lipsa'}, status=status.HTTP_400_BAD_REQUEST)

            # Optimizare: Reducem dimensiunea imaginilor înainte de a le încărca în memorie
            id_card_pil = Image.open(io.BytesIO(id_card_image.read())).convert("RGB")
            live_pil = Image.open(io.BytesIO(live_image.read())).convert("RGB")
            
            # Redimensionează imaginile dacă sunt prea mari
            max_size = 1024
            if max(id_card_pil.size) > max_size:
                id_card_pil.thumbnail((max_size, max_size), Image.LANCZOS)
            if max(live_pil.size) > max_size:
                live_pil.thumbnail((max_size, max_size), Image.LANCZOS)
                
            id_card_array = np.array(id_card_pil)
            live_array = np.array(live_pil)

            match, message = face_recognition_service.compare_faces(id_card_array, live_array)

            return Response({'message': message, 'match': match}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Eroare server: {e}")
            return Response({'error': 'Eroare internă server'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

toxic_classifier = pipeline("text-classification", model="unitary/toxic-bert")



def contains_profanity_with_ai(message):
    """
    Detectează limbaj nepotrivit în mesaj folosind AI.
    """
    sentences = re.split(r'[.!?]', message)  # impartim mesajul în propozitii
    for sentence in sentences:
        if sentence.strip():  # Ignoram propozitiile goale
            result = toxic_classifier(sentence)
            for label in result:
                if label["label"] == "LABEL_1" and label["score"] > 0.5:
                    return True
    return False

@api_view(['POST'])
@permission_classes([AllowAny])
def check_profanity(request):
    """
    Endpoint pentru verificarea limbajului nepotrivit.
    """
    message = request.data.get('message', '')
    if contains_profanity_with_ai(message):
        return Response({'containsProfanity': True}, status=200)
    return Response({'containsProfanity': False}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_feedback(request):
    feedback_data = {
        'name': request.data.get('name', '').strip(),
        'phone': request.data.get('phone', '').strip(),
        'email': request.user.email,
        'message': request.data.get('message', '').strip()
    }

    # Validare mesaj pentru injurii
    if contains_profanity_with_ai(feedback_data['message']):
        return Response({'error': 'Mesajul conține limbaj nepotrivit și nu poate fi trimis.'}, status=400)

    # Alte validari si trimiterea mesajului
    feedback_template = render_to_string('feedback_email.html', feedback_data)
    email = EmailMessage(
        subject='Feedback de la utilizator',
        body=feedback_template,
        from_email=config('DEFAULT_FROM_EMAIL'),
        to=[config('ADMIN_EMAIL')],
        reply_to=[feedback_data['email']],
    )
    email.content_subtype = 'html'
    email.send()

    return Response({'message': 'Feedback-ul a fost trimis cu succes!'}, status=200)


# Functie pentru validarea numelui
def validate_name(name):
    return name.isalpha() and len(name) > 1

# Functie pentru validarea telefonului
def validate_phone(phone, prefix):
    return phone.startswith(prefix) and phone.replace(prefix, '').isdigit()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_feedback(request):
    feedback_data = {
        'name': request.data.get('name', '').strip(),
        'phone': request.data.get('phone', '').strip(),
        'email': request.user.email,
        'message': request.data.get('message', '').strip()
    }

    # Validare: numele trebuie sa fie valid
    if not validate_name(feedback_data['name']):
        return Response({'error': 'Nume invalid. Verificati introducerea.'}, status=400)

    # Validare: numarul de telefon trebuie sa fie valid
    if not validate_phone(feedback_data['phone'], "RO"):
        return Response({'error': 'Numar de telefon invalid. Verificati prefixul si numărul.'}, status=400)

    # Validare: mesajul sa nu contina injurii
    if contains_profanity_with_ai(feedback_data['message']):
        return Response({'error': 'Mesajul contine limbaj nepotrivit si nu a fost trimis.'}, status=400)

    # Validare: mesajul trebuie sa aiba cel putin 20 de cuvinte
    if len(feedback_data['message'].split()) < 20:
        return Response({'error': 'Mesajul trebuie sa contina cel putin 20 de cuvinte.'}, status=400)

    # Trimiterea feedback-ului daca toate conditiile sunt satisfăcute
    feedback_template = render_to_string('feedback_email.html', feedback_data)
    email = EmailMessage(
        subject='Feedback de la utilizator',
        body=feedback_template,
        from_email=config('DEFAULT_FROM_EMAIL'),
        to=[config('ADMIN_EMAIL')],
        reply_to=[feedback_data['email']],
    )
    email.content_subtype = 'html'
    email.send()

    return Response({'message': 'Feedback-ul a fost trimis cu succes!'}, status=200)



def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    return render(request, 'terms_of_service.html')

def social_login_redirect(request, provider):
    #stiluri pt pagina
    provider_class = 'google-logo' if provider == 'Google' else 'facebook-logo'
    context = {
        'provider': provider,
        'provider_class': provider_class
    }
    return render(request, 'social_login_redirect.html', context)

#view pt incarcarea unei imagini cu buletinul
class UploadIdView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Citim cuvintele cheie din fisierul CSV
        self.valid_keywords = load_valid_keywords(settings.VALID_KEYWORDS_CSV)
    

    def post(self, request):
        image = request.FILES.get('id_card_image')
        if not image:
            return Response({'error': 'Niciun fișier nu a fost încărcat'}, status=status.HTTP_400_BAD_REQUEST)

        # Salvam imaginea pe disc
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, image.name)

        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        # Detectam cartea de identitate
        detector = IDCardDetector()
        cropped_image = detector.detect_id_card(file_path)

        if cropped_image is None:
            return Response({'error': 'Nu s-a putut detecta cartea de identitate'}, status=status.HTTP_400_BAD_REQUEST)

        # Salvam imaginea decupata
        cropped_file_path = file_path.replace('.jpg', '_cropped.jpg')
        cv2.imwrite(cropped_file_path, cropped_image)

        # Aplicam OCR pentru a extrage textul
        extracted_text = extract_text(cropped_file_path)

        # Dacă textul nu este detectat, încercăm cu imaginea oglindită

        is_valid_id = any(keyword in extracted_text.upper() for keyword in self.valid_keywords)

        if not is_valid_id:
            create_security_event(
                user=request.user if request.user.is_authenticated else None,
                event_type='id_card_scan_failed',
                description="Scanare buletin eșuată - document invalid",
                request=request,
                risk_level='medium'
            )
            # Oglindim imaginea și rulăm OCR din nou
            flipped_image = cv2.flip(cropped_image, 1)  # 1 pentru oglindire orizontala
            flipped_file_path = cropped_file_path.replace('.jpg', '_flipped.jpg')
            cv2.imwrite(flipped_file_path, flipped_image)
            extracted_text_flipped = extract_text(flipped_file_path)

            # Verificăm dacă imaginea oglindită conține text valid
            is_valid_id = any(keyword in extracted_text_flipped.upper() for keyword in self.valid_keywords)

        if not is_valid_id:
            return Response({'error': 'Imaginea încărcată nu corespunde unui act de identitate'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        create_security_event(
            user=request.user if request.user.is_authenticated else None,
            event_type='id_card_scan_success',
            description="Scanare și validare buletin reușită",
            request=request,
            risk_level='low'
        )

        return Response({
            'message': 'Imaginea a fost încărcată și procesată cu succes.',
            'cropped_image_path': os.path.join(settings.MEDIA_URL, 'uploads', os.path.basename(cropped_file_path))
        }, status=status.HTTP_200_OK)
    

class ValidateLocalityView(APIView):
    """
    View îmbunătățit pentru validarea și sugerarea localităților.
    """
    permission_classes = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.matcher = LocalityMatcher(settings.LOCALITATI_CSV_PATH)
        except Exception as e:
            logger.error(f"Eroare la inițializarea LocalityMatcher: {str(e)}")
            self.matcher = None

    def post(self, request):
        if self.matcher is None:
            return Response(
                {'error': 'Serviciul de validare a localităților nu este disponibil'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        locality = request.data.get('locality', '').strip()
        if not locality:
            return Response(
                {'error': 'Localitatea nu a fost specificată'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Configurăm parametrii de căutare
            top_n = request.data.get('top_n', 5)
            min_similarity = request.data.get('min_similarity', 0.1)
            
            # Validăm parametrii
            try:
                top_n = int(top_n)
                min_similarity = float(min_similarity)
                if top_n < 1 or min_similarity < 0 or min_similarity > 1:
                    raise ValueError
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Parametri invalizi pentru căutare'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            matches = self.matcher.find_best_matches(
                locality,
                top_n=top_n,
                min_similarity=min_similarity
            )

            if matches:
                return Response({
                    'matches': matches,
                    'input_processed': self.matcher.preprocess_locality(locality)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Nicio potrivire găsită',
                    'input_processed': self.matcher.preprocess_locality(locality)
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Eroare la procesarea localității '{locality}': {str(e)}")
            return Response(
                {'error': 'Eroare la procesarea cererii'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ManipulateImageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            image_path = request.data.get('image_path')
            action = request.data.get('action')
            angle = int(request.data.get('angle', 0)) if action == 'rotate' else None

            if not image_path or not action:
                return Response({'error': 'Parametrii lipsă'}, status=status.HTTP_400_BAD_REQUEST)

            # Curata calea imaginii
            if image_path.startswith(settings.MEDIA_URL):
                image_path = image_path.replace(settings.MEDIA_URL, '')
            if image_path.startswith('http://') or image_path.startswith('https://'):
                image_path = image_path.split('/media/')[-1]
            
            # Elimina parametrii query
            image_path = image_path.split('?')[0]
            
            image_full_path = os.path.join(settings.MEDIA_ROOT, image_path)

            if not os.path.exists(image_full_path):
                return Response({'error': f'Imaginea nu există la calea: {image_full_path}'}, 
                              status=status.HTTP_404_NOT_FOUND)

            # Determina numele fisierului si extensia
            directory = os.path.dirname(image_full_path)
            filename = os.path.basename(image_full_path)
            base_name, ext = os.path.splitext(filename)

            # Genereaza un nou nume de fisier bazat pe actiune
            if action == 'rotate':
                new_base_name = f"{base_name}rotated{angle}"
            else:  # flip
                if '_flipped' in base_name:
                    # Daca imaginea este deja oglindita, revenim la versiunea neoglindita
                    new_base_name = base_name.replace('_flipped', '')
                else:
                    new_base_name = f"{base_name}_flipped"

            new_file_path = os.path.join(directory, f"{new_base_name}{ext}")

            # Efectueaza manipularea imaginii
            if action == 'rotate':
                manipulated_image = ImageManipulator.rotate_image(image_full_path, angle)
            elif action == 'flip':
                manipulated_image = ImageManipulator.flip_image(image_full_path)
            else:
                return Response({'error': 'Acțiune invalidă'}, status=status.HTTP_400_BAD_REQUEST)

            # Salveaza noua imagine
            cv2.imwrite(new_file_path, manipulated_image)

            # Creeaza calea relativa pentru URL
            relative_path = os.path.relpath(new_file_path, settings.MEDIA_ROOT).replace('\\', '/')

            return Response({
                'message': f'Imaginea a fost manipulată cu succes ({action}).',
                'manipulated_image_path': f"{settings.MEDIA_URL}{relative_path}"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
class ScanIdView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    def post(self, request):
        # Verifică dacă imaginea a fost trimisă
        image = request.FILES.get('camera_image')
        if not image:
            return Response({'error': 'Niciun fișier nu a fost încărcat.'}, status=status.HTTP_400_BAD_REQUEST)

        # Salvează imaginea originală
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'camera')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, image.name)

        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        # Aplică detectarea cărții de identitate
        detector = IDCardDetector()
        cropped_image = detector.detect_id_card(file_path)

        if cropped_image is None:
            return Response({'error': 'Nu s-a putut detecta cartea de identitate.'}, status=status.HTTP_400_BAD_REQUEST)

        # Salvează imaginea decupată
        cropped_file_path = file_path.replace('.jpg', '_cropped.jpg')  # Schimbă extensia dacă imaginea nu este .jpg
        cv2.imwrite(cropped_file_path, cropped_image)

        # Aplică transformarea într-o versiune "scanată"
        enhanced_file_path = cropped_file_path.replace('_cropped.jpg', '_enhanced.jpg')  # Schimbă extensia dacă este .png
        try:
            ImageScanner.save_enhanced_image(cropped_file_path, enhanced_file_path)
        except Exception as e:
            return Response({'error': f'Eroare la procesarea imaginii: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Returnează răspunsul cu calea imaginii procesate
        return Response({
            'message': 'Imaginea a fost încărcată și procesată cu succes.',
            'cropped_image_path': os.path.join(settings.MEDIA_URL, 'camera', os.path.basename(cropped_file_path)),
            'enhanced_image_path': os.path.join(settings.MEDIA_URL, 'camera', os.path.basename(enhanced_file_path))
        }, status=status.HTTP_200_OK)

class AutofillScanDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Obține calea imaginii decupate din cerere
        cropped_file_path = request.data.get('cropped_file_path')
        if not cropped_file_path:
            return Response({'error': 'Calea fișierului este necesară.'}, status=status.HTTP_400_BAD_REQUEST)

        # Construiește calea completă către fișierul din backend
        absolute_path = os.path.join(settings.MEDIA_ROOT, cropped_file_path.lstrip('/'))

        if not os.path.exists(absolute_path):
            return Response({'error': 'Fișierul nu a fost găsit.'}, status=status.HTTP_404_NOT_FOUND)

        # Procesează imaginea cu modelul IDCardProcessor
        # processor = IDCardProcessor()
        # extracted_info = processor.process_id_card(absolute_path)
        extracted_info = id_card_service.process_id_card(absolute_path)

        return Response({
            'message': 'Datele au fost extrase cu succes.',
            'extracted_info': extracted_info
        }, status=status.HTTP_200_OK)
class ValidateRomanianID(APIView):
    def post(self, request):
        image = request.FILES.get('camera_image')
        if not image:
            return Response({'error': 'Niciun fișier nu a fost încărcat'}, status=status.HTTP_400_BAD_REQUEST)

        # Salvează imaginea
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'camera')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, image.name)

        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        # Validăm textul pentru "ROMANIA"
        extracted_text = pytesseract.image_to_string(Image.open(file_path))
        if "ROMANIA" not in extracted_text and "ROU" not in extracted_text:
            return Response({'error': 'Se acceptă doar cărți de identitate românești.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Validarea a fost realizată cu succes.', 'file_path': file_path}, status=status.HTTP_200_OK)

class DetectIDCardView(APIView):
    """
    Endpoint pentru detectarea și decuparea cărților de identitate.
    """
    permission_classes=[AllowAny]
    def post(self, request):
        file = request.FILES.get('image')
        if not file:
            return Response({"error": "Niciun fișier încărcat"}, status=400)

        file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb+') as f:
            for chunk in file.chunks():
                f.write(chunk)

        detector = IDCardDetector()
        cropped_image = detector.detect_id_card(file_path)
        if cropped_image is None:
            return Response({"error": "Carte de identitate nedetectată"}, status=400)

        # Salvăm imaginea decupată
        cropped_path = file_path.replace('.png', '_cropped.png')
        cv2.imwrite(cropped_path, cropped_image)

        return Response({"cropped_image_path": cropped_path.replace(settings.MEDIA_ROOT, '/media/')}, status=200)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', None)
        cnp = request.data.get('cnp', None)

        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            #creeaza un nou utilizator
            user = serializer.save()
            user.is_active = False # initial contul este inactiv pentru toti utilizatorii noi

            create_security_event(
                user=user,
                event_type='profile_update',
                description=f"Cont nou creat pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
                request=request,
                additional_data={
                    'registration_method': 'email' if email else 'cnp',
                    'has_email': bool(email),
                    'has_cnp': bool(cnp)
                },
                risk_level='low'
            )

            log_gdpr_event(
                user=user,
                action='registration_consent',
                request=request
            )
            
            # verificam daca utilizatorul s-a autentificat prin Google
            if SocialAccount.objects.filter(user=user, provider='google').exists():
                user.is_active = True
                user.save()
                create_security_event(
                    user=user,
                    event_type='login_success',
                    description=f"Cont activat automat prin Google pentru {user.email}",
                    request=request,
                    risk_level='low'
                )
                return Response({'message': 'Utilizatorul s-a autentificat prin Google. Cont activat automat.'}, status=status.HTTP_201_CREATED)

            # pt utilizatorii care folosesc email și parola, trimitem un cod de verificare prin mail
            if email:
                verification_code = str(random.randint(100000, 999999))
                user.verification_code = verification_code
                user.save()

                create_security_event(
                    user=user,
                    event_type='email_verification',
                    description=f"Începe trimiterea codului de verificare email pentru înregistrare către {email}",
                    request=request,
                    additional_data={
                        'email_type': 'account_verification',
                        'recipient_email': email,
                        'verification_code_length': len(verification_code)
                    },
                    risk_level='low'
                )

                html_message = render_to_string('email_template.html', {
                    'verification_code': verification_code
                })

                email = EmailMessage(
                    config('EMAIL_SUBJECT_VERIFICATION'),
                    html_message,
                    config('EMAIL_FROM'),
                    [user.email],
                    reply_to=[config('EMAIL_FROM')],
                )
                email.content_subtype = 'html'
                email.send()

                create_security_event(
                    user=user,
                    event_type='email_verification',
                    description=f"Codul de verificare email pentru înregistrare trimis cu succes către {email}",
                    request=request,
                    additional_data={
                        'email_type': 'account_verification',
                        'recipient_email': email,
                        'status': 'success'
                    },
                    risk_level='low'
                )
                


                return Response({'message': 'Utilizatorul a fost înregistrat cu succes. Verificați emailul pentru codul de verificare.'}, status=status.HTTP_201_CREATED)

            # pt utilizatorii care se inregistreaza cu buletin
            elif cnp:
                user.is_verified_by_id = True
                user.save()
                return Response({'message': 'Utilizatorul a fost înregistrat cu succes cu buletinul.'}, status=status.HTTP_201_CREATED)
            
        create_security_event(
            user=None,
            event_type='profile_update',
            description=f"Încercare eșuată de înregistrare pentru {email or 'CNP: ' + str(cnp)[:3] + '***' if cnp else 'date necunoscute'}",
            request=request,
            additional_data={'errors': serializer.errors},
            risk_level='medium'
        )


        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SocialLoginCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        provider = request.data.get('provider')
        code = request.data.get('code')
        
        try:
            if not request.user.is_authenticated:
                return Response({'error': 'Autentificare eșuată'}, status=403)
            
            # Generare tokeni JWT
            refresh = RefreshToken.for_user(request.user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            # returneaza informatii user si token  uri
            user_data = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'message': 'Autentificare socială reușită!',
                'tokens': tokens
            }
            
            return Response(user_data, status=200)
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)

#view pentru autentificarea cu buletin
class LoginWithIDCardView(APIView):
    permission_classes = [AllowAny]
    
    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     self.model = YOLO(MODEL_PATH)
    
    def detect_spoofing(self, image_array):
        try:
            h, w = image_array.shape[:2]
            scale = min(1.0, 640 / max(h, w))
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                image_array = cv2.resize(image_array, (new_w, new_h))

            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            normalized = cv2.equalizeHist(gray)
            image_array = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)

            results = self.model(image_array, stream=True, verbose=False, conf=0.6)

            for r in results:
                for box in r.boxes:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())
                    
                    logger.info(f"Detectare spoofing - Scor: {conf}, Clasificare: {cls}")
                    
                    return cls == 1

            return False
        except Exception as e:
            logger.error(f"Eroare la detectarea spoofing-ului: {e}")
            return False

    def detect_and_encode_face(self, image_array):
        try:
            h, w = image_array.shape[:2]
            scale = min(1.0, 480 / max(h, w))
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                small_image = cv2.resize(image_array, (new_w, new_h))
            else:
                small_image = image_array.copy()
            
            face_locations = face_recognition.face_locations(small_image, model="hog")

            if len(face_locations) == 0:
                return None, "Nicio fata detectata in imagine. Verificati pozitia si iluminarea."

            if len(face_locations) > 1:
                return None, "S-au detectat mai multe fete. Procesul necesita o singura fata."

            if scale < 1.0:
                adjusted_locations = []
                for top, right, bottom, left in face_locations:
                    adjusted_locations.append(
                        (int(top / scale), int(right / scale), 
                         int(bottom / scale), int(left / scale))
                    )
                face_encodings = face_recognition.face_encodings(image_array, known_face_locations=adjusted_locations)
            else:
                face_encodings = face_recognition.face_encodings(image_array, known_face_locations=face_locations)

            if len(face_encodings) == 0:
                return None, "Codificarea fetei a esuat"

            return face_encodings[0], None
        except Exception as e:
            logger.error(f"Eroare la detectarea/codificarea fetei: {e}")
            return None, f"Eroare la detectarea fetei: {e}"

    def compare_faces(self, id_card_array, live_array):
        try:
            is_real = self.detect_spoofing(live_array)
            if not is_real:
                return False, "Frauda detectata: folositi o imagine reala!"
            
            id_card_encoding, id_card_error = self.detect_and_encode_face(id_card_array)
            if id_card_encoding is None:
                return False, id_card_error
                
            live_encoding, live_error = self.detect_and_encode_face(live_array)
            if live_encoding is None:
                return False, live_error

            face_distance = np.linalg.norm(id_card_encoding - live_encoding)
            match = face_distance < 0.6
            return match, "Identificare reușită!" if match else "Fetele nu se potrivesc."
        except Exception as e:
            logger.error(f"Eroare la compararea fetelor: {e}")
            return False, f"Eroare la compararea fețelor: {e}"

    def post(self, request):
        logger.info(f"Cerere POST primită în LoginWithIDCardView")
        
        cnp = request.data.get('cnp')
        live_image = request.FILES.get('live_image')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        id_series = request.data.get('id_series')
        
        is_facial_recognition = live_image is not None
        is_manual_id_auth = first_name is not None and last_name is not None and id_series is not None
        
        auth_type = 'Recunoaștere facială' if is_facial_recognition else 'Manual cu buletin' if is_manual_id_auth else 'Necunoscut'
        logger.info(f"Tip autentificare: {auth_type}")
        
        if not cnp:
            create_security_event(
                user=None,
                event_type='login_failed',
                description="Încercare de autentificare cu buletin fără CNP",
                request=request,
                risk_level='medium'
            )
            return Response(
                {"detail": "CNP-ul este necesar pentru autentificare."},
                status=400
            )
        
        try:
            user = User.objects.get(cnp=cnp)
            logger.info(f"Utilizator găsit cu CNP: {cnp}")
            create_security_event(
                user=user,
                event_type='login_success',
                description=f"Încercare autentificare cu buletin pentru CNP: {cnp[:3]}*** folosind {auth_type}",
                request=request,
                additional_data={
                    'auth_type': auth_type,
                    'facial_recognition': is_facial_recognition,
                    'manual_auth': is_manual_id_auth
                },
                risk_level='low'
            )
            
            if not user.is_verified_by_id:
                create_security_event(
                    user=user,
                    event_type='login_failed',
                    description=f"Încercare autentificare cu cont neverificat prin buletin: {cnp[:3]}***",
                    request=request,
                    risk_level='medium'
                )
                return Response({"detail": "Contul nu este verificat prin buletin."}, status=403)
                
            if not user.is_active:
                logger.info(f"Utilizatorul cu CNP: {cnp} este inactiv. Îl activăm.")
                user.is_active = True
                user.save()
                
        except User.DoesNotExist:
            create_security_event(
                user=None,
                event_type='login_failed',
                description=f"Încercare de autentificare cu CNP inexistent: {cnp[:3]}***",
                request=request,
                risk_level='high'
            )
            return Response({"detail": "Utilizator inexistent."}, status=401)
        
        has_2fa = False
        requires_2fa = False
        try:
            account_settings = user.account_settings
            has_2fa = account_settings.two_factor_enabled and account_settings.two_factor_verified
            requires_2fa = has_2fa
        except Exception as e:
            logger.error(f"Eroare la verificarea setărilor 2FA: {str(e)}")

        if is_facial_recognition:
            if not live_image:
                create_security_event(
                    user=user,
                    event_type='facial_recognition_failed',
                    description=f"Autentificare facială fără imagine live pentru {cnp[:3]}***",
                    request=request,
                    risk_level='medium'
                )
                return Response(
                    {"detail": "Imaginea live este necesară pentru autentificarea cu recunoaștere facială."},
                    status=400
                )
                
            live_pil = Image.open(io.BytesIO(live_image.read())).convert("RGB")
            
            max_size = 1024
            if max(live_pil.size) > max_size:
                live_pil.thumbnail((max_size, max_size), Image.LANCZOS)
                
            if user.id_card_image:
                id_card_path = user.id_card_image.path if default_storage.exists(user.id_card_image.name) else None
                
                if not id_card_path:
                    create_security_event(
                        user=user,
                        event_type='facial_recognition_failed',
                        description=f"Imagine de referință lipsă pentru {cnp[:3]}***",
                        request=request,
                        risk_level='high'
                    )
                    return Response({"detail": "Nu există imaginea de referință în baza de date."}, status=404)
                    
                id_card_pil = Image.open(id_card_path).convert("RGB")
                
                if max(id_card_pil.size) > max_size:
                    id_card_pil.thumbnail((max_size, max_size), Image.LANCZOS)
                
                id_card_array = np.array(id_card_pil)
                live_array = np.array(live_pil)
                
                match, message = face_recognition_service.compare_faces(id_card_array, live_array)
                
                if not match:
                    if 'spoofing' in message.lower() or 'fraud' in message.lower():
                        create_security_event(
                            user=user,
                            event_type='anti_spoofing_triggered',
                            description=f"Detectată încercare de spoofing pentru {cnp[:3]}***: {message}",
                            request=request,
                            risk_level='critical'
                        )
                    elif 'multiple' in message.lower():
                        create_security_event(
                            user=user,
                            event_type='multiple_faces_detected',
                            description=f"Multiple fețe detectate pentru {cnp[:3]}***: {message}",
                            request=request,
                            risk_level='critical'
                        )
                    else:
                        create_security_event(
                            user=user,
                            event_type='facial_recognition_failed',
                            description=f"Recunoaștere facială eșuată pentru {cnp[:3]}***: {message}",
                            request=request,
                            risk_level='high'
                        )
                        return Response({"detail": "Fraudă detectată: folosiți o imagine reală!"}, status=401)
                    return Response({"detail": message}, status=401)
                else:
                    create_security_event(
                        user=user,
                        event_type='facial_recognition_success',
                        description=f"Recunoaștere facială reușită pentru {cnp[:3]}***",
                        request=request,
                        risk_level='low'
                    )
                
            else:
                create_security_event(
                    user=user,
                    event_type='facial_recognition_failed',
                    description=f"Imaginea de referință lipsește pentru {cnp[:3]}***",
                    request=request,
                    risk_level='high'
                )
                return Response({"detail": "Imaginea de referință lipsește."}, status=404)
        
        elif is_manual_id_auth:
            if user.first_name.lower() != first_name.lower() or user.last_name.lower() != last_name.lower():
                create_security_event(
                    user=user,
                    event_type='login_failed',
                    description=f"Nume și prenume incorecte pentru {cnp[:3]}***",
                    request=request,
                    risk_level='high'
                )
                return Response({"detail": "Numele și prenumele nu corespund cu cele din baza de date."}, status=401)
            
            if hasattr(user, 'id_series') and user.id_series and user.id_series != id_series:
                create_security_event(
                    user=user,
                    event_type='login_failed',
                    description=f"Seria buletinului incorectă pentru {cnp[:3]}***",
                    request=request,
                    risk_level='high'
                )
                return Response({"detail": "Seria buletinului nu corespunde cu cea din baza de date."}, status=401)
            create_security_event(
                user=user,
                event_type='login_success',
                description=f"Autentificare manuală cu buletin reușită pentru {cnp[:3]}***",
                request=request,
                risk_level='low'
            )
        else:
            create_security_event(
                user=user,
                event_type='login_failed',
                description=f"Date insuficiente pentru autentificare cu buletin: {cnp[:3]}***",
                request=request,
                risk_level='medium'
            )
            return Response(
                {"detail": "Date insuficiente pentru autentificare."},
                status=400
            )
        
        if requires_2fa:
            logger.info(f"Autentificare de bază reușită pentru utilizatorul cu CNP {user.cnp}, dar necesită 2FA")
            return Response({
                'requires_2fa': True,
                'cnp': user.cnp,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_verified_by_id': user.is_verified_by_id,
                'is_active': user.is_active,
                'message': "Autentificare de bază reușită. Este necesară verificarea cu doi factori."
            }, status=200)
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        logger.info(f"Autentificare reușită pentru utilizatorul cu CNP {user.cnp}")
        create_security_event(
            user=user,
            event_type='login_success',
            description=f"Autentificare completă cu buletin reușită pentru {user.cnp[:3]}***",
            request=request,
            additional_data={
                'auth_method': 'id_card',
                'auth_type': auth_type
            },
        ) 
       
        response_data = {
            'refresh': str(refresh),
            'access': access_token,
            'cnp': user.cnp,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_verified_by_id': user.is_verified_by_id,
            'is_active': user.is_active,
            'message': "Autentificare reușită!"
        }
        
        if hasattr(user, 'email') and user.email:
            response_data['email'] = user.email
        
        logger.info(f"Răspuns autentificare trimis cu succes pentru CNP: {user.cnp}")
        
        return Response(response_data, status=200)

#Endpoint pentru verificarea reCAPTCHA
class VerifyRecaptchaView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        context = request.data.get('context', 'general')  # Adaugă context
        
        if not token:
            create_security_event(
                user=request.user if request.user.is_authenticated else None,
                event_type='captcha_failed',
                description="Verificare CAPTCHA eșuată - token lipsă",
                request=request,
                additional_data={'context': context, 'reason': 'missing_token'},
                risk_level='medium'
            )
            return Response({'success': False, 'detail': 'Token CAPTCHA lipsă'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_valid = verify_recaptcha(token)

        # Log evenimente CAPTCHA
        log_captcha_attempt(
            request=request,
            is_success=is_valid,
            captcha_type='recaptcha',
            context=context,
            user=request.user if request.user.is_authenticated else None
        )
        
        if is_valid:
            create_security_event(
                user=request.user if request.user.is_authenticated else None,
                event_type='captcha_success',
                description="Verificare reCAPTCHA reușită",
                request=request,
                additional_data={'context': context},
                risk_level='low'
            )
        else:
            create_security_event(
                user=request.user if request.user.is_authenticated else None,
                event_type='captcha_failed',
                description="Verificare reCAPTCHA eșuată",
                request=request,
                additional_data={'context': context, 'reason': 'invalid_token'},
                risk_level='medium'
            )
            
            # Verifică pentru încercări multiple
            self.check_multiple_captcha_attempts(request)
        
        if is_valid:
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'detail': 'Verificarea reCAPTCHA a eșuat'}, status=status.HTTP_400_BAD_REQUEST)
    
    def check_multiple_captcha_attempts(self, request):
        """Verifică pentru încercări multiple CAPTCHA eșuate"""
        from datetime import timedelta
        from security.models import CaptchaAttempt
        
        ip_address = self.get_client_ip(request)
        recent_failures = CaptchaAttempt.objects.filter(
            ip_address=ip_address,
            is_success=False,
            timestamp__gte=timezone.now() - timedelta(minutes=10)
        ).count()
        
        if recent_failures >= 3:  # 3 eșecuri în 10 minute
            create_security_event(
                user=request.user if request.user.is_authenticated else None,
                event_type='captcha_multiple_attempts',
                description=f'Detectate {recent_failures} eșecuri CAPTCHA în ultimele 10 minute',
                request=request,
                additional_data={
                    'failure_count': recent_failures,
                    'ip_address': ip_address,
                    'time_window': '10 minutes'
                },
                risk_level='high'
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
# view pt autentif clasica cu mail si parola   
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        logger.info(f"Cerere de autentificare pentru email: {email}")

        # Caută utilizatorul după email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            create_security_event(
                user=None,
                event_type='login_failed',
                description=f"Încercare de autentificare cu email inexistent: {email}",
                request=request,
                risk_level='medium'
            )
            return Response(
                {"detail": "Autentificare eșuată. Verifică email-ul și parola."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verifică dacă utilizatorul are un cont social asociat
        if SocialAccount.objects.filter(user=user).exists():
            create_security_event(
                user=user,
                event_type='login_failed',
                description=f"Încercare de autentificare clasică pe cont social: {email}",
                request=request,
                risk_level='medium'
            )
            return Response(
                {"detail": "Folosește autentificarea socială pentru acest cont (Facebook/Google)."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Autentificare clasică
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Verifică direct din baza de date setarea pentru 2FA
            try:
                # Accesăm direct din baza de date pentru a evita probleme de relație
                settings = AccountSettings.objects.get(user=user)
                has_2fa = settings.two_factor_enabled and settings.two_factor_verified
                
                logger.info(f"Setări 2FA pentru {user.email}: enabled={settings.two_factor_enabled}, verified={settings.two_factor_verified}")
                
            except AccountSettings.DoesNotExist:
                logger.warning(f"Nu există setări de cont pentru utilizatorul {user.email}")
                has_2fa = False
                
                # Creați setări pentru acest utilizator pentru viitoare autentificări
                AccountSettings.objects.create(user=user)
                
            except Exception as e:
                logger.error(f"Eroare la verificarea setărilor 2FA: {str(e)}")
                has_2fa = False
            
            if has_2fa:
                create_security_event(
                    user=user,
                    event_type='login_success',
                    description=f"Autentificare parțială reușită pentru {user.email} - necesită 2FA",
                    request=request,
                    risk_level='low'
                )

                # Returnăm un răspuns care indică necesitatea 2FA
                logger.info(f"Se solicită 2FA pentru utilizatorul {user.email}")
            
                return Response({
                    'requires_2fa': True,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_verified_by_id': getattr(user, 'is_verified_by_id', False),
                    'is_active': user.is_active,
                    'message': 'Este necesară verificarea cu doi factori.'
                }, status=status.HTTP_200_OK)
            else:

                create_security_event(
                    user=user,
                    event_type='login_success',
                    description=f"Autentificare completă reușită pentru {user.email}",
                    request=request,
                    risk_level='low'
                )

                # Generează token-uri JWT
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_verified_by_id': getattr(user, 'is_verified_by_id', False)
                }, status=status.HTTP_200_OK)

        # Parola este greșită
        create_security_event(
            user=None,
            event_type='login_failed',
            description=f"Autentificare eșuată - parolă incorectă pentru {email}",
            request=request,
            risk_level='medium'
        )
        return Response(
            {"detail": "Autentificare eșuată. Verifică email-ul și parola."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email-ul este obligatoriu'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            
            # Verificăm dacă utilizatorul are cont social
            if SocialAccount.objects.filter(user=user).exists():
                return Response({'error': 'Contul este asociat cu autentificare socială. Nu se poate reseta parola.'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # log inceput proces de resetare parola
            create_security_event(
                user=user,
                event_type='password_reset_request',
                description=f"Solicitare resetare parolă pentru {user.email}",
                request=request,
                additional_data={
                    'email': email,
                    'reset_method': 'email_code'
                },
                risk_level='low'
            )
            
            # Generăm un cod de resetare
            reset_code = str(random.randint(100000, 999999))
            user.verification_code = reset_code  # Folosim același câmp ca pentru verificarea emailului
            user.save()

            # log inceput dee trimitere mail
            create_security_event(
                user=user,
                event_type='email_verification',
                description=f"Începe trimiterea codului de resetare parolă prin email către {email}",
                request=request,
                additional_data={
                    'email_type': 'password_reset',
                    'recipient_email': email,
                    'reset_code_length': len(reset_code)
                },
                risk_level='low'
            )
            
            # Trimitem codul prin email
            html_message = render_to_string('password_reset_email.html', {
                'verification_code': reset_code
            })
            
            email = EmailMessage(
                'Cod de resetare parolă SmartVote',
                html_message,
                config('EMAIL_FROM'),
                [user.email],
                reply_to=[config('EMAIL_FROM')],
            )
            email.content_subtype = 'html'
            email.send()
            
            create_security_event(
                user=user,
                event_type='email_verification',
                description=f"Codul de resetare parolă trimis cu succes prin email către {email}",
                request=request,
                additional_data={
                    'email_type': 'password_reset',
                    'recipient_email': email,
                    'status': 'success'
                },
                risk_level='low'
            )
            return Response({'message': 'Un cod de resetare a fost trimis pe adresa de email.'}, 
                          status=status.HTTP_200_OK)
        except Exception as email_error:
                        create_security_event(
                user=user,
                event_type='email_verification',
                description=f"Eșec trimitere cod resetare parolă prin email către {email}: {str(email_error)}",
                request=request,
                additional_data={
                    'email_type': 'password_reset',
                    'recipient_email': email,
                    'status': 'failed',
                    'error': str(email_error)
                },
                risk_level='medium'
            )
                        return Response({'error': 'Eroare la trimiterea email-ului. Încercați din nou.'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        except User.DoesNotExist:
            create_security_event(
                user=None,
                event_type='password_reset_request',
                description=f"Încercare resetare parolă pentru email inexistent: {email}",
                request=request,
                additional_data={
                    'email': email,
                    'reason': 'user_not_found'
                },
                risk_level='medium'
            )
            # Pentru securitate, nu dezvăluim că email-ul nu există
            return Response({'message': 'Dacă email-ul există în sistem, un cod de resetare a fost trimis.'}, 
                          status=status.HTTP_200_OK)


class VerifyResetCodeView(APIView):
    """
    View pentru verificarea codului de resetare a parolei.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        verification_code = request.data.get('verification_code')
        
        if not all([email, verification_code]):
            return Response({'error': 'Email-ul și codul de verificare sunt obligatorii'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email, verification_code=verification_code)
            return Response({'message': 'Cod de verificare corect.'}, 
                          status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'Cod de verificare incorect sau email invalid.'}, 
                          status=status.HTTP_400_BAD_REQUEST)



class ResetPasswordView(APIView):
    """
    View pentru resetarea efectivă a parolei după verificarea codului.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        verification_code = request.data.get('verification_code')
        new_password = request.data.get('new_password')
        
        if not all([email, verification_code, new_password]):
            return Response({'error': 'Toate câmpurile sunt obligatorii'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email, verification_code=verification_code)
            
            # Validăm complexitatea parolei cu aceleași reguli ca la înregistrare
            password_errors = []
            
            # Verificare lungime minimă
            if len(new_password) < 6:
                password_errors.append('Parola trebuie să aibă cel puțin 6 caractere.')
            
            # Verificare pentru cel puțin o literă mare
            if not re.search(r'[A-Z]', new_password):
                password_errors.append('Parola trebuie să conțină cel puțin o literă mare.')
            
            # Verificare pentru cel puțin un caracter special
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
                password_errors.append('Parola trebuie să conțină cel puțin un caracter special.')
            
            # Verificare pentru cel puțin o cifră
            if not re.search(r'\d', new_password):
                password_errors.append('Parola trebuie să conțină cel puțin o cifră.')
            
            # Verificare dacă parola conține informații personale
            first_name = user.first_name.lower() if user.first_name else ""
            last_name = user.last_name.lower() if user.last_name else ""
            
            if first_name and len(first_name) > 2 and first_name in new_password.lower():
                password_errors.append('Parola nu trebuie să conțină prenumele tău.')
                
            if last_name and len(last_name) > 2 and last_name in new_password.lower():
                password_errors.append('Parola nu trebuie să conțină numele tău.')
                
            # Verificăm dacă parola nouă este similară cu parola veche
            if user.check_password(new_password):
                password_errors.append('Noua parolă nu poate fi identică cu parola veche.')
            
            # Verificări extinse pentru similitudine cu adresa de email
            if email:
                email_lower = email.lower()
                password_lower = new_password.lower()
                
                # Împărțim email-ul în părți pentru verificări separate
                email_parts = re.split(r'[.@_-]', email_lower)
                
                # Verificăm fiecare parte a emailului care are cel puțin 3 caractere
                for part in email_parts:
                    if len(part) >= 3 and part in password_lower:
                        password_errors.append(f'Parola nu trebuie să conțină părți din adresa de email ({part}).')
                        break
                
                # Verificăm numele de utilizator întreg (înainte de @)
                username = email_lower.split('@')[0]
                if len(username) >= 3 and username in password_lower:
                    password_errors.append('Parola nu trebuie să conțină numele de utilizator din email.')
                
                # Verificăm pentru subșiruri mai lungi de 3 caractere din email
                for i in range(len(email_lower) - 3):
                    substr = email_lower[i:i+4]  # Verificăm subșiruri de 4 caractere
                    if len(substr) >= 4 and substr in password_lower:
                        password_errors.append(f'Parola nu trebuie să conțină secvențe din adresa de email ({substr}).')
                        break
            
            # Verificăm împotriva parolelor comune
            common_passwords = ["password", "123456", "qwerty", "admin", "welcome", "parola"]
            if new_password.lower() in common_passwords:
                password_errors.append('Această parolă este prea comună și ușor de ghicit.')
            
            # Verificăm secvențe alfanumerice (ex: abc123, 123456)
            if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)', new_password.lower()):
                password_errors.append('Parola conține secvențe predictibile de caractere.')
            
            # Verificăm pentru caractere repetate excesiv
            if re.search(r'(.)\1{2,}', new_password):
                password_errors.append('Parola nu trebuie să conțină caractere repetate excesiv.')
            
            # Dacă avem erori, le returnăm
            if password_errors:
                return Response({'error': password_errors}, status=status.HTTP_400_BAD_REQUEST)
            
            # Dacă nu avem erori, actualizăm parola
            user.set_password(new_password)
            user.verification_code = None  # Resetăm codul după utilizare
            user.save()
            create_security_event(
                user=user,
                event_type='password_reset_success',
                description=f"Parolă resetată cu succes pentru {user.email}",
                request=request,
                risk_level='low'
            )
            
            return Response({'message': 'Parola a fost resetată cu succes.'}, 
                          status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'Cod de verificare incorect sau email invalid.'}, 
                          status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        verification_code = request.data.get('verification_code')
        email = request.data.get('email')
        
        print(f"Verificare email: {email}, cod: {verification_code}")  # Log pentru debug
        
        if not all([email, verification_code]):
            print("Câmpuri lipsă")  # Log pentru debug
            return Response({'error': 'Email-ul și codul de verificare sunt obligatorii'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email, verification_code=verification_code)
            print(f"Utilizator găsit: {user.email}, cod: {user.verification_code}")  # Log pentru debug
            
            # Activează contul și resetează codul de verificare
            user.is_active = True
            user.verification_code = None
            user.save()
            create_security_event(
                user=user,
                event_type='email_verification',
                description=f"Email verificat cu succes pentru {user.email}",
                request=request,
                risk_level='low'
            )
            return Response({'message': 'Contul a fost verificat cu succes și activat!'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            create_security_event(
                user=None,
                event_type='email_verification',
                description=f"Verificare email eșuată pentru {email} - cod invalid: {verification_code}",
                request=request,
                risk_level='medium'
            )
            print(f"Utilizator negăsit pentru {email} cu codul {verification_code}")  # Log pentru debug
            return Response({'error': 'Cod de verificare incorect sau email invalid.'}, status=status.HTTP_400_BAD_REQUEST)

class AutofillDataView(APIView):
    """
    Endpoint pentru procesarea imaginii încărcate și extragerea informațiilor.
    """
    permission_classes = [AllowAny]  

    def post(self, request):
        cropped_file_path = request.data.get('cropped_file_path')
        if not cropped_file_path:
            return Response({'error': 'Calea fișierului este necesară.'}, status=status.HTTP_400_BAD_REQUEST)

        # Construim calea completă către fișier
        absolute_path = os.path.join(settings.MEDIA_ROOT, cropped_file_path)
        if not os.path.exists(absolute_path):
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Procesăm imaginea
        processor = IDCardProcessor()
        extracted_info = processor.process_id_card(absolute_path)

        return Response({
            'message': 'Datele au fost extrase cu succes.',
            'extracted_info': extracted_info
        }, status=status.HTTP_200_OK)




#view pt inregistrarea utilizatorilor prin date din buletin
@csrf_exempt
def register_with_id_card(request):
    if request.method == 'POST':
        form = IDCardForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified_by_id = True
            user.save()
            return JsonResponse({'message': 'Te-ai înregistrat cu succes cu buletinul'}, status=200)
    else:
        form = IDCardForm()
    return render(request, 'users/register_with_id.html', {'form': form})


@api_view(['POST'])
@permission_classes([AllowAny])
def send_feedback(request):
    feedback_email = request.data.get('email')
    if not feedback_email or not User.objects.filter(email=feedback_email, is_active=True).exists():
        return Response(
            {'error': 'Se poate trimite feedback numai dacă sunteți conectat la aplicație.'},
            status=status.HTTP_403_FORBIDDEN
        )

    feedback_data = {
        'name': request.data.get('name'),
        'phone': request.data.get('phone'),
        'email': feedback_email,
        'message': request.data.get('message')
    }

    feedback_template = render_to_string('feedback_email.html', feedback_data)

    email = EmailMessage(
        subject='Feedback de la utilizator',
        body=feedback_template,
        from_email=config('DEFAULT_FROM_EMAIL'),
        to=[config('ADMIN_EMAIL')],
        reply_to=[feedback_email],
    )
    email.content_subtype = 'html'
    email.send()

    return Response({'message': 'Feedback-ul a fost trimis cu succes!'}, status=status.HTTP_200_OK)

class VerifyTwoFactorLoginView(APIView):
    """API view pentru verificarea codului 2FA în timpul autentificării"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        cnp = request.data.get('cnp')
        code = request.data.get('code')
        
        logger.info(f"Verificare 2FA: Email: {email}, CNP: {cnp}, Cod: {code}")
        
        if not code:
            return Response(
                {'error': 'Codul de verificare este obligatoriu.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Identifică utilizatorul după email sau CNP
        if email:
            user = User.objects.filter(email=email).first()
            logger.info(f"Căutare utilizator după email: {email}, găsit: {user is not None}")
        elif cnp:
            user = User.objects.filter(cnp=cnp).first()
            logger.info(f"Căutare utilizator după CNP: {cnp}, găsit: {user is not None}")
        else:
            logger.warning("Lipsă email și CNP în cererea de verificare 2FA")
            return Response(
                {'error': 'Email sau CNP este necesar pentru verificare.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not user:
            logger.warning("Utilizator negăsit pentru verificare 2FA")
            create_security_event(
                user=None,
                vent_type='2fa_failed',
                description=f"Încercare 2FA cu utilizator inexistent: {email or cnp[:3] + '***'}",
                request=request,
                risk_level='high'
            )
            return Response(
                {'error': 'Utilizator negăsit în baza de date.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verifică dacă utilizatorul are 2FA activat - accesăm direct din baza de date
        try:
            # Obține direct din baza de date pentru a evita probleme de relație
            account_settings = AccountSettings.objects.get(user=user)
            
            logger.info(f"Verificare setări 2FA pentru {user.email or user.cnp}: activat={account_settings.two_factor_enabled}, verificat={account_settings.two_factor_verified}")
            
            if not account_settings.two_factor_enabled:
                logger.warning(f"2FA nu este activat pentru {user.email or user.cnp}")
                create_security_event(
                    user=user,
                    event_type='2fa_failed',
                    description=f"Încercare 2FA pe cont fără 2FA activat: {user.email or user.cnp[:3] + '***'}",
                    request=request,
                    risk_level='medium'
                )
                return Response(
                    {'error': 'Autentificarea cu doi factori nu este activată pentru acest cont.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if not account_settings.two_factor_secret:
                logger.warning(f"Lipsă secret 2FA pentru {user.email or user.cnp}")
                create_security_event(
                    user=user,
                    event_type='2fa_failed',
                    description=f"Secret 2FA lipsă pentru: {user.email or user.cnp[:3] + '***'}",
                    request=request,
                    risk_level='high'
                )
                return Response(
                    {'error': 'Secret-ul pentru autentificarea cu doi factori lipsește. Vă rugăm reconfigurați autentificarea cu doi factori.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verifică codul TOTP
            totp = pyotp.TOTP(account_settings.two_factor_secret)
            is_valid = totp.verify(code, valid_window=1)  # Toleranță ±30 secunde
            logger.info(f"Verificare cod 2FA pentru {user.email or user.cnp}: {is_valid}")
            
            if is_valid:
                log_2fa_event(
                    user=user,
                    event_type='2fa',
                    is_success=True,
                    request=request,
                    additional_data={
                        'code_verified': True,
                        'auth_method': 'email' if user.email else 'id_card'
                    }
                )
                # Generează token JWT și returnează răspunsul
                refresh = RefreshToken.for_user(user)
                
                response_data = {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
                
                # Adaugă datele utilizatorului în răspuns
                if hasattr(user, 'email') and user.email:
                    response_data['email'] = user.email
                if hasattr(user, 'cnp') and user.cnp:
                    response_data['cnp'] = user.cnp
                    
                response_data['first_name'] = user.first_name
                response_data['last_name'] = user.last_name
                response_data['is_verified_by_id'] = getattr(user, 'is_verified_by_id', False)
                response_data['is_active'] = user.is_active
                
                logger.info(f"Verificare 2FA reușită pentru {user.email or user.cnp}")
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                # Pentru debugging, generăm un cod valid și vedem care ar fi fost codul corect
                current_code = totp.now()
                logger.warning(f"Cod 2FA invalid pentru {user.email or user.cnp}. Cod furnizat: {code}, cod curent valid: {current_code}")
                
                log_2fa_event(
                    user=user,
                    event_type='2fa',
                    is_success=False,
                    request=request,
                    additional_data={
                        'code_provided': code,
                        'expected_code': current_code,
                        'auth_method': 'email' if user.email else 'id_card'
                    }
                )
                return Response(
                    {'error': 'Cod de verificare invalid. Vă rugăm să introduceți codul corect din aplicația de autentificare.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except AccountSettings.DoesNotExist:
            logger.error(f"Nu există setări pentru utilizatorul {user.email or user.cnp}")
            
            create_security_event(
                user=user,
                event_type='2fa_failed',
                description=f"Setări 2FA lipsă pentru: {user.email or user.cnp[:3] + '***'}",
                request=request,
                risk_level='medium'
            )
            
            # Creăm automat setările lipsă pentru a evita această eroare în viitor
            try:
                AccountSettings.objects.create(user=user)
                logger.info(f"S-au creat setări de cont noi pentru utilizatorul {user.email or user.cnp}")
            except Exception as create_error:
                logger.error(f"Eroare la crearea setărilor pentru {user.email or user.cnp}: {str(create_error)}")
            
            return Response(
                {'error': 'Contul nu are setări de autentificare în doi factori configurate. Vă rugăm configurați autentificarea din Setări Cont.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Eroare la verificarea 2FA pentru {user.email or user.cnp if user else 'utilizator necunoscut'}: {str(e)}")
            logger.error(f"Detalii excepție: {str(e.__class__.__name__)}")
            
            try:
                # Încercăm să capturăm stack trace-ul pentru debugging
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
            except:
                pass
                
            return Response(
                {'error': 'A apărut o eroare la verificarea codului. Vă rugăm încercați din nou sau contactați administratorul.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        create_security_event(
            user=user,
            event_type='logout',
            description=f"Utilizatorul {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'} s-a deconectat",
            request=request,
            additional_data={
                'logout_method': 'manual_button',
                'auth_method': 'email' if user.email else 'id_card'
            },
            risk_level='low'
        )
        
        return Response({'message': 'Deconectare reușită'}, status=status.HTTP_200_OK)