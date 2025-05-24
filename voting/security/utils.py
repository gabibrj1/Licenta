from django.utils import timezone
from .models import SecurityEvent, SecurityAlert, CaptchaAttempt
import logging
import user_agents
from django.contrib.sessions.models import Session
from .models import UserSession

logger = logging.getLogger(__name__)

def get_client_info(request):
    """Extrage informații despre client din request"""
    if not request:
        return {}
    
    # IP Address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR', '')
    
    # User Agent
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = user_agents.parse(user_agent_string)
    
    # Device Info
    device_info = {
        'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
        'os': f"{user_agent.os.family} {user_agent.os.version_string}",
        'device': user_agent.device.family,
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'is_bot': user_agent.is_bot,
        'type': 'mobile' if user_agent.is_mobile else 'tablet' if user_agent.is_tablet else 'desktop'
    }
    
    # Location Info basic
    location_info = {
        'ip': ip_address,
        'country': 'Unknown',
        'city': 'Unknown',
    }
    
    return {
        'ip_address': ip_address,
        'user_agent': user_agent_string,
        'device_info': device_info,
        'location_info': location_info,
    }

def create_security_event(user=None, event_type='', description='', request=None, 
                         additional_data=None, risk_level='low'):
    """Creează un eveniment de securitate"""
    try:
        client_info = get_client_info(request) if request else {}
        
        SecurityEvent.objects.create(
            user=user,
            event_type=event_type,
            risk_level=risk_level,
            description=description,
            ip_address=client_info.get('ip_address'),
            user_agent=client_info.get('user_agent'),
            device_info=client_info.get('device_info', {}),
            location_info=client_info.get('location_info', {}),
            additional_data=additional_data or {},
            session_key=request.session.session_key if request and hasattr(request, 'session') else None,
        )
        logger.info(f"Eveniment de securitate creat: {event_type} pentru {user}")
    except Exception as e:
        logger.error(f"Eroare la crearea evenimentului de securitate: {e}")

def create_security_alert(user, alert_type, severity, title, message, details=None):
    """Creează o alertă de securitate"""
    try:
        SecurityAlert.objects.create(
            user=user,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details=details or {},
            requires_user_action=severity in ['error', 'critical']
        )
    except Exception as e:
        logger.error(f"Eroare la crearea alertei de securitate: {e}")

def log_captcha_attempt(request, is_success, captcha_type='recaptcha', context='', user=None):
    """Logează o încercare de CAPTCHA - ÎMBUNĂTĂȚIT"""
    try:
        client_info = get_client_info(request)
        
        # Creează înregistrarea CAPTCHA
        CaptchaAttempt.objects.create(
            user=user,
            ip_address=client_info.get('ip_address', ''),
            session_key=request.session.session_key if hasattr(request, 'session') else None,
            captcha_type=captcha_type,
            is_success=is_success,
            context=context,
            user_agent=client_info.get('user_agent', '')
        )
        
        # Creează eveniment de securitate ÎNTOTDEAUNA
        event_type = 'captcha_success' if is_success else 'captcha_failed'
        risk_level = 'low' if is_success else 'medium'
        
        create_security_event(
            user=user,
            event_type=event_type,
            description=f"CAPTCHA {captcha_type} {'reușit' if is_success else 'eșuat'} în contextul {context}",
            request=request,
            additional_data={
                'captcha_type': captcha_type,
                'context': context,
                'success': is_success
            },
            risk_level=risk_level
        )
        
        # Verifică pentru încercări multiple eșuate
        if not is_success:
            check_multiple_captcha_failures(client_info.get('ip_address'), user)
            
    except Exception as e:
        logger.error(f"Eroare la logarea încercării CAPTCHA: {e}")

def check_multiple_captcha_failures(ip_address, user=None):
    """Verifică pentru eșecuri multiple de CAPTCHA"""
    from datetime import timedelta
    
    # Verifică ultimele 15 minute
    recent_failures = CaptchaAttempt.objects.filter(
        ip_address=ip_address,
        is_success=False,
        timestamp__gte=timezone.now() - timedelta(minutes=15)
    ).count()
    
    if recent_failures >= 5:  # 5 eșecuri în 15 minute
        create_security_event(
            user=user,
            event_type='captcha_multiple_attempts',
            description=f'Detectate {recent_failures} eșecuri CAPTCHA în ultimele 15 minute',
            risk_level='high',
            additional_data={
                'failure_count': recent_failures,
                'ip_address': ip_address,
                'time_window': '15 minutes'
            }
        )
        
        if user:
            create_security_alert(
                user=user,
                alert_type='captcha_multiple_failures',
                severity='warning',
                title='Eșecuri multiple CAPTCHA',
                message=f'Au fost detectate {recent_failures} eșecuri CAPTCHA în ultimele 15 minute.',
                details={
                    'failure_count': recent_failures,
                    'ip_address': ip_address,
                    'time_window': '15 minutes'
                }
            )

