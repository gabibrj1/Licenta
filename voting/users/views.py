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
from .utils import extract_text_from_image, is_valid_id_card, parse_id_card
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
    permission_classes = [AllowAny]

    def post(self, request):
        image = request.FILES.get('id_card_image')
        if not image:
            return Response({'error': 'Niciun fișier nu a fost încărcat'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not is_valid_id_card(image):
            return Response({'error': 'Buletin invalid'}, status=status.HTTP_400_BAD_REQUEST)
        
        extracted_data = extract_text_from_image(image)
        print("Date extrase:", extracted_data)
        return Response({'data': extracted_data}, status=status.HTTP_200_OK)

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
    permission_classes = [AllowAny]

    def post(self, request):
        image = request.FILES.get('id_card_image')
        if not image:
            return Response({'error': 'Niciun fișier nu a fost încărcat'}, status=status.HTTP_400_BAD_REQUEST)

        # verfifica validitatea buletinului
        if not is_valid_id_card(image):
            return Response({'error': 'Buletin invalid'}, status=status.HTTP_400_BAD_REQUEST)

        extracted_text = extract_text_from_image(image)
        extracted_data = parse_id_card(extracted_text)
        
        if extracted_data:
            return Response({'data': extracted_data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Nu s-au putut extrage datele din imagine'}, status=status.HTTP_400_BAD_REQUEST)

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

#view pentru incarcarea unei imagini a unei carti de identitate si extragerea informatiilor
@csrf_exempt
def upload_id_card(request):
    if request.method == 'POST':
        image = request.FILES.get('id_card_image')
        if is_valid_id_card(image):
            extracted_data = extract_text_from_image(image)
            return JsonResponse({'data': extracted_data}, status=200)
        else:
            return JsonResponse({'error': 'Buletin invalid'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

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