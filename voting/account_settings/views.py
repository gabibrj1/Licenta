from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging
import re
import base64
import pyotp
import qrcode
import io
from django.conf import settings
from .serializers import TwoFactorVerifySerializer
from security.utils import log_vote_security_event, log_captcha_attempt, create_security_event

from .models import ProfileImage, AccountSettings
from .serializers import (
    UserProfileSerializer, 
    ProfileImageSerializer, 
    AccountSettingsSerializer,
    CompleteUserProfileSerializer,
    ChangePasswordSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)

class UserProfileView(APIView):
    # API view pentru obținerea și actualizarea informațiilor profilului utilizatorului
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Obține profilul complet al utilizatorului cu setări și imagine
        user = request.user
        
        AccountSettings.objects.get_or_create(user=user)
        
        serializer = CompleteUserProfileSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        # Actualizează informațiile profilului utilizatorului
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Dacă utilizatorul încearcă să schimbe email-ul, trebuie validat
            if 'email' in request.data and request.data['email'] != user.email:
                # Verifică dacă email-ul există deja
                if User.objects.filter(email=request.data['email']).exists():
                    return Response(
                        {'email': 'Un utilizator cu acest email există deja.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            changed_fields = []

            for field, value in request.data.items():
                if hasattr(user, field) and getattr(user, field) != value:
                    changed_fields.append(field)

            serializer.save()
            create_security_event(
                user=user,
                event_type='profile_update',
                description=f"Profil actualizat pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
                request=request,
                additional_data={
                    'changed_fields': changed_fields,
                    'update_method': 'profile_settings'
                },
                risk_level='low'
            )

            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileImageView(APIView):
    # API view pentru gestionarea imaginilor de profil
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        # Încarcă o nouă imagine de profil
        user = request.user
        
        # Obține sau creează obiectul imaginii de profil
        profile_image, created = ProfileImage.objects.get_or_create(user=user)
        
        # Salvează noua imagine
        serializer = ProfileImageSerializer(
            profile_image,
            data=request.data,
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        # Șterge imaginea de profil
        user = request.user
        
        try:
            profile_image = ProfileImage.objects.get(user=user)
            # Șterge fișierul imaginii
            if profile_image.image:
                profile_image.image.delete(save=False)
            
            # Resetează câmpul imaginii
            profile_image.image = None
            profile_image.save()
            
            return Response({'message': 'Imaginea de profil a fost ștearsă cu succes.'}, 
                          status=status.HTTP_200_OK)
        except ProfileImage.DoesNotExist:
            return Response({'message': 'Nu există o imagine de profil.'},
                          status=status.HTTP_404_NOT_FOUND)

class AccountSettingsView(APIView):
    # API view pentru setările contului
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Obține sau creează setările contului pentru utilizator
        account_settings, created = AccountSettings.objects.get_or_create(user=request.user)
        serializer = AccountSettingsSerializer(account_settings)
        return Response(serializer.data)
    
    def put(self, request):
        # Obține sau creează setările contului pentru utilizator
        account_settings, created = AccountSettings.objects.get_or_create(user=request.user)
        serializer = AccountSettingsSerializer(account_settings, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    # API view pentru schimbarea parolei utilizatorului
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Verifică parola veche
            if not user.check_password(serializer.validated_data['old_password']):
                create_security_event(
                    user=user,
                    event_type='password_change',
                    description=f"Încercare schimbare parolă cu parolă curentă incorectă pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
                    request=request,
                    risk_level='medium'
                )
                return Response(
                    {'old_password': 'Parola actuală este incorectă.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validează complexitatea parolei
            try:
                self.validate_password_complexity(
                    serializer.validated_data['new_password'],
                    user
                )
            except ValidationError as e:
                return Response({'new_password': e.messages}, status=status.HTTP_400_BAD_REQUEST)
            
            # Setează noua parolă
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            create_security_event(
                user=user,
                event_type='password_change',
                description=f"Parolă schimbată cu succes pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
                request=request,
                additional_data={'change_method': 'user_settings'},
                risk_level='low'
            )

            return Response(
                {'message': 'Parola a fost schimbată cu succes.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def validate_password_complexity(self, password, user):
        # Validează cerințele de complexitate ale parolei
        errors = []
        
        # Validarea lungimii
        if len(password) < 8:
            errors.append('Parola trebuie să aibă cel puțin 8 caractere.')
        
        # Literă mare
        if not re.search(r'[A-Z]', password):
            errors.append('Parola trebuie să conțină cel puțin o literă mare.')
        
        # Caracter special
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Parola trebuie să conțină cel puțin un caracter special.')
        
        # Cifră
        if not re.search(r'\d', password):
            errors.append('Parola trebuie să conțină cel puțin o cifră.')
        
        # Verifică informațiile personale
        email = getattr(user, 'email', "")
        first_name = getattr(user, 'first_name', "").lower()
        last_name = getattr(user, 'last_name', "").lower()
        
        if first_name and len(first_name) > 2 and first_name in password.lower():
            errors.append('Parola nu trebuie să conțină prenumele tău.')
        
        if last_name and len(last_name) > 2 and last_name in password.lower():
            errors.append('Parola nu trebuie să conțină numele tău.')
        
        if email:
            email_lower = email.lower()
            password_lower = password.lower()
            
            # Verifică părțile din email
            email_parts = re.split(r'[.@_-]', email_lower)
            for part in email_parts:
                if len(part) >= 3 and part in password_lower:
                    errors.append(f'Parola nu trebuie să conțină părți din adresa de email.')
                    break
        
        if errors:
            raise ValidationError(errors)
            
        return True

class DeleteAccountView(APIView):
    # API view pentru dezactivarea unui cont de utilizator
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Dezactivează contul în loc să îl șteargă permanent
        user.is_active = False
        user.save()
        
        return Response(
            {'message': 'Contul a fost dezactivat cu succes.'},
            status=status.HTTP_200_OK
        )
    
class TwoFactorSetupView(APIView):
    # API view pentru configurarea autentificării în doi factori
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Generează TOTP și codul QR
        user = request.user
        account_settings, _ = AccountSettings.objects.get_or_create(user=user)
        
        # Generează un two_factor_secret nou dacă nu există sau nu a fost verificat
        if not account_settings.two_factor_secret or not account_settings.two_factor_verified:
            # Generează secretul pentru TOTP
            secret = pyotp.random_base32()
            account_settings.two_factor_secret = secret
            account_settings.two_factor_verified = False
            account_settings.save()
        else:
            secret = account_settings.two_factor_secret
        
        # Creează URL-ul pentru aplicația de autentificare
        totp = pyotp.TOTP(secret)
        app_name = "VotingApp"
        user_identifier = user.email or user.cnp
        provisioning_uri = totp.provisioning_uri(name=user_identifier, issuer_name=app_name)
        
        # Generează codul QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_code_base64}",
            'is_verified': account_settings.two_factor_verified
        })
    
    def post(self, request):
        # Verifică codul TOTP și activează 2FA
        user = request.user
        account_settings = AccountSettings.objects.get(user=user)
        
        # Verifică dacă există un secret
        if not account_settings.two_factor_secret:
            return Response(
                {'error': 'Nu există un secret configurat pentru autentificarea în doi factori.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obține codul din cerere
        code = request.data.get('code')
        if not code:
            return Response(
                {'error': 'Codul de verificare este obligatoriu.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Curăță codul
        code = str(code).strip()
        
        logger.debug(f"Verifying 2FA code: {code} with secret: {account_settings.two_factor_secret}")
        
        # Verifică codul TOTP cu toleranță extinsă
        totp = pyotp.TOTP(account_settings.two_factor_secret)
        
        if totp.verify(code, valid_window=1):  # Adăugă o fereastră de toleranță de 1 interval (+- 30 secunde)
            # Activează autentificarea în doi factori
            account_settings.two_factor_verified = True
            account_settings.two_factor_enabled = True
            account_settings.save()
            
            logger.info(f"2FA enabled successfully for user {user.id}")
            create_security_event(
                user=user,
                event_type='2fa_enabled',
                description=f"Autentificare 2FA activată pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
                request=request,
                risk_level='low'
            )

            
            return Response({
                'message': 'Autentificarea în doi factori a fost activată cu succes.',
                'is_verified': True
            })
        else:
            logger.warning(f"2FA verification failed for user {user.id}. Code entered: {code}")
            
            # Generăm un cod valid pentru debugging
            current_code = totp.now()
            logger.debug(f"Current valid code would be: {current_code}")
            
            return Response(
                {'error': 'Codul de verificare este invalid. Asigurați-vă că introduceți codul curent din aplicație.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request):
        # Dezactivează autentificarea în doi facctori
        user = request.user
        account_settings = AccountSettings.objects.get(user=user)
        
        account_settings.two_factor_enabled = False
        account_settings.two_factor_verified = False
        account_settings.two_factor_secret = None
        account_settings.save()
        
        logger.info(f"2FA disabled for user {user.id}")
        create_security_event(
            user=user,
            event_type='2fa_disabled',
            description=f"Autentificare 2FA dezactivată pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
            request=request,
            risk_level='low'
        )
        
        return Response({
            'message': 'Autentificarea în doi factori a fost dezactivată cu succes.'
        })
    
class BlockAccountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        reason = request.data.get('reason', 'Manual block')
        
        user.is_active = False
        user.save()
        
        create_security_event(
            user=user,
            event_type='account_locked',
            description=f"Cont blocat pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
            request=request,
            additional_data={'block_reason': reason},
            risk_level='high'
        )
        
        return Response({'message': 'Cont blocat cu succes'})

class UnblockAccountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        user.is_active = True
        user.save()
        
        create_security_event(
            user=user,
            event_type='account_unlocked',
            description=f"Cont deblocat pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
            request=request,
            risk_level='low'
        )
        
        return Response({'message': 'Cont deblocat cu succes'})