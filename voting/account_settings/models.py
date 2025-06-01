from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class ProfileImage(models.Model):
    # Model pentru stocarea imaginilor de profil pentru utilizatori
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_image')
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Profile image for {self.user.email or self.user.cnp}"

class AccountSettings(models.Model):
    # Model pentru stocarea setărilor contului pentru utilizatori
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account_settings')
    
    # Preferințe de notificări
    email_notifications = models.BooleanField(default=True)
    vote_reminders = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    
    # Setări de confidențialitate
    show_name_in_forums = models.BooleanField(default=False)
    show_activity_history = models.BooleanField(default=False)
    
    # Setări de accesibilitate
    high_contrast = models.BooleanField(default=False)
    large_font = models.BooleanField(default=False)
    
    # Preferință de limbă
    LANGUAGE_CHOICES = [
        ('ro', _('Romanian')),
        ('en', _('English')),
        ('hu', _('Hungarian')),
    ]
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='ro',
    )
    
    # Autentificare în doi factori
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True, null=True)  # Pentru stocarea secretului TOTP
    two_factor_verified = models.BooleanField(default=False)
    
    # Ultima actualizare a profilului
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Account settings for {self.user.email or self.user.cnp}"