from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class SecurityEvent(models.Model):
    EVENT_TYPES = [
        ('login_success', 'Autentificare reușită'),
        ('login_failed', 'Autentificare eșuată'),
        ('logout', 'Deconectare'),
        ('password_change', 'Schimbare parolă'),
        ('password_reset_request', 'Solicitare resetare parolă'),
        ('password_reset_success', 'Resetare parolă reușită'),
        ('2fa_enabled', 'Activare autentificare 2FA'),
        ('2fa_disabled', 'Dezactivare autentificare 2FA'),
        ('2fa_failed', 'Autentificare 2FA eșuată'),
        ('2fa_success', 'Autentificare 2FA reușită'),
        ('captcha_success', 'Verificare CAPTCHA reușită'),
        ('captcha_failed', 'Verificare CAPTCHA eșuată'),
        ('captcha_multiple_attempts', 'Încercări multiple CAPTCHA'),
        ('vote_cast', 'Vot emis'),
        ('vote_attempted', 'Încercare vot'),
        ('facial_recognition_failed', 'Recunoaștere facială eșuată'),
        ('facial_recognition_success', 'Recunoaștere facială reușită'),
        ('anti_spoofing_triggered', 'Detectie anti-spoofing'),
        ('multiple_faces_detected', 'Detectie mai multe fețe'),
        ('id_card_scan_success', 'Scanare buletin reușită'),
        ('id_card_scan_failed', 'Scanare buletin eșuată'),
        ('device_fingerprint_match', 'Dispozitiv cunoscut detectat'),
        ('new_device_detected', 'Dispozitiv nou detectat'),
        ('suspicious_device_detected', 'Dispozitiv suspect detectat'),
        ('device_marked_trusted', 'Dispozitiv marcat ca de încredere'),
        ('device_trust_changed', 'Stare încredere dispozitiv schimbată'),
        ('suspicious_activity', 'Activitate suspectă'),
        ('data_export', 'Export date'),
        ('profile_update', 'Actualizare profil'),
        ('account_locked', 'Cont blocat'),
        ('account_unlocked', 'Cont deblocat'),
        ('session_expired', 'Sesiune expirată'),
        ('force_logout', 'Deconectare forțată'),
        ('gdpr_consent', 'Consimțământ GDPR'),
        ('email_verification', 'Verificare email'),
        ('page_visit', 'Vizitare pagină'),
        ('profile_access', 'Acces profil'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Scăzut'),
        ('medium', 'Mediu'),
        ('high', 'Ridicat'),
        ('critical', 'Critic'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, default='low')
    
    # Detalii despre eveniment
    description = models.TextField(verbose_name="Descriere eveniment")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    device_info = models.JSONField(default=dict, blank=True)
    location_info = models.JSONField(default=dict, blank=True)
    
    # Metadate pentru context
    additional_data = models.JSONField(default=dict, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    
    # Timestamp și stare
    timestamp = models.DateTimeField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_events')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Eveniment Securitate"
        verbose_name_plural = "Evenimente Securitate"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['risk_level', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        user_info = f" - {self.user.email}" if self.user else " - Anonymous"
        return f"{self.get_event_type_display()}{user_info} ({self.timestamp})"

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    
    # Informații despre sesiune
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict)
    location_info = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    # Stare sesiune
    is_active = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False)
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = "Sesiune Utilizator"
        verbose_name_plural = "Sesiuni Utilizatori"
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active', '-last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address} ({self.created_at})"
    
    @property
    def duration(self):
        end_time = self.ended_at or timezone.now()
        return end_time - self.created_at
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

class SecurityAlert(models.Model):
    ALERT_TYPES = [
        ('multiple_failed_logins', 'Încercări multiple de autentificare'),
        ('captcha_multiple_failures', 'Eșecuri multiple CAPTCHA'),
        ('multiple_devices', 'Dispozitive multiple detectate'),
        ('suspicious_device', 'Dispozitiv suspect'),
        ('suspicious_location', 'Locație suspectă'),
        ('unusual_activity', 'Activitate neobișnuită'),
        ('potential_fraud', 'Potențială fraudă'),
        ('security_breach', 'Breach de securitate'),
        ('facial_recognition_anomaly', 'Anomalie recunoaștere facială'),
        ('voting_anomaly', 'Anomalie la vot'),
        ('id_verification_issues', 'Probleme verificare identitate'),
        ('weak_password', 'Parolă slabă'),
        ('password_reuse', 'Reutilizare parolă'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Informativ'),
        ('warning', 'Avertisment'),
        ('error', 'Eroare'),
        ('critical', 'Critic'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Stare alert
    is_active = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Acțiuni automate
    auto_action_taken = models.JSONField(default=dict, blank=True)
    requires_user_action = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Alertă Securitate"
        verbose_name_plural = "Alerte Securitate"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['alert_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_severity_display()}"

class CaptchaAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=40, blank=True, null=True)
    
    # Detalii CAPTCHA
    captcha_type = models.CharField(max_length=50, default='recaptcha')
    is_success = models.BooleanField()
    attempt_count = models.IntegerField(default=1)
    
    # Context unde a fost folosit CAPTCHA
    context = models.CharField(max_length=100, blank=True)
    
    # Metadate
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Încercare CAPTCHA"
        verbose_name_plural = "Încercări CAPTCHA"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['is_success', '-timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.is_success else "Failed"
        user_info = f" - {self.user.email}" if self.user else f" - IP: {self.ip_address}"
        return f"CAPTCHA {status}{user_info} ({self.timestamp})"

class DeviceFingerprint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    fingerprint_hash = models.CharField(max_length=64, db_index=True)
    
    # Informații despre dispozitiv colectate automat din browser
    screen_resolution = models.CharField(max_length=20, blank=True)
    color_depth = models.IntegerField(null=True, blank=True)
    timezone_offset = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, blank=True)
    platform = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Caracteristici browser
    has_cookies = models.BooleanField(default=True)
    has_local_storage = models.BooleanField(default=True)
    has_session_storage = models.BooleanField(default=True)
    canvas_fingerprint = models.CharField(max_length=64, blank=True)
    
    # Stare și utilizare
    is_trusted = models.BooleanField(default=False)
    is_suspicious = models.BooleanField(default=False)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    usage_count = models.IntegerField(default=1)
    
    # Locații tipice
    typical_ips = models.JSONField(default=list, blank=True)
    
    class Meta:
        verbose_name = "Device Fingerprint"
        verbose_name_plural = "Device Fingerprints"
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['fingerprint_hash']),
            models.Index(fields=['user', '-last_seen']),
            models.Index(fields=['is_trusted']),
            models.Index(fields=['is_suspicious']),
        ]
    
    def __str__(self):
        user_info = f"{self.user.email}" if self.user else "Anonymous"
        return f"{user_info} - {self.fingerprint_hash[:8]}..."
    
    def mark_as_suspicious(self, reason=''):
        """Marchează dispozitivul ca suspect"""
        if not self.is_suspicious:
            self.is_suspicious = True
            self.save()
            
            # Creează alertă de securitate
            if self.user:
                from .utils import create_security_alert
                create_security_alert(
                    user=self.user,
                    alert_type='suspicious_device',
                    severity='warning',
                    title='Dispozitiv suspect detectat',
                    message=f'Dispozitivul cu fingerprint {self.fingerprint_hash[:8]}... a fost marcat ca suspect.',
                    details={'fingerprint': self.fingerprint_hash[:8], 'reason': reason}
                )