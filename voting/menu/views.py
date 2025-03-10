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