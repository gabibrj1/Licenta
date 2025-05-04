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
    """API view for retrieving and updating user profile information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get complete user profile with settings and image"""
        user = request.user
        
        # Ensure user has account settings
        AccountSettings.objects.get_or_create(user=user)
        
        serializer = CompleteUserProfileSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        """Update user profile information"""
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            # If user tries to change email, validate it
            if 'email' in request.data and request.data['email'] != user.email:
                # Check if email already exists
                if User.objects.filter(email=request.data['email']).exists():
                    return Response(
                        {'email': 'Un utilizator cu acest email există deja.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileImageView(APIView):
    """API view for managing profile images"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload a new profile image"""
        user = request.user
        
        # Get or create profile image object
        profile_image, created = ProfileImage.objects.get_or_create(user=user)
        
        # Save new image
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
        """Delete profile image"""
        user = request.user
        
        try:
            profile_image = ProfileImage.objects.get(user=user)
            # Delete the image file
            if profile_image.image:
                profile_image.image.delete(save=False)
            
            # Reset the image field
            profile_image.image = None
            profile_image.save()
            
            return Response({'message': 'Imaginea de profil a fost ștearsă cu succes.'}, 
                          status=status.HTTP_200_OK)
        except ProfileImage.DoesNotExist:
            return Response({'message': 'Nu există o imagine de profil.'},
                          status=status.HTTP_404_NOT_FOUND)

class AccountSettingsView(APIView):
    """API view for account settings"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get or create account settings for user
        account_settings, created = AccountSettings.objects.get_or_create(user=request.user)
        serializer = AccountSettingsSerializer(account_settings)
        return Response(serializer.data)
    
    def put(self, request):
        # Get or create account settings for user
        account_settings, created = AccountSettings.objects.get_or_create(user=request.user)
        serializer = AccountSettingsSerializer(account_settings, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    """API view for changing user password"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Parola actuală este incorectă.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate password complexity
            try:
                self.validate_password_complexity(
                    serializer.validated_data['new_password'],
                    user
                )
            except ValidationError as e:
                return Response({'new_password': e.messages}, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {'message': 'Parola a fost schimbată cu succes.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def validate_password_complexity(self, password, user):
        """Validate password complexity requirements"""
        errors = []
        
        # Length validation
        if len(password) < 8:
            errors.append('Parola trebuie să aibă cel puțin 8 caractere.')
        
        # Uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append('Parola trebuie să conțină cel puțin o literă mare.')
        
        # Special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Parola trebuie să conțină cel puțin un caracter special.')
        
        # Digit
        if not re.search(r'\d', password):
            errors.append('Parola trebuie să conțină cel puțin o cifră.')
        
        # Check for personal info
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
            
            # Check for email parts
            email_parts = re.split(r'[.@_-]', email_lower)
            for part in email_parts:
                if len(part) >= 3 and part in password_lower:
                    errors.append(f'Parola nu trebuie să conțină părți din adresa de email.')
                    break
        
        if errors:
            raise ValidationError(errors)
            
        return True

class DeleteAccountView(APIView):
    """API view for deactivating a user account"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Deactivate account rather than permanently deleting
        user.is_active = False
        user.save()
        
        return Response(
            {'message': 'Contul a fost dezactivat cu succes.'},
            status=status.HTTP_200_OK
        )
    
class TwoFactorSetupView(APIView):
    """API view pentru configurarea autentificării în doi pași"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generează secretul TOTP și codul QR"""
        user = request.user
        account_settings, _ = AccountSettings.objects.get_or_create(user=user)
        
        # Generează un secret nou dacă nu există sau nu a fost verificat
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
        """Verifică codul TOTP și activează 2FA"""
        user = request.user
        account_settings = AccountSettings.objects.get(user=user)
        
        # Verifică dacă există un secret
        if not account_settings.two_factor_secret:
            return Response(
                {'error': 'Nu există un secret configurat pentru autentificarea în doi pași.'},
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
        
        if totp.verify(code, valid_window=1):  # Adăugăm o fereastră de toleranță de 1 interval (±30 secunde)
            # Activează autentificarea în doi pași
            account_settings.two_factor_verified = True
            account_settings.two_factor_enabled = True
            account_settings.save()
            
            logger.info(f"2FA enabled successfully for user {user.id}")
            
            return Response({
                'message': 'Autentificarea în doi pași a fost activată cu succes.',
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
        """Dezactivează autentificarea în doi pași"""
        user = request.user
        account_settings = AccountSettings.objects.get(user=user)
        
        account_settings.two_factor_enabled = False
        account_settings.two_factor_verified = False
        account_settings.two_factor_secret = None
        account_settings.save()
        
        logger.info(f"2FA disabled for user {user.id}")
        
        return Response({
            'message': 'Autentificarea în doi pași a fost dezactivată cu succes.'
        })