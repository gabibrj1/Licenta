from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import VoteSettings
from django.utils import timezone
from django.core.exceptions import ValidationError

class VoteSettingsView(APIView):
    permission_classes = [AllowAny]
    
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