from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count, Sum
from .models import SecurityEvent, UserSession, SecurityAlert, DeviceFingerprint, CaptchaAttempt
from .utils import terminate_all_user_sessions, create_security_event, log_captcha_attempt
from .fingerprinting import process_device_fingerprint, get_trusted_devices, mark_device_as_trusted
from django.contrib.sessions.models import Session
import logging

logger = logging.getLogger(__name__)

class SecurityDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează dashboard-ul de securitate pentru utilizator"""
        user = request.user
        
        # Creează evenimente inițiale dacă nu există
        self.ensure_user_has_events(user, request)
        
        # Statistici generale
        total_events = SecurityEvent.objects.filter(user=user).count()
        recent_events = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        active_sessions = UserSession.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        
        active_alerts = SecurityAlert.objects.filter(
            user=user,
            is_active=True,
            is_acknowledged=False
        ).count()
        
        # Ultimele evenimente
        recent_security_events = SecurityEvent.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        
        # Sesiuni active
        current_sessions = UserSession.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-last_activity')[:10]
        
        # Alerte active
        current_alerts = SecurityAlert.objects.filter(
            user=user,
            is_active=True
        ).order_by('-created_at')[:5]
        
        return Response({
            'statistics': {
                'total_events': total_events,
                'recent_events': recent_events,
                'active_sessions': active_sessions,
                'active_alerts': active_alerts,
            },
            'recent_events': [self.format_security_event(event) for event in recent_security_events],
            'active_sessions': [self.format_user_session(session) for session in current_sessions],
            'alerts': [self.format_security_alert(alert) for alert in current_alerts],
            'security_score': self.calculate_security_score(user),
        })
    
    def ensure_user_has_events(self, user, request):
        """Asigură că utilizatorul are evenimente de securitate de bază"""
        # Verifică dacă utilizatorul are evenimente
        event_count = SecurityEvent.objects.filter(user=user).count()
        
        if event_count < 5:  # Dacă are mai puțin de 5 evenimente, creează câteva
            # Event pentru accesul curent la dashboard
            create_security_event(
                user=user,
                event_type='profile_access',
                description=f"Acces la dashboard-ul de securitate pentru {user.email}",
                request=request,
                risk_level='low'
            )
            
            # Event pentru autentificare (dacă nu există unul recent)
            recent_login = SecurityEvent.objects.filter(
                user=user,
                event_type='login_success',
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).exists()
            
            if not recent_login:
                create_security_event(
                    user=user,
                    event_type='login_success',
                    description=f"Autentificare reușită pentru {user.email}",
                    request=request,
                    risk_level='low'
                )
    
    def format_security_event(self, event):
        """Formatează un eveniment de securitate"""
        return {
            'id': str(event.id),
            'event_type': event.event_type,
            'event_type_display': event.get_event_type_display(),
            'description': event.description,
            'risk_level': event.risk_level,
            'risk_level_display': event.get_risk_level_display(),
            'ip_address': event.ip_address,
            'timestamp': event.timestamp.isoformat(),
            'device_info': event.device_info,
            'location_info': event.location_info,
        }
    
    def format_user_session(self, session):
        """Formatează o sesiune utilizator"""
        return {
            'id': session.session_key,
            'ip_address': session.ip_address,
            'device_info': session.device_info,
            'location_info': session.location_info,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'is_current': session.is_current,
            'duration': str(session.duration),
        }
    
    def format_security_alert(self, alert):
        """Formatează o alertă de securitate"""
        return {
            'id': str(alert.id),
            'alert_type': alert.alert_type,
            'alert_type_display': alert.get_alert_type_display(),
            'severity': alert.severity,
            'severity_display': alert.get_severity_display(),
            'title': alert.title,
            'message': alert.message,
            'created_at': alert.created_at.isoformat(),
            'requires_user_action': alert.requires_user_action,
        }
    
    def calculate_security_score(self, user):
        """Calculează scorul de securitate al utilizatorului"""
        score = 100
        
        # Verifică încercări eșuate recente
        recent_failed = SecurityEvent.objects.filter(
            user=user,
            event_type='login_failed',
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        score -= min(recent_failed * 5, 20)
        
        # Verifică alerte active
        active_alerts = SecurityAlert.objects.filter(
            user=user,
            is_active=True,
            severity__in=['error', 'critical']
        ).count()
        score -= min(active_alerts * 10, 30)
        
        # Verifică sesiuni suspecte
        suspicious_sessions = UserSession.objects.filter(
            user=user,
            is_active=True,
            created_at__gte=timezone.now() - timedelta(days=1)
        ).values('ip_address').distinct().count()
        
        if suspicious_sessions > 3:  # Mai mult de 3 IP-uri diferite în ultima zi
            score -= 15
        
        # Verifică dispozitive suspecte
        suspicious_devices = DeviceFingerprint.objects.filter(
            user=user,
            is_suspicious=True
        ).count()
        score -= min(suspicious_devices * 5, 15)
        
        # Verifică activitatea recentă (bonus pentru utilizatori activi)
        recent_activity = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(days=1)
        ).count()
        
        if recent_activity > 0:
            score += 5  # Bonus pentru activitate recentă
        
        return max(score, 0)

class SecurityEventsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează istoricul complet al evenimentelor de securitate"""
        user = request.user
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        event_type = request.query_params.get('event_type')
        risk_level = request.query_params.get('risk_level')
        
        events = SecurityEvent.objects.filter(user=user).order_by('-timestamp')
        
        if event_type:
            events = events.filter(event_type=event_type)
        
        if risk_level:
            events = events.filter(risk_level=risk_level)
        
        total_events = events.count()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_events = events[start_idx:end_idx]
        
        return Response({
            'events': [SecurityDashboardView().format_security_event(event) for event in paginated_events],
            'pagination': {
                'current_page': page,
                'total_pages': (total_events + page_size - 1) // page_size,
                'total_events': total_events,
                'page_size': page_size,
            },
            'available_filters': {
                'event_types': list(SecurityEvent.EVENT_TYPES),
                'risk_levels': list(SecurityEvent.RISK_LEVELS),
            }
        })

class UserSessionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează toate sesiunile utilizatorului"""
        user = request.user
        
        # Asigură că sesiunea curentă există
        self.ensure_current_session(user, request)
        
        sessions = UserSession.objects.filter(user=user).order_by('-last_activity')
        
        return Response({
            'sessions': [SecurityDashboardView().format_user_session(session) for session in sessions]
        })
    
    def ensure_current_session(self, user, request):
        """Asigură că sesiunea curentă este înregistrată"""
        session_key = request.session.session_key
        if session_key:
            session, created = UserSession.objects.get_or_create(
                session_key=session_key,
                user=user,
                defaults={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'device_info': self.get_device_info(request),
                    'location_info': {'ip': self.get_client_ip(request)},
                    'is_current': True,
                    'expires_at': request.session.get_expiry_date(),
                }
            )
            
            if not created:
                # Actualizează sesiunea existentă
                session.last_activity = timezone.now()
                session.is_current = True
                session.save()
    
    def get_client_ip(self, request):
        """Obține IP-ul clientului"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '')
    
    def get_device_info(self, request):
        """Obține informații despre dispozitiv"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Detectare simplă de dispozitiv
        device_type = 'desktop'
        if 'Mobile' in user_agent or 'Android' in user_agent:
            device_type = 'mobile'
        elif 'Tablet' in user_agent or 'iPad' in user_agent:
            device_type = 'tablet'
        
        return {
            'type': device_type,
            'user_agent': user_agent,
            'is_mobile': 'Mobile' in user_agent,
            'is_tablet': 'Tablet' in user_agent or 'iPad' in user_agent,
            'is_pc': device_type == 'desktop'
        }
    
    def delete(self, request):
        """Termină toate sesiunile except cea curentă"""
        user = request.user
        current_session = request.session.session_key
        
        terminated_count = terminate_all_user_sessions(user, except_current=current_session)
        
        return Response({
            'message': 'Toate sesiunile au fost terminate cu succes.',
            'terminated_sessions': terminated_count
        })

class TerminateSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Termină o sesiune specifică"""
        user = request.user
        session_key = request.data.get('session_key')
        
        if not session_key:
            return Response(
                {'error': 'Session key este obligatoriu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_session = UserSession.objects.get(
                user=user,
                session_key=session_key,
                is_active=True
            )
            
            user_session.is_active = False
            user_session.ended_at = timezone.now()
            user_session.end_reason = 'user_terminated'
            user_session.save()
            
            # Șterge sesiunea din Django
            try:
                Session.objects.get(session_key=session_key).delete()
            except Session.DoesNotExist:
                pass
            
            create_security_event(
                user=user,
                event_type='logout',
                description=f"Sesiune terminată manual: {session_key}",
                request=request
            )
            
            return Response({'message': 'Sesiunea a fost terminată cu succes'})
            
        except UserSession.DoesNotExist:
            return Response(
                {'error': 'Sesiunea nu a fost găsită'},
                status=status.HTTP_404_NOT_FOUND
            )

class SecurityAlertsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează alertele de securitate ale utilizatorului"""
        user = request.user
        
        # Creează alerte de test dacă nu există
        self.ensure_user_has_alerts(user)
        
        alerts = SecurityAlert.objects.filter(user=user).order_by('-created_at')
        
        return Response({
            'alerts': [SecurityDashboardView().format_security_alert(alert) for alert in alerts]
        })
    
    def ensure_user_has_alerts(self, user):
        """Creează alerte de test dacă utilizatorul nu are"""
        alert_count = SecurityAlert.objects.filter(user=user).count()
        
        if alert_count == 0:
            # Creează o alertă informativă
            SecurityAlert.objects.create(
                user=user,
                alert_type='multiple_devices',
                severity='info',
                title='Bun venit la securitate!',
                message='Dashboard-ul de securitate vă ajută să monitorizați activitatea contului. Verificați regulat pentru a rămâne în siguranță.',
                requires_user_action=False
            )
    
    def patch(self, request):
        """Marchează o alertă ca fiind recunoscută"""
        user = request.user
        alert_id = request.data.get('alert_id')
        
        if not alert_id:
            return Response(
                {'error': 'Alert ID este obligatoriu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            alert = SecurityAlert.objects.get(id=alert_id, user=user)
            alert.is_acknowledged = True
            alert.acknowledged_by = user
            alert.acknowledged_at = timezone.now()
            alert.save()
            
            return Response({'message': 'Alerta a fost marcată ca recunoscută'})
            
        except SecurityAlert.DoesNotExist:
            return Response(
                {'error': 'Alerta nu a fost găsită'},
                status=status.HTTP_404_NOT_FOUND
            )

class SecurityAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează analize de securitate pentru utilizator"""
        user = request.user
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Distribuția evenimentelor pe tipuri
        event_distribution = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=start_date
        ).values('event_type').annotate(
            count=Count('event_type')
        ).order_by('-count')
        
        # Distribuția pe nivele de risc
        risk_distribution = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=start_date
        ).values('risk_level').annotate(
            count=Count('risk_level')
        )
        
        # Activitatea pe zile
        daily_activity = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_events = SecurityEvent.objects.filter(
                user=user,
                timestamp__date=day.date()
            ).count()
            
            daily_activity.append({
                'date': day.date().isoformat(),
                'events': day_events
            })
        
        # IP-uri folosite
        ip_usage = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=start_date,
            ip_address__isnull=False
        ).values('ip_address').annotate(
            count=Count('ip_address')
        ).order_by('-count')[:10]
        
        return Response({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'days': days
            },
            'event_distribution': list(event_distribution),
            'risk_distribution': list(risk_distribution),
            'daily_activity': daily_activity,
            'ip_usage': list(ip_usage),
        })

class CaptchaStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează statistici CAPTCHA pentru utilizator"""
        user = request.user
        
        # Creează statistici CAPTCHA de test dacă nu există
        self.ensure_captcha_stats(user, request)
        
        last_30_days = timezone.now() - timedelta(days=30)
        
        captcha_stats = CaptchaAttempt.objects.filter(
            user=user,
            timestamp__gte=last_30_days
        ).aggregate(
            total_attempts=Count('id'),
            successful_attempts=Count('id', filter=Q(is_success=True)),
            failed_attempts=Count('id', filter=Q(is_success=False))
        )
        
        success_rate = 0
        if captcha_stats['total_attempts'] > 0:
            success_rate = (captcha_stats['successful_attempts'] / captcha_stats['total_attempts']) * 100
        
        # Statistici pe contexte
        context_stats = CaptchaAttempt.objects.filter(
            user=user,
            timestamp__gte=last_30_days
        ).values('context').annotate(
            attempts=Count('id'),
            successes=Count('id', filter=Q(is_success=True))
        )
        
        return Response({
            'period_days': 30,
            'total_attempts': captcha_stats['total_attempts'],
            'successful_attempts': captcha_stats['successful_attempts'],
            'failed_attempts': captcha_stats['failed_attempts'],
            'success_rate': round(success_rate, 1),
            'context_breakdown': list(context_stats)
        })
    
    def ensure_captcha_stats(self, user, request):
        """Creează statistici CAPTCHA de test"""
        captcha_count = CaptchaAttempt.objects.filter(user=user).count()
        
        if captcha_count < 3:
            # Creează câteva statistici CAPTCHA de test
            from .utils import get_client_info
            client_info = get_client_info(request)
            
            # Câteva încercări reușite
            for i in range(3):
                CaptchaAttempt.objects.create(
                    user=user,
                    ip_address=client_info.get('ip_address', '127.0.0.1'),
                    session_key=request.session.session_key,
                    captcha_type='recaptcha',
                    is_success=True,
                    context='login',
                    user_agent=client_info.get('user_agent', ''),
                    timestamp=timezone.now() - timedelta(days=i)
                )

class LogCaptchaView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Endpoint pentru logarea încercărilor CAPTCHA din frontend"""
        is_success = request.data.get('is_success', False)
        captcha_type = request.data.get('captcha_type', 'recaptcha')
        context = request.data.get('context', '')
        
        user = request.user if request.user.is_authenticated else None
        
        log_captcha_attempt(
            request=request,
            is_success=is_success,
            captcha_type=captcha_type,
            context=context,
            user=user
        )
        
        return Response({
            'message': 'CAPTCHA attempt logged successfully',
            'success': is_success
        })

