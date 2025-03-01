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


logger = logging.getLogger(__name__)

class RegisterWithIDCardView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = IDCardRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # Verificam daca utilizatorul exista deja
            cnp = serializer.validated_data.get("cnp")
            email = serializer.validated_data.get("email")

            existing_user = None
            if cnp:
                existing_user = User.objects.filter(cnp=cnp).first()
            elif email:
                existing_user = User.objects.filter(email=email).first()

            if existing_user:
                return Response({'error': 'Utilizatorul există deja. Încearcă să te autentifici.'}, status=status.HTTP_400_BAD_REQUEST)

            # Cream un nou utilizator
            user = serializer.save(is_active=False, is_verified_by_id=True)  # 🔹 Initial, contul este inactiv

            # Salvam imaginea buletinului daca este incarcata
            image = request.FILES.get('id_card_image')
            if image:
                user.id_card_image.save(f'id_cards/{user.id}_{image.name}', image, save=True)

            return Response({'message': 'Înregistrare cu buletinul completată cu succes!'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# Calea catre modelul de anti - spoofing
MODEL_PATH = r"C:\Users\brj\Desktop\voting\media\models\l_version_1_300.pt"

class FaceRecognitionView(APIView):
    permission_classes = [AllowAny]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Incarca modelul YOLO pentru detectarea spoofing-ului
        self.model = YOLO(MODEL_PATH)

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

            match, message = self.compare_faces(id_card_array, live_array)

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
                new_base_name = f"{base_name}_rotated_{angle}"
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
        processor = IDCardProcessor()
        extracted_info = processor.process_id_card(absolute_path)

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

            # verificam daca utilizatorul s-a autentificat prin Google
            if SocialAccount.objects.filter(user=user, provider='google').exists():
                user.is_active = True
                user.save()
                return Response({'message': 'Utilizatorul s-a autentificat prin Google. Cont activat automat.'}, status=status.HTTP_201_CREATED)

            # pt utilizatorii care folosesc email și parola, trimitem un cod de verificare prin mail
            if email:
                verification_code = str(random.randint(100000, 999999))
                user.verification_code = verification_code
                user.save()

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

                return Response({'message': 'Utilizatorul a fost înregistrat cu succes. Verificați emailul pentru codul de verificare.'}, status=status.HTTP_201_CREATED)

            # pt utilizatorii care se inregistreaza cu buletin
            elif cnp:
                user.is_verified_by_id = True
                user.save()
                return Response({'message': 'Utilizatorul a fost înregistrat cu succes cu buletinul.'}, status=status.HTTP_201_CREATED)

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
@method_decorator(csrf_exempt, name='dispatch')
class LoginWithIDCardView(APIView):

    authentication_classes = [] # Permite autentificarea si fara token JWT
    permission_classes = [AllowAny]

    def post(self, request):
        cnp = request.data.get('cnp')
        series = request.data.get('series')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        if not cnp or not series or not first_name or not last_name:
            return Response(
                {"detail": "Toate câmpurile sunt necesare pentru autentificare cu buletinul."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(cnp=cnp, series=series, first_name=first_name, last_name=last_name)
        except User.DoesNotExist:
            return Response(
                {"detail": "Autentificare eșuată. Verifică datele introduse."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verifica daca utilizatorul este verificat prin buletin
        if user.is_verified_by_id and not user.is_active:
            user.is_active = True
            user.save()
        

        # Generăm tokeni JWT pentru sesiunea utilizatorului
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'cnp': user.cnp # Adaugam cnp in raspuns pentru a fi folosit in frontend
        }, status=status.HTTP_200_OK)



# view pt autentif clasica cu mail si parola   
class LoginView(APIView):
    permission_classes = [AllowAny]  # Permite accesul public pentru autentificare

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # cauta utilizatorul după email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Autentificare eșuată. Verifică email-ul și parola."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # verif daca utilizatorul are un cont social asociat
        if SocialAccount.objects.filter(user=user).exists():
            return Response(
                {"detail": "Folosește autentificarea socială pentru acest cont (Facebook/Google)."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Autentificare clasica
        user = authenticate(request, username=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        # Parola este gresita
        return Response(
            {"detail": "Autentificare eșuată. Verifică email-ul și parola."},
            status=status.HTTP_401_UNAUTHORIZED
        )

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        verification_code = request.data.get('verification_code')
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email, verification_code=verification_code)
            # activeaza contul si resteaza codul de verificare
            if user.verification_code == verification_code:
                user.is_active = True
                user.verification_code = None
                user.save()
                return Response({'message': 'Contul a fost verificat cu succes și activat!'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
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
