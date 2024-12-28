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


# Model AI pentru detecția limbajului nepotrivit
toxic_classifier = pipeline("text-classification", model="unitary/toxic-bert")

def contains_profanity_with_ai(message):
    """
    Detectează limbaj nepotrivit în mesaj folosind AI.
    """
    sentences = re.split(r'[.!?]', message)  # Împărțim mesajul în propoziții
    for sentence in sentences:
        if sentence.strip():  # Ignorăm propozițiile goale
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

    # Alte validări și trimiterea mesajului
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


# Funcție pentru validarea numelui
def validate_name(name):
    return name.isalpha() and len(name) > 1

# Funcție pentru validarea telefonului
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

    # Validare: numele trebuie să fie valid
    if not validate_name(feedback_data['name']):
        return Response({'error': 'Nume invalid. Verificați introducerea.'}, status=400)

    # Validare: numărul de telefon trebuie să fie valid
    if not validate_phone(feedback_data['phone'], "RO"):
        return Response({'error': 'Număr de telefon invalid. Verificați prefixul și numărul.'}, status=400)

    # Validare: mesajul să nu conțină injurii
    if contains_profanity_with_ai(feedback_data['message']):
        return Response({'error': 'Mesajul conține limbaj nepotrivit și nu a fost trimis.'}, status=400)

    # Validare: mesajul trebuie să aibă cel puțin 20 de cuvinte
    if len(feedback_data['message'].split()) < 20:
        return Response({'error': 'Mesajul trebuie să conțină cel puțin 20 de cuvinte.'}, status=400)

    # Trimiterea feedback-ului dacă toate condițiile sunt satisfăcute
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
    """
    Endpoint pentru încărcarea imaginii.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # Permite acces public (opțional)

    def post(self, request):
        image = request.FILES.get('id_card_image')
        if not image:
            return Response({'error': 'Niciun fișier nu a fost încărcat'}, status=status.HTTP_400_BAD_REQUEST)

        # Salvează imaginea în media/uploads
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, image.name)

        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        return Response({
            'message': 'Imaginea a fost încărcată cu succes.',
            'file_path': file_path  # Trimite calea fișierului pentru procesare ulterioară
        }, status=status.HTTP_200_OK)
    
class ScanIdView(APIView):
    """
    Endpoint pentru scanarea imaginii de pe camera și extragerea informațiilor.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # Permite acces public (opțional)

    def post(self, request):
        image = request.FILES.get('camera_image')
        if not image:
            return Response({'error': 'Niciun fișier nu a fost încărcat'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Salvează imaginea în media/camera
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'camera')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, image.name)

        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)

        # Procesăm imaginea pentru extragerea datelor
        #processor = IDCardProcessor()
        #extracted_info = processor.process_id_card(file_path)

        return Response({
            
            'message': 'Imaginea a fost scanată cu succes.',
            'file_path': os.path.join('media/camera', image.name)
           # 'extracted_info': extracted_info
        }, status=status.HTTP_200_OK)
    
class AutofillScanDataView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        file_path = request.data.get('file_path')
        if not file_path:
            return Response({'error': 'Calea fișierului este necesară.'}, status=status.HTTP_400_BAD_REQUEST)

        # Construim calea completă către fișier
        if not file_path.startswith(settings.MEDIA_ROOT):
            file_path = os.path.join(settings.MEDIA_ROOT, file_path.replace('media/', ''))
        
        if not os.path.exists(file_path):
            return Response({'error': 'Fișierul nu a fost găsit.'}, status=status.HTTP_404_NOT_FOUND)

        # Procesăm imaginea
        processor = IDCardProcessor()
        extracted_info = processor.process_id_card(file_path)

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

#view pt autentif clasica cu mail si parola   
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
    permission_classes = [AllowAny]  # Permite acces public (opțional)

    def post(self, request):
        file_path = request.data.get('file_path')
        if not file_path:
            return Response({'error': 'Calea fișierului este necesară.'}, status=status.HTTP_400_BAD_REQUEST)

        # Construim calea completă către fișier
        absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
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