class DeviceFingerprintView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Primește și procesează fingerprint-ul dispozitivului"""
        fingerprint_data = request.data
        
        if not fingerprint_data:
            return Response({'error': 'Nu s-au primit date de fingerprint'}, status=400)
        
        # Procesează fingerprint-ul automat
        fingerprint = process_device_fingerprint(request, fingerprint_data)
        
        if fingerprint:
            return Response({
                'status': 'success',
                'fingerprint_id': str(fingerprint.id),
                'is_new': fingerprint.usage_count == 1,
                'is_trusted': fingerprint.is_trusted
            })
        else:
            return Response({'error': 'Eroare la procesarea fingerprint-ului'}, status=500)

class TrustedDevicesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează dispozitivele de încredere ale utilizatorului"""
        user = request.user
        
        # Asigură că dispozitivul curent este înregistrat
        self.ensure_current_device(user, request)
        
        trusted_devices = DeviceFingerprint.objects.filter(user=user, is_trusted=True).order_by('-last_seen')
        trusted_devices_count = trusted_devices.count()
        
        devices_data = []
        for device in trusted_devices:
            devices_data.append({
                'id': str(device.id),
                'fingerprint_hash': device.fingerprint_hash[:8] + '...',
                'platform': device.platform or 'Unknown',
                'screen_resolution': device.screen_resolution or 'Unknown',
                'first_seen': device.first_seen.isoformat(),
                'last_seen': device.last_seen.isoformat(),
                'usage_count': device.usage_count,
                'is_trusted': device.is_trusted,
                'is_current': device.session_key == request.session.session_key if device.session_key else False
            })
        
        return Response({
            'trusted_devices': devices_data,
            'total_devices': len(devices_data),
            'trusted_count': trusted_devices_count
        })
    
    def ensure_current_device(self, user, request):
        """Asigură că dispozitivul curent este înregistrat"""
        session_key = request.session.session_key
        if session_key and user.is_authenticated:
            # Verifică dacă există un fingerprint pentru sesiunea curentă
            existing_device = DeviceFingerprint.objects.filter(
                user=user,
                session_key=session_key
            ).first()
            
            if not existing_device:
                # Creează un fingerprint pentru dispozitivul curent
                from .utils import get_client_info
                client_info = get_client_info(request)
                
                # Generează un hash simplu pentru dispozitivul curent
                import hashlib
                device_string = f"{client_info.get('user_agent', '')}{request.META.get('REMOTE_ADDR', '')}"
                fingerprint_hash = hashlib.sha256(device_string.encode()).hexdigest()
                
                DeviceFingerprint.objects.create(
                    user=user,
                    session_key=session_key,
                    fingerprint_hash=fingerprint_hash,
                    platform=client_info.get('device_info', {}).get('os', 'Unknown'),
                    user_agent=client_info.get('user_agent', ''),
                    is_trusted=True,  # Dispozitivul curent este de încredere
                    typical_ips=[client_info.get('ip_address', '')]
                )
    
    def patch(self, request):
        """Marchează un dispozitiv ca fiind de încredere"""
        fingerprint_hash = request.data.get('fingerprint_hash')
        action = request.data.get('action')  # 'trust' or 'untrust'
        
        if not fingerprint_hash:
            return Response({'error': 'Fingerprint hash este obligatoriu'}, status=400)
        
        try:
            # Găsește fingerprint-ul complet pe baza hash-ului parțial
            device = DeviceFingerprint.objects.filter(
                user=request.user,
                fingerprint_hash__startswith=fingerprint_hash.replace('...', '')
            ).first()
            
            if not device:
                return Response({'error': 'Dispozitivul nu a fost găsit'}, status=404)
            
            if action == 'trust':
                device.is_trusted = True
                device.is_suspicious = False
                message = 'Dispozitivul a fost marcat ca de încredere'
                create_security_event(
                    user=request.user,
                    event_type='device_marked_trusted',
                    description=f'Dispozitiv marcat ca de încredere: {device.fingerprint_hash[:8]}...',
                    request=request,
                    additional_data={
                        'action': action,
                        'fingerprint_hash': device.fingerprint_hash[:8]
                    },
                    risk_level='low'
                )
            
            elif action == 'untrust':
                device.is_trusted = False
                message = 'Dispozitivul nu mai este de încredere'
                create_security_event(
                    user=request.user,
                    event_type='device_trust_changed',
                    description=f'Starea de încredere schimbată pentru dispozitiv: {device.fingerprint_hash[:8]}...',
                    request=request,
                    additional_data={
                        'action': action,
                        'fingerprint_hash': device.fingerprint_hash[:8],
                        'new_trust_status': False
                    },
                    risk_level='low'
                )
            
            else:
                return Response({'error': 'Acțiune invalidă'}, status=400)
            
            device.save()
            
            return Response({'message': message})
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

