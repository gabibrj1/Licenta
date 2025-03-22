from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class VoteSettings(models.Model):
    vote_type = models.CharField(max_length=20, choices=[
        ('simulare', 'Simulare Vot'),
        ('prezidentiale', 'Alegeri Prezidențiale'),
        ('parlamentare', 'Alegeri Parlamentare'),
        ('locale', 'Alegeri Locale'),
    ])
    is_active = models.BooleanField(default=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Setări Vot"
        verbose_name_plural = "Setări Vot"
    
    def clean(self):
        # Verifica daca data de sfarsit este dupa data de inceput
        if self.end_datetime <= self.start_datetime:
            raise ValidationError({
                'end_datetime': _('Ora de sfârșit trebuie să fie după ora de început.')
            })
        
        # Verifica suprapunerea cu alte sesiuni active
        overlapping_sessions = VoteSettings.objects.filter(
            is_active=True,
        ).exclude(pk=self.pk)  # Exclude acest obiect dacă exista deja
        
        for session in overlapping_sessions:
            # Verifica daca exista suprapunere de intervale
            if (self.start_datetime < session.end_datetime and 
                self.end_datetime > session.start_datetime):
                
                raise ValidationError(
                    _(f'Această sesiune de vot se suprapune cu o altă sesiune activă '
                      f'de tip "{session.vote_type}" programată între '
                      f'{session.start_datetime.strftime("%d.%m.%Y, %H:%M")} și '
                      f'{session.end_datetime.strftime("%d.%m.%Y, %H:%M")}.')
                )
    
    def save(self, *args, **kwargs):
        self.clean()  # Apeleaza metoda de validare inainte de salvare
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.vote_type} ({self.start_datetime.strftime('%d.%m.%Y, %H:%M')} - {self.end_datetime.strftime('%d.%m.%Y, %H:%M')})"