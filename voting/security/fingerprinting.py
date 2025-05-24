import hashlib
import json
from django.utils import timezone
from .models import DeviceFingerprint, SecurityEvent
from .utils import create_security_event, create_security_alert
import logging

logger = logging.getLogger(__name__)

def generate_fingerprint_hash(fingerprint_data):
    """Generează hash-ul unique pentru fingerprint"""
    # Sortează datele pentru consistență
    sorted_data = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()

def process_device_fingerprint(request, fingerprint_data):
    """Procesează fingerprint-ul dispozitivului automat"""
    
    try:
        # Generează hash-ul fingerprint-ului
        fp_hash = generate_fingerprint_hash(fingerprint_data)
        
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key if hasattr(request, 'session') else None
        
        # Verifică dacă fingerprint-ul există deja
        fingerprint, created = DeviceFingerprint.objects.get_or_create(
            fingerprint_hash=fp_hash,
            user=user,
            defaults={
                'session_key': session_key,
                'screen_resolution': fingerprint_data.get('screen_resolution', ''),
                'color_depth': fingerprint_data.get('color_depth'),
                'timezone_offset': fingerprint_data.get('timezone_offset'),
                'language': fingerprint_data.get('language', ''),
                'platform': fingerprint_data.get('platform', ''),
                'user_agent': fingerprint_data.get('user_agent', ''),
                'has_cookies': fingerprint_data.get('has_cookies', True),
                'has_local_storage': fingerprint_data.get('has_local_storage', True),
                'has_session_storage': fingerprint_data.get('has_session_storage', True),
                'canvas_fingerprint': fingerprint_data.get('canvas_fingerprint', ''),
                'typical_ips': [request.META.get('REMOTE_ADDR', '')]
            }
        )
        
        if not created:
            # Actualizează fingerprint-ul existent
            fingerprint.last_seen = timezone.now()
            fingerprint.usage_count += 1
            
            # Adaugă IP-ul curent la lista tipică
            current_ip = request.META.get('REMOTE_ADDR', '')
            if current_ip and current_ip not in fingerprint.typical_ips:
                fingerprint.typical_ips.append(current_ip)
                # Păstrează doar ultimele 10 IP-uri
                if len(fingerprint.typical_ips) > 10:
                    fingerprint.typical_ips = fingerprint.typical_ips[-10:]
            
            fingerprint.save()
            
            # Logează revenirea unui dispozitiv cunoscut
            create_security_event(
                user=user,
                event_type='device_fingerprint_match',
                description=f'Dispozitiv cunoscut: {fp_hash[:8]}...',
                request=request,
                additional_data={'fingerprint_hash': fp_hash[:8], 'usage_count': fingerprint.usage_count},
                risk_level='low'
            )
        else:
            # Nou dispozitiv detectat
            create_security_event(
                user=user,
                event_type='new_device_detected',
                description=f'Dispozitiv nou detectat: {fp_hash[:8]}...',
                request=request,
                additional_data={'fingerprint_hash': fp_hash[:8]},
                risk_level='medium'
            )
            
            # Dacă utilizatorul este autentificat și are deja alte dispozitive
            if user:
                existing_devices = DeviceFingerprint.objects.filter(user=user).count()
                if existing_devices > 3:  # Mai mult de 3 dispozitive
                    create_security_alert(
                        user=user,
                        alert_type='multiple_devices',
                        severity='info',
                        title='Dispozitiv nou adăugat',
                        message=f'Aveți acum {existing_devices} dispozitive înregistrate. Dacă nu recunoașteți acest dispozitiv, vă recomandăm să schimbați parola.',
                        details={'device_count': existing_devices, 'new_fingerprint': fp_hash[:8]}
                    )
        
        # Analiză de securitate automată
        analyze_fingerprint_security(fingerprint, request)
        
        return fingerprint
        
    except Exception as e:
        logger.error(f"Eroare la procesarea fingerprint-ului: {e}")
        return None

def analyze_fingerprint_security(fingerprint, request):
    """Analizează fingerprint-ul pentru potențiale probleme de securitate"""
    
    suspicious_indicators = []
    
    # Verifică pentru automatizare (bots)
    user_agent = fingerprint.user_agent.lower()
    bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'automated']
    if any(indicator in user_agent for indicator in bot_indicators):
        suspicious_indicators.append('potential_bot')
    
    # Verifică pentru fingerprint-uri similare
    similar_fps = DeviceFingerprint.objects.filter(
        canvas_fingerprint=fingerprint.canvas_fingerprint,
        screen_resolution=fingerprint.screen_resolution
    ).exclude(id=fingerprint.id)
    
    if similar_fps.count() > 5:  # Prea multe dispozitive similare
        suspicious_indicators.append('similar_devices')
    
    # Verifică pentru schimbări rapide de IP
    if len(fingerprint.typical_ips) > 5:  # Multe IP-uri diferite
        suspicious_indicators.append('ip_switching')
    
    # Verifică pentru lipsa caracteristicilor de browser
    if not fingerprint.has_cookies or not fingerprint.has_local_storage:
        suspicious_indicators.append('disabled_features')
    
    # Dacă s-au găsit indicatori suspicioși
    if suspicious_indicators:
        fingerprint.mark_as_suspicious(f"Indicatori: {', '.join(suspicious_indicators)}")
        
        create_security_event(
            user=fingerprint.user,
            event_type='suspicious_device_detected',
            description=f'Dispozitiv suspect detectat: {", ".join(suspicious_indicators)}',
            request=request,
            additional_data={
                'fingerprint_hash': fingerprint.fingerprint_hash[:8],
                'suspicious_indicators': suspicious_indicators
            },
            risk_level='high'
        )
def get_trusted_devices(user):
    """Returnează dispozitivele de încredere ale utilizatorului"""
    return DeviceFingerprint.objects.filter(
        user=user,
        is_trusted=True,
        is_suspicious=False
    ).order_by('-last_seen')

def mark_device_as_trusted(fingerprint_hash, user):
    """Marchează un dispozitiv ca fiind de încredere"""
    try:
        fingerprint = DeviceFingerprint.objects.get(
            fingerprint_hash=fingerprint_hash,
            user=user
        )
        fingerprint.is_trusted = True
        fingerprint.is_suspicious = False
        fingerprint.save()
        
        create_security_event(
            user=user,
            event_type='device_marked_trusted',
            description=f'Dispozitiv marcat ca de încredere: {fingerprint_hash[:8]}...',
            additional_data={'fingerprint_hash': fingerprint_hash[:8]},
            risk_level='low'
        )
        
        return True
    except DeviceFingerprint.DoesNotExist:
        return False