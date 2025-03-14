from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from decouple import config
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
import uuid
from datetime import datetime
from django.urls import reverse
from django.conf import settings
from .models import Appointment
from django.http import HttpResponseRedirect
from django.db import transaction
from django.utils import timezone



logger = logging.getLogger(__name__)

class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.info(f"🔹 Autentificare utilizator: ID={user.id} | Email={user.email} | CNP={getattr(user, 'cnp', None)}")

        if not user.is_active:
            return Response({"detail": "Utilizatorul nu este activ."}, status=403)

        # Daca utilizatorul s-a logat cu email si parola (nu are CNP)
        if not hasattr(user, 'cnp') or not user.cnp:
            return Response({
                'email': user.email
            }, status=200)

        # Daca utilizatorul s-a logat cu buletinul (are CNP si este verificat)
        if hasattr(user, 'cnp') and user.is_verified_by_id:
            return Response({
                'cnp': user.cnp,
                'first_name': user.first_name,
                'last_name': user.last_name
            }, status=200)

        # in orice alt caz, returnam 403
        return Response({"detail": "Acces interzis."}, status=403)
    

# view pentru contact
class ContactInfoView(APIView):
    permission_classes = [AllowAny]  
    
    def get(self, request):
        contact_info = {
            'address': 'Str. Scafe nr. 14, Prahova',
            'phone': '+40 723 452 871',
            'email': 'g.brujbeanu18@gmail.com',
            'business_hours': 'Luni-Vineri: 9:00 - 17:00'
        }
        
        return Response(contact_info)
    
# view pentru trimiterea formularului de contact pe mail
@api_view(['POST'])