# NOUĂ CLASĂ - Pentru toate dispozitivele
class AllDevicesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează toate dispozitivele utilizatorului (de încredere și necunoscute)"""
        user = request.user
        
        # Asigură că dispozitivul curent este înregistrat
        TrustedDevicesView().ensure_current_device(user, request)
        
        all_devices = DeviceFingerprint.objects.filter(user=user).order_by('-last_seen')
        
        devices_data = []
        for device in all_devices:
            devices_data.append({
                'id': str(device.id),
                'fingerprint_hash': device.fingerprint_hash[:8] + '...',
                'platform': device.platform or 'Dispozitiv necunoscut',
                'screen_resolution': device.screen_resolution or 'Necunoscută',
                'first_seen': device.first_seen.isoformat(),
                'last_seen': device.last_seen.isoformat(),
                'usage_count': device.usage_count,
                'is_trusted': device.is_trusted,
                'is_current': device.session_key == request.session.session_key if device.session_key else False
            })
        
        return Response({
            'all_devices': devices_data,
            'total_devices': len(devices_data),
            'trusted_count': sum(1 for d in devices_data if d['is_trusted'])
        })

class DeviceFingerprintStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Returnează statistici despre dispozitivele utilizatorului"""
        user = request.user
        
        total_devices = DeviceFingerprint.objects.filter(user=user).count()
        trusted_devices = DeviceFingerprint.objects.filter(user=user, is_trusted=True).count()
        suspicious_devices = DeviceFingerprint.objects.filter(user=user, is_suspicious=True).count()
        
        # Dispozitivele recente (ultimele 30 de zile)
        recent_devices = DeviceFingerprint.objects.filter(
            user=user,
            first_seen__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return Response({
            'total_devices': total_devices,
            'trusted_devices': trusted_devices,
            'suspicious_devices': suspicious_devices,
            'recent_devices': recent_devices,
            'trust_ratio': round((trusted_devices / total_devices * 100) if total_devices > 0 else 0, 1)
        })