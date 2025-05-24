from django.db.models.signals import post_save, post_delete, pre_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import SecurityEvent, UserSession, SecurityAlert
from .utils import get_client_info, create_security_event
import logging
from django.contrib.auth.signals import user_logged_out

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Log autentificare reușită"""
    client_info = get_client_info(request)
    
    create_security_event(
        user=user,
        event_type='login_success',
        description=f"Autentificare reușită pentru {user.email}",
        request=request,
        additional_data=client_info
    )
    
    # Creează sau actualizează sesiunea utilizatorului
    session_key = request.session.session_key
    if session_key:
        # Marchează toate sesiunile anterioare ca nefiind curente
        UserSession.objects.filter(user=user, is_current=True).update(is_current=False)
        
        # Creează noua sesiune
        user_session, created = UserSession.objects.update_or_create(
            session_key=session_key,
            defaults={
                'user': user,
                'ip_address': client_info.get('ip_address', ''),
                'user_agent': client_info.get('user_agent', ''),
                'device_info': client_info.get('device_info', {}),
                'location_info': client_info.get('location_info', {}),
                'is_current': True,
                'is_active': True,
                'expires_at': request.session.get_expiry_date(),
            }
        )
        
        if created:
            logger.info(f"Sesiune nouă creată pentru {user.email}")

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    """Log deconectare - CORECTAT"""
    if user and user.is_authenticated:
        create_security_event(
            user=user,
            event_type='logout',
            description=f"Deconectare pentru {user.email}",
            request=request
        )
        
        # Marchează sesiunea ca încheiată
        session_key = getattr(request.session, 'session_key', None)
        if session_key:
            try:
                user_session = UserSession.objects.get(session_key=session_key, user=user)
                user_session.is_active = False
                user_session.is_current = False
                user_session.ended_at = timezone.now()
                user_session.end_reason = 'logout'
                user_session.save()
                logger.info(f"Sesiune încheiată pentru {user.email}")
            except UserSession.DoesNotExist:
                logger.warning(f"Sesiune nu a fost găsită pentru deconectare: {user.email}")

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log autentificare eșuată"""
    email = credentials.get('email', 'Unknown')
    client_info = get_client_info(request)
    
    create_security_event(
        user=None,
        event_type='login_failed',
        description=f"Încercare de autentificare eșuată pentru {email}",
        request=request,
        additional_data={
            'attempted_email': email,
            **client_info
        },
        risk_level='medium'
    )
    
    # Verifică pentru încercări multiple
    check_multiple_failed_attempts(email, client_info.get('ip_address'))

def check_multiple_failed_attempts(email, ip_address):
    """Verifică pentru încercări multiple de autentificare eșuată"""
    from datetime import timedelta
    
    # Verifică ultimele 15 minute
    recent_failures = SecurityEvent.objects.filter(
        event_type='login_failed',
        timestamp__gte=timezone.now() - timedelta(minutes=15),
        additional_data__attempted_email=email
    ).count()
    
    if recent_failures >= 5:  # 5 încercări eșuate în 15 minute
        try:
            user = User.objects.get(email=email)
            
            SecurityAlert.objects.create(
                user=user,
                alert_type='multiple_failed_logins',
                severity='warning',
                title='Încercări multiple de autentificare',
                message=f'Au fost detectate {recent_failures} încercări de autentificare eșuate în ultimele 15 minute.',
                details={
                    'failed_attempts': recent_failures,
                    'ip_address': ip_address,
                    'time_window': '15 minutes'
                },
                requires_user_action=True
            )
        except User.DoesNotExist:
            pass

# Signal pentru crearea automată de evenimente la acțiuni importante
@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Logare la modificări utilizator"""
    if created:
        create_security_event(
            user=instance,
            event_type='profile_update',
            description=f"Cont nou creat pentru {instance.email}",
            risk_level='low'
        )

# Signal pentru ștersul sesiunilor
@receiver(pre_delete, sender=Session)
def log_session_deletion(sender, instance, **kwargs):
    """Logare când o sesiune este ștearsă"""
    try:
        user_session = UserSession.objects.get(session_key=instance.session_key)
        if user_session.is_active:
            user_session.is_active = False
            user_session.ended_at = timezone.now()
            user_session.end_reason = 'session_expired'
            user_session.save()
            
            create_security_event(
                user=user_session.user,
                event_type='session_expired',
                description=f"Sesiune expirată pentru {user_session.user.email}",
                risk_level='low'
            )
    except UserSession.DoesNotExist:
        pass

@receiver(user_logged_out)
def log_session_timeout(sender, request, user, **kwargs):
    """Loghează când o sesiune expiră sau utilizatorul este deconectat"""
    if user:
        # Verifică dacă este timeout sau logout manual
        if hasattr(request, 'session') and not request.session.get('manual_logout', False):
            create_security_event(
                user=user,
                event_type='session_expired',
                description=f"Sesiune expirată pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
                request=request,
                risk_level='low'
            )