@permission_classes([AllowAny])
def send_contact_message(request):
    name = request.data.get('name')
    email = request.data.get('email')
    message = request.data.get('message')
    
    # Verificăm dacă avem toate datele necesare
    if not name or not email or not message:
        return Response(
            {'error': 'Toate câmpurile sunt obligatorii: nume, email și mesaj.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificăm dacă userul este autentificat
    is_authenticated = "Nu"
    user_email = None
    
    if request.user.is_authenticated:
        is_authenticated = "Da (Email: {})".format(request.user.email)
        user_email = request.user.email
    
    # Pregătim datele pentru template
    contact_data = {
        'name': name,
        'email': email,
        'is_authenticated': is_authenticated,
        'message': message
    }
    
    # Generăm conținutul email-ului
    contact_template = render_to_string('contact_email.html', contact_data)
    
    # Creăm și trimitem email-ul
    email_obj = EmailMessage(
        subject='Mesaj nou din formularul de contact',
        body=contact_template,
        from_email=config('DEFAULT_FROM_EMAIL'),
        to=[config('ADMIN_EMAIL')],  # g.brujbeanu18@gmail.com
        reply_to=[email],
    )
    email_obj.content_subtype = 'html'
    
    try:
        email_obj.send()
        return Response({'message': 'Mesajul tău a fost trimis cu succes!'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'Eroare la trimiterea mesajului: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def schedule_appointment(request):
    """
    Programează un apel telefonic
    """
    data = request.data
    
    if not all(key in data for key in ['name', 'email', 'phone', 'dateTime']):
        return Response({
            'message': 'Toate câmpurile sunt obligatorii: nume, email, telefon și data.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Parsează datetime
        date_time_str = data['dateTime'].replace('Z', '+00:00')
        date_time = datetime.fromisoformat(date_time_str)
        
        # Extrage ora exactă din data primită din frontend
        # Aceasta este ora pe care utilizatorul a selectat-o în interfață
        frontend_hour = int(data.get('originalHour', date_time.hour))
        
        # Convertește la datetime aware pentru comparare
        from django.utils import timezone
        date_time = timezone.make_aware(date_time.replace(tzinfo=None)) if date_time.tzinfo is None else date_time
        
        # Asigură-te că folosim ora exactă pe care utilizatorul a selectat-o, indiferent de timezone
        date_time = date_time.replace(hour=frontend_hour)
        
        now = timezone.now()
        
        if date_time < now:
            return Response({
                'message': 'Data programării nu poate fi în trecut.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifică disponibilitatea în intervalul orar (cu o marjă de protecție)
        start_time = date_time.replace(minute=0, second=0, microsecond=0)
        end_time = date_time.replace(minute=59, second=59, microsecond=999999)
        
        # Verifică dacă există deja programări în acest interval
        existing_appointments = Appointment.objects.filter(
            date_time__range=(start_time, end_time)
        )
        
        if existing_appointments.exists():
            return Response({
                'message': 'Această oră a fost deja rezervată. Te rugăm să selectezi o altă oră.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generează token pentru confirmare
        confirmation_token = str(uuid.uuid4())
        
        # Verifică dacă utilizatorul este autentificat
        user = None
        if request.user.is_authenticated:
            user = request.user
        
        # Creează programarea în baza de date
        appointment = Appointment.objects.create(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            date_time=date_time,
            notes=data.get('notes', ''),
            confirmation_token=confirmation_token,
            user=user
        )
        
        # Formatează data pentru afișare cu ora exactă selectată de utilizator
        date_time_str = date_time.strftime('%d %B %Y') + f", {frontend_hour}:00"
        
        # Construiește URL-urile pentru confirmare/refuz
        backend_domain = config('BACKEND_URL', default='http://127.0.0.1:8000')
        confirmation_url = f"{backend_domain}/api/menu/appointments/confirm/{confirmation_token}/"
        reject_url = f"{backend_domain}/api/menu/appointments/reject/{confirmation_token}/"
        
        # Pregătește datele pentru email
        context = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'date_time_str': date_time_str,
            'notes': data.get('notes', ''),
            'confirmation_url': confirmation_url,
            'reject_url': reject_url
        }
        
        # Generează email-ul
        email_body = render_to_string('appointment_email.html', context)
        
        # Trimite email către admin
        admin_email = EmailMessage(
            subject=f'Nouă solicitare de programare de la {data["name"]}',
            body=email_body,
            from_email=config('DEFAULT_FROM_EMAIL'),
            to=[config('ADMIN_EMAIL')],
            reply_to=[data['email']]
        )
        admin_email.content_subtype = 'html'
        admin_email.send()
        
        return Response({
            'message': 'Programarea a fost trimisă cu succes! Vei primi un email când aceasta va fi confirmată.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Eroare la programare:", str(e))
        print(traceback.format_exc())
        return Response({
            'message': f'Eroare la programare: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        import traceback
        print("Eroare la programare:", str(e))
        print(traceback.format_exc())
        return Response({
            'message': f'Eroare la programare: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def confirm_appointment(request, token):
    """
    Confirmă programarea de către admin
    """
    try:
        appointment = Appointment.objects.get(confirmation_token=token, is_confirmed=False)
        appointment.is_confirmed = True
        appointment.save()
        
        # Formatează data pentru afișare
        date_time_str = appointment.date_time.strftime('%d %B %Y, %H:%M')
        
        # Trimite email de confirmare către client
        context = {
            'name': appointment.name,
            'date_time_str': date_time_str,
            'phone': appointment.phone
        }
        
        client_email_body = render_to_string('appointment_confirmation_email.html', context)
        
        client_email = EmailMessage(
            subject='Programarea ta a fost confirmată',
            body=client_email_body,
            from_email=config('DEFAULT_FROM_EMAIL'),
            to=[appointment.email]
        )
        client_email.content_subtype = 'html'
        client_email.send()
        
        # Redirecționare către pagina de succes din frontend
        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        redirect_url = f"{frontend_url}/appointment-confirmed"
        
        return HttpResponseRedirect(redirect_url)
        
    except Appointment.DoesNotExist:
        # Redirecționare către pagina de eroare din frontend
        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        redirect_url = f"{frontend_url}/appointment-error"
        
        return HttpResponseRedirect(redirect_url)
    except Exception as e:
        # Redirecționare către pagina de eroare din frontend
        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        redirect_url = f"{frontend_url}/appointment-error"
        
        return HttpResponseRedirect(redirect_url)


@api_view(['GET'])
@permission_classes([AllowAny])
def reject_appointment(request, token):
    """
    Respinge programarea
    """
    try:
        appointment = Appointment.objects.get(confirmation_token=token)
        email = appointment.email
        name = appointment.name
        
        # Pregătește datele pentru email
        context = {
            'name': name
        }
        
        # Generează email-ul de respingere
        client_email_body = render_to_string('appointment_rejection_email.html', context)
        
        # Ștergem programarea
        appointment.delete()
        
        # Trimite email către client
        client_email = EmailMessage(
            subject='Programarea ta nu poate fi onorată',
            body=client_email_body,
            from_email=config('DEFAULT_FROM_EMAIL'),
            to=[email]
        )
        client_email.content_subtype = 'html'
        client_email.send()
        
        # Redirecționare către pagina de succes din frontend
        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        redirect_url = f"{frontend_url}/appointment-rejected"
        
        return HttpResponseRedirect(redirect_url)
        
    except Appointment.DoesNotExist:
        # Redirecționare către pagina de eroare din frontend
        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        redirect_url = f"{frontend_url}/appointment-error"
        
        return HttpResponseRedirect(redirect_url)
    except Exception as e:
        # Redirecționare către pagina de eroare din frontend
        frontend_url = config('FRONTEND_URL', default='http://localhost:4200')
        redirect_url = f"{frontend_url}/appointment-error"
        
        return HttpResponseRedirect(redirect_url)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def check_availability(request, date):
    try:
        # Convertim string-ul de dată în obiect date
        from datetime import datetime
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Setăm intervalul orar de lucru (9:00 - 17:00)
        business_hours = [hour for hour in range(9, 18) if hour != 12]
        
        # Obținem toate programările confirmate pentru data selectată
        
        start_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
        
        # Include programări în așteptare (neconfirmate încă) pentru a evita suprareservarea
        booked_appointments = Appointment.objects.filter(
            date_time__range=(start_of_day, end_of_day)
        ).values_list('date_time', flat=True)
        
        # Extragem orele care sunt deja programate
        booked_hours = set()
        for appointment in booked_appointments:
            booked_hours.add(appointment.hour)
        
        # Calculăm orele disponibile
        available_hours = [hour for hour in business_hours if hour not in booked_hours]
        
        # Formatăm orele pentru răspuns
        formatted_hours = [f"{hour}:00" for hour in available_hours]
        
        return Response({
            'available_hours': formatted_hours
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'message': f'Eroare la verificarea disponibilității: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class MapInfoView(APIView):
    permission_classes = [AllowAny]  
    
    def get(self, request):
        map_info = {
            'center': {
                'lat': 45.9443,
                'lng': 25.0094
            },
            'zoom': 7,
            'regions': [
                {'name': 'Alba', 'code': 'AB', 'voters': 1250, 'percentage': 0.25},
                {'name': 'Arad', 'code': 'AR', 'voters': 980, 'percentage': 0.18},
                {'name': 'Argeș', 'code': 'AG', 'voters': 1430, 'percentage': 0.30},
                {'name': 'Bacău', 'code': 'BC', 'voters': 1650, 'percentage': 0.35},
                {'name': 'Bihor', 'code': 'BH', 'voters': 1120, 'percentage': 0.22},
                {'name': 'Bistrița-Năsăud', 'code': 'BN', 'voters': 860, 'percentage': 0.17},
                {'name': 'Botoșani', 'code': 'BT', 'voters': 920, 'percentage': 0.19},
                {'name': 'Brăila', 'code': 'BR', 'voters': 780, 'percentage': 0.16},
                {'name': 'Brașov', 'code': 'BV', 'voters': 1580, 'percentage': 0.32},
                {'name': 'București', 'code': 'B', 'voters': 5320, 'percentage': 0.65},
                {'name': 'Buzău', 'code': 'BZ', 'voters': 940, 'percentage': 0.20},
                {'name': 'Călărași', 'code': 'CL', 'voters': 720, 'percentage': 0.15},
                {'name': 'Caraș-Severin', 'code': 'CS', 'voters': 830, 'percentage': 0.17},
                {'name': 'Cluj', 'code': 'CJ', 'voters': 1850, 'percentage': 0.38},
                {'name': 'Constanța', 'code': 'CT', 'voters': 1730, 'percentage': 0.36},
                {'name': 'Covasna', 'code': 'CV', 'voters': 560, 'percentage': 0.12},
                {'name': 'Dâmbovița', 'code': 'DB', 'voters': 1020, 'percentage': 0.21},
                {'name': 'Dolj', 'code': 'DJ', 'voters': 1380, 'percentage': 0.29},
                {'name': 'Galați', 'code': 'GL', 'voters': 1290, 'percentage': 0.27},
                {'name': 'Giurgiu', 'code': 'GR', 'voters': 680, 'percentage': 0.14},
                {'name': 'Gorj', 'code': 'GJ', 'voters': 890, 'percentage': 0.18},
                {'name': 'Harghita', 'code': 'HR', 'voters': 640, 'percentage': 0.13},
                {'name': 'Hunedoara', 'code': 'HD', 'voters': 1060, 'percentage': 0.22},
                {'name': 'Ialomița', 'code': 'IL', 'voters': 710, 'percentage': 0.15},
                {'name': 'Iași', 'code': 'IS', 'voters': 1820, 'percentage': 0.37},
                {'name': 'Ilfov', 'code': 'IF', 'voters': 1120, 'percentage': 0.23},
                {'name': 'Maramureș', 'code': 'MM', 'voters': 1190, 'percentage': 0.24},
                {'name': 'Mehedinți', 'code': 'MH', 'voters': 690, 'percentage': 0.14},
                {'name': 'Mureș', 'code': 'MS', 'voters': 1280, 'percentage': 0.26},
                {'name': 'Neamț', 'code': 'NT', 'voters': 1150, 'percentage': 0.24},
                {'name': 'Olt', 'code': 'OT', 'voters': 950, 'percentage': 0.20},
                {'name': 'Prahova', 'code': 'PH', 'voters': 1680, 'percentage': 0.35},
                {'name': 'Sălaj', 'code': 'SJ', 'voters': 610, 'percentage': 0.13},
                {'name': 'Satu Mare', 'code': 'SM', 'voters': 780, 'percentage': 0.16},
                {'name': 'Sibiu', 'code': 'SB', 'voters': 1140, 'percentage': 0.23},
                {'name': 'Suceava', 'code': 'SV', 'voters': 1350, 'percentage': 0.28},
                {'name': 'Teleorman', 'code': 'TR', 'voters': 810, 'percentage': 0.17},
                {'name': 'Timiș', 'code': 'TM', 'voters': 1620, 'percentage': 0.33},
                {'name': 'Tulcea', 'code': 'TL', 'voters': 580, 'percentage': 0.12},
                {'name': 'Vâlcea', 'code': 'VL', 'voters': 970, 'percentage': 0.20},
                {'name': 'Vaslui', 'code': 'VS', 'voters': 830, 'percentage': 0.17},
                {'name': 'Vrancea', 'code': 'VN', 'voters': 760, 'percentage': 0.16}
            ]
        }
        
        return Response(map_info)