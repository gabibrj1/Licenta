from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import AccessibilitySettings
from .serializers import AccessibilitySettingsSerializer
from security.utils import create_security_event
import logging

logger = logging.getLogger(__name__)

class AccessibilitySettingsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obține setările de accesibilitate ale utilizatorului"""
        try:
            settings = AccessibilitySettings.objects.get(user=request.user)
            serializer = AccessibilitySettingsSerializer(settings)
            
            create_security_event(
                user=request.user,
                event_type='profile_access',
                description=f"Acces la setările de accesibilitate pentru {request.user.email}",
                request=request,
                risk_level='low'
            )
            
            return Response(serializer.data)
        except AccessibilitySettings.DoesNotExist:
            # Creează setări implicite dacă nu există
            settings = AccessibilitySettings.objects.create(user=request.user)
            serializer = AccessibilitySettingsSerializer(settings)
            return Response(serializer.data)
    
    def post(self, request):
        """Actualizează setările de accesibilitate"""
        try:
            settings, created = AccessibilitySettings.objects.get_or_create(user=request.user)
            serializer = AccessibilitySettingsSerializer(settings, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                create_security_event(
                    user=request.user,
                    event_type='profile_update',
                    description=f"Actualizare setări accesibilitate pentru {request.user.email}",
                    request=request,
                    additional_data=request.data,
                    risk_level='low'
                )
                
                return Response({
                    'message': 'Setările de accesibilitate au fost actualizate cu succes!',
                    'settings': serializer.data
                })
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Eroare la actualizarea setărilor de accesibilitate: {str(e)}")
            return Response(
                {'error': f'Eroare la salvarea setărilor: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AccessibilityTestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează opțiuni pentru testarea accesibilității"""
        return Response({
            'font_size_options': AccessibilitySettings.FONT_SIZES,
            'contrast_options': AccessibilitySettings.CONTRAST_MODES,
            'animation_options': AccessibilitySettings.ANIMATION_SETTINGS,
            'features': {
                'screen_reader_compatible': True,
                'keyboard_navigation': True,
                'voice_commands': False,  # Pentru viitor
                'braille_support': False,  # Pentru viitor
            }
        })

class AccessibilityInfoView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează informații despre funcțiile de accesibilitate ale aplicației"""
        return Response({
            'accessibility_features': [
                {
                    'title': 'Suport pentru Cititori de Ecran',
                    'description': 'Aplicația este compatibilă cu JAWS, NVDA și VoiceOver pentru utilizatorii cu deficiențe de vedere.',
                    'available': True
                },
                {
                    'title': 'Navigare cu Tastatura',
                    'description': 'Toate funcțiile pot fi accesate folosind doar tastatura, fără mouse.',
                    'available': True
                },
                {
                    'title': 'Contrast Ridicat',
                    'description': 'Teme cu contrast ridicat pentru utilizatorii cu probleme de vedere.',
                    'available': True
                },
                {
                    'title': 'Mărirea Textului',
                    'description': 'Opțiuni pentru mărirea fontului până la 22px pentru o citire mai ușoară.',
                    'available': True
                },
                {
                    'title': 'Timp Extins pentru Vot',
                    'description': 'Timp suplimentar pentru completarea procesului de vot.',
                    'available': True
                },
                {
                    'title': 'Interfață Simplificată',
                    'description': 'Versiune simplificată a interfeței pentru utilizatori cu dizabilități cognitive.',
                    'available': True
                },
                {
                    'title': 'Asistență Audio',
                    'description': 'Ghidare vocală prin procesul de vot.',
                    'available': True
                },
                {
                    'title': 'Verificare Facială Asistată',
                    'description': 'Asistență suplimentară pentru utilizatorii cu dificultăți în recunoașterea facială.',
                    'available': True
                }
            ],
            'contact_info': {
                'email': 'accesibilitate@votapp.ro',
                'phone': '+40 723 452 871',
                'hours': 'Luni-Vineri: 9:00 - 17:00'
            }
        })