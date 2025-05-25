from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AccessibilitySettings(models.Model):
    FONT_SIZES = [
        ('small', 'Mic (14px)'),
        ('medium', 'Mediu (16px)'),
        ('large', 'Mare (18px)'),
        ('extra_large', 'Extra Mare (22px)'),
    ]
    
    CONTRAST_MODES = [
        ('normal', 'Normal'),
        ('high', 'Contrast Ridicat'),
        ('dark', 'Temă Întunecată'),
    ]
    
    ANIMATION_SETTINGS = [
        ('enabled', 'Activate'),
        ('reduced', 'Reduse'),
        ('disabled', 'Dezactivate'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='accessibility_settings')
    
    # Setări vizuale
    font_size = models.CharField(max_length=20, choices=FONT_SIZES, default='medium')
    contrast_mode = models.CharField(max_length=20, choices=CONTRAST_MODES, default='normal')
    animations = models.CharField(max_length=20, choices=ANIMATION_SETTINGS, default='enabled')
    focus_highlights = models.BooleanField(default=False, verbose_name="Evidențiere focus")
    
    # Setări pentru vot
    extended_time = models.BooleanField(default=False, verbose_name="Timp extins pentru vot")
    simplified_interface = models.BooleanField(default=False, verbose_name="Interfață simplificată")
    audio_assistance = models.BooleanField(default=False, verbose_name="Asistență audio")
    keyboard_navigation = models.BooleanField(default=False, verbose_name="Navigare doar cu tastatura")
    
    # Setări de confirmări
    extra_confirmations = models.BooleanField(default=False, verbose_name="Confirmări suplimentare")
    large_buttons = models.BooleanField(default=False, verbose_name="Butoane mari")
    
    # Setări notificări
    screen_reader_support = models.BooleanField(default=False, verbose_name="Suport cititor de ecran")
    audio_notifications = models.BooleanField(default=False, verbose_name="Notificări audio")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Setări Accesibilitate"
        verbose_name_plural = "Setări Accesibilitate"
    
    def __str__(self):
        return f"Setări accesibilitate - {self.user.email}"