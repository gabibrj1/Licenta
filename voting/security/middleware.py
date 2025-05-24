from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .utils import create_security_event, get_client_info
from .models import UserSession
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class SecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Procesează cererea pentru evenimente de securitate"""
        
        # Loghează accesul la pagini importante pentru utilizatorii autentificați
        if request.user.is_authenticated:
            # Lista paginilor importante de monitorizat
            important_pages = [
                '/api/menu/profile/',
                '/api/security/',
                '/vot/',
                '/menu/setari-cont/',
                '/menu/securitate/'
            ]
            
            # Verifică dacă este o pagină importantă
            for page in important_pages:
                if request.path.startswith(page):
                    create_security_event(
                        user=request.user,
                        event_type='page_visit',
                        description=f"Acces la pagina {request.path}",
                        request=request,
                        risk_level='low'
                    )
                    break
        
        # Actualizează ultima activitate pentru sesiuni autentificate
        if request.user.is_authenticated and hasattr(request, 'session'):
            try:
                user_session = UserSession.objects.get(
                    session_key=request.session.session_key,
                    user=request.user,
                    is_active=True
                )
                user_session.last_activity = timezone.now()
                user_session.save(update_fields=['last_activity'])
            except UserSession.DoesNotExist:
                # Creează sesiunea dacă nu există
                client_info = get_client_info(request)
                UserSession.objects.create(
                    session_key=request.session.session_key,
                    user=request.user,
                    ip_address=client_info.get('ip_address', ''),
                    user_agent=client_info.get('user_agent', ''),
                    device_info=client_info.get('device_info', {}),
                    location_info=client_info.get('location_info', {}),
                    is_current=True,
                    expires_at=request.session.get_expiry_date(),
                )
            if request.user.is_authenticated and hasattr(request.user, 'email') and request.user.email:
                important_pages = [
                    '/menu/',
                    '/vote/',
                    '/contact/',
                    '/menu/profile/',
                    '/menu/securitate/'
                ]

                for page in important_pages:
                    if request.path.startswith(page):
                        create_security_event(
                            user=request.user,
                            event_type='page_visit',
                            description=f"Acces la pagina {request.path}",
                            request=request,
                            additional_data={'page_url': request.path},
                            risk_level='low'
                        )
                        break
        
        return None

    def process_exception(self, request, exception):
        """Logează excepțiile ca evenimente de securitate"""
        if request.user.is_authenticated:
            create_security_event(
                user=request.user,
                event_type='suspicious_activity',
                description=f'Excepție în aplicație: {str(exception)}',
                request=request,
                risk_level='medium'
            )
        
        return None

class FingerprintMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        """Injectează automat JavaScript-ul de fingerprinting în toate paginile HTML"""
        
        # Doar pentru răspunsuri HTML
        if (response.status_code == 200 and 
            'text/html' in response.get('Content-Type', '') and
            hasattr(response, 'content')):
            
            try:
                content = response.content.decode('utf-8')
                
                # Injectează scriptul înainte de </body>
                fingerprint_script = '''
                <script>
                    // Fingerprinting automat - încărcat automat în toate paginile
                    (function() {
                        'use strict';
                        
                        function generateCanvasFingerprint() {
                            try {
                                const canvas = document.createElement('canvas');
                                const ctx = canvas.getContext('2d');
                                ctx.textBaseline = 'top';
                                ctx.font = '14px Arial';
                                ctx.fillText('Device fingerprint canvas 🔒', 2, 2);
                                return canvas.toDataURL().substring(0, 50);
                            } catch (e) {
                                return '';
                            }
                        }
                        
                        function detectDeviceType() {
                            const userAgent = navigator.userAgent.toLowerCase();
                            
                            if (/tablet|ipad|playbook|silk/i.test(userAgent)) {
                                return 'tablet';
                            }
                            if (/mobi|android|touch|blackberry|nokia|windows phone/i.test(userAgent)) {
                                return 'mobile';
                            }
                            return 'desktop';
                        }
                        
                        function collectFingerprint() {
                            return {
                                screen_resolution: `${screen.width}x${screen.height}`,
                                color_depth: screen.colorDepth,
                                timezone_offset: new Date().getTimezoneOffset(),
                                language: navigator.language || navigator.userLanguage,
                                platform: navigator.platform,
                                user_agent: navigator.userAgent,
                                has_cookies: navigator.cookieEnabled,
                                has_local_storage: typeof(Storage) !== "undefined",
                                has_session_storage: typeof(sessionStorage) !== "undefined",
                                canvas_fingerprint: generateCanvasFingerprint(),
                                device_type: detectDeviceType(),
                                device_memory: navigator.deviceMemory || 'unknown',
                                hardware_concurrency: navigator.hardwareConcurrency || 'unknown'
                            };
                        }
                        
                        function sendFingerprint() {
                            const fingerprint = collectFingerprint();
                            
                            fetch('/api/security/fingerprint/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCsrfToken()
                                },
                                body: JSON.stringify(fingerprint)
                            }).catch(error => {
                                console.debug('Fingerprint collection failed:', error);
                            });
                        }
                        
                        function getCsrfToken() {
                            const cookies = document.cookie.split(';');
                            for (let cookie of cookies) {
                                const [name, value] = cookie.trim().split('=');
                                if (name === 'csrftoken') {
                                    return value;
                                }
                            }
                            return '';
                        }
                        
                        // Colectează fingerprint-ul când pagina se încarcă
                        if (document.readyState === 'loading') {
                            document.addEventListener('DOMContentLoaded', sendFingerprint);
                        } else {
                            setTimeout(sendFingerprint, 1000); // Mic delay pentru a lăsa pagina să se încarce
                        }
                    })();
                </script>
                '''
                
                if '</body>' in content:
                    content = content.replace('</body>', fingerprint_script + '</body>')
                    response.content = content.encode('utf-8')
                    response['Content-Length'] = len(response.content)
                
            except Exception as e:
                # Nu afectează funcționarea aplicației dacă fingerprinting-ul eșuează
                pass
        
        return response