def terminate_all_user_sessions(user, except_current=None):
    """Termină toate sesiunile unui utilizator - RETURNEAZĂ NUMĂRUL DE SESIUNI TERMINATE"""
    
    # Marchează toate sesiunile ca inactive
    user_sessions = UserSession.objects.filter(user=user, is_active=True)
    
    if except_current:
        user_sessions = user_sessions.exclude(session_key=except_current)
    
    terminated_count = 0
    for session in user_sessions:
        session.is_active = False
        session.ended_at = timezone.now()
        session.end_reason = 'force_logout'
        session.save()
        terminated_count += 1
        
        # Șterge sesiunea din Django
        try:
            Session.objects.get(session_key=session.session_key).delete()
        except Session.DoesNotExist:
            pass
    
    # Log eveniment
    if terminated_count > 0:
        create_security_event(
            user=user,
            event_type='force_logout',
            description=f"Deconectare forțată din {terminated_count} sesiuni pentru {user.email if user.email else 'CNP: ' + user.cnp[:3] + '***'}",
            additional_data={
                'terminated_sessions': terminated_count,
                'force_reason': 'force_logout'
            },
            risk_level='medium'
        )
    
    return terminated_count  # RETURNEAZĂ NUMĂRUL DE SESIUNI TERMINATE

def log_vote_security_event(user, event_type, description, additional_data=None, request=None):
    """Log evenimente de securitate specifice votului"""
    risk_mapping = {
        'facial_recognition_failed': 'high',
        'facial_recognition_success': 'low',
        'anti_spoofing_triggered': 'critical',
        'multiple_faces_detected': 'critical',
        'id_card_scan_success': 'low',
        'id_card_scan_failed': 'medium',
        'vote_cast': 'low',
        'vote_attempted': 'medium',
        'vote_verification_success': 'low',
        'vote_verification_failed': 'high',
        'vote_page_access': 'low',
        'vote_session_started': 'low',
        'vote_session_ended': 'low',
    }
    
    risk_level = risk_mapping.get(event_type, 'medium')
    
    create_security_event(
        user=user,
        event_type=event_type,
        description=description,
        request=request,
        additional_data=additional_data,
        risk_level=risk_level
    )
    
    # Creează alerte pentru evenimente critice
    if risk_level in ['high', 'critical']:
        alert_titles = {
            'facial_recognition_failed': 'Recunoaștere facială eșuată',
            'anti_spoofing_triggered': 'Detectat anti-spoofing',
            'multiple_faces_detected': 'Detectate mai multe fețe',
            'id_card_scan_failed': 'Scanare buletin eșuată',
            'vote_verification_failed': 'Verificare vot eșuată',
        }
        
        alert_type = 'facial_recognition_anomaly' if 'facial' in event_type else 'voting_anomaly'
        if 'id_card' in event_type:
            alert_type = 'id_verification_issues'
        
        create_security_alert(
            user=user,
            alert_type=alert_type,
            severity='critical' if risk_level == 'critical' else 'error',
            title=alert_titles.get(event_type, 'Eveniment de securitate'),
            message=description,
            details=additional_data or {}
        )

def log_2fa_event(user, event_type, is_success, request=None, additional_data=None):
    """Logează evenimente pentru autentificarea cu 2 factori"""
    if is_success:
        event_type_final = f'{event_type}_success' if event_type in ['2fa'] else event_type
        risk_level = 'low'
        description = f"2FA {event_type} reușit"
    else:
        event_type_final = f'{event_type}_failed' if event_type in ['2fa'] else event_type
        risk_level = 'medium'
        description = f"2FA {event_type} eșuat"
    
    create_security_event(
        user=user,
        event_type=event_type_final,
        description=description,
        request=request,
        additional_data=additional_data or {},
        risk_level=risk_level
    )

def log_gdpr_event(user, action, request=None):
    """Logează evenimente GDPR"""
    create_security_event(
        user=user,
        event_type='gdpr_consent',
        description=f"Acțiune GDPR: {action}",
        request=request,
        additional_data={'gdpr_action': action},
        risk_level='low'
    )

def log_menu_navigation(user, page, request=None):
    """Logează navigarea în meniu"""
    create_security_event(
        user=user,
        event_type='page_visit',
        description=f"Acces la pagina: {page}",
        request=request,
        additional_data={'page': page},
        risk_level='low'
    )

def detect_suspicious_activity(user, request, activity_type, **kwargs):
    """Detectează și loghează activități suspecte"""
    suspicious_indicators = []
    
    # Verificări pentru activitate suspectă
    if activity_type == 'multiple_failed_attempts':
        suspicious_indicators.append('multiple_login_failures')
    elif activity_type == 'unusual_location':
        suspicious_indicators.append('unusual_ip_location')
    elif activity_type == 'rapid_actions':
        suspicious_indicators.append('automated_behavior')
    
    if suspicious_indicators:
        create_security_event(
            user=user,
            event_type='suspicious_activity',
            description=f"Activitate suspectă detectată: {', '.join(suspicious_indicators)}",
            request=request,
            additional_data={
                'suspicious_indicators': suspicious_indicators,
                'activity_type': activity_type,
                **kwargs
            },
            risk_level='high'
        )

def log_device_trust_change(user, device_fingerprint, action, request=None):
    """Logează schimbările în încrederea dispozitivelor"""
    create_security_event(
        user=user,
        event_type='device_trust_changed',
        description=f'Starea de încredere {"activată" if action == "trust" else "dezactivată"} pentru dispozitiv: {device_fingerprint[:8]}...',
        request=request,
        additional_data={
            'device_fingerprint': device_fingerprint[:8],
            'action': action,
            'trust_status': action == 'trust'
        },
        risk_level='low'
    )