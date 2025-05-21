from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid
from datetime import timedelta

class VoteSettings(models.Model):
    vote_type = models.CharField(max_length=20, choices=[
        ('simulare', 'Simulare'),
        ('prezidentiale', 'Alegeri Prezidențiale'),
        ('parlamentare', 'Alegeri Parlamentare'),
        ('locale', 'Alegeri Locale'),
    ])
    is_active = models.BooleanField(default=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Câmpul adăugat
    
    class Meta:
        verbose_name = "Setări Vot"
        verbose_name_plural = "Setări Vot"
    
    def clean(self):
        # Verifică dacă data de sfârșit este după data de început
        if self.end_datetime <= self.start_datetime:
            raise ValidationError({
                'end_datetime': _('Ora de sfârșit trebuie să fie după ora de început.')
            })
        
        # Verifică suprapunerea cu alte sesiuni active
        overlapping_sessions = VoteSettings.objects.filter(
            is_active=True,
        ).exclude(pk=self.pk)  # Exclude acest obiect dacă există deja
        
        for session in overlapping_sessions:
            # Verifică dacă există suprapunere de intervale
            if (self.start_datetime < session.end_datetime and 
                self.end_datetime > session.start_datetime):
                
                raise ValidationError(
                    _(f'Această sesiune de vot se suprapune cu o altă sesiune activă '
                      f'de tip "{session.vote_type}" programată între '
                      f'{session.start_datetime.strftime("%d.%m.%Y, %H:%M")} și '
                      f'{session.end_datetime.strftime("%d.%m.%Y, %H:%M")}.')
                )
    
    def save(self, *args, **kwargs):
        self.clean()  # Apelează metoda de validare înainte de salvare
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.vote_type} ({self.start_datetime.strftime('%d.%m.%Y, %H:%M')} - {self.end_datetime.strftime('%d.%m.%Y, %H:%M')})"
    
# vote/models.py (adaugă aceste modele la codul existent)

class VotingSection(models.Model):
    """Model pentru secțiile de vot"""
    section_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    address_desc = models.CharField(max_length=500, verbose_name="Adresă descriptivă", blank=True, null=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=50)
    locality = models.CharField(max_length=255, verbose_name="Localitate componentă/Sat aparținător", blank=True, null=True)
    
    class Meta:
        verbose_name = "Secție de Vot"
        verbose_name_plural = "Secții de Vot"
    
    def __str__(self):
        return f"Secția {self.section_id} - {self.name}, {self.city}, {self.county}"

class LocalCandidate(models.Model):
    """Model pentru candidații locali"""
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    position = models.CharField(max_length=50, choices=[
        ('mayor', 'Primar'),
        ('councilor', 'Consilier Local'),
        ('county_president', 'Președinte Consiliu Județean'),
        ('county_councilor', 'Consilier Județean'),
    ])
    county = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    photo_url = models.URLField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Candidat Local"
        verbose_name_plural = "Candidați Locali"
    
    def __str__(self):
        return f"{self.name} ({self.party}) - {self.get_position_display()}, {self.city}, {self.county}"



# vote/models.py (corectează definiția pentru LocalVote)

class LocalVote(models.Model):
    """Model pentru voturile locale înregistrate"""
   
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    candidate = models.ForeignKey(LocalCandidate, on_delete=models.CASCADE)
    voting_section = models.ForeignKey(VotingSection, on_delete=models.CASCADE)
    vote_datetime = models.DateTimeField(auto_now_add=True)
    vote_reference = models.CharField(max_length=20, blank=True, null=True)  # Adăugat câmp pentru referință unică
    
    class Meta:
        verbose_name = "Vot Local"
        verbose_name_plural = "Voturi Locale"
        # O constrângere simplă doar pe user și candidate, validarea detaliată va fi în save()
        unique_together = ('user', 'candidate')
    
    def save(self, *args, **kwargs):
        # Verifică dacă utilizatorul a votat deja pentru această poziție în acest județ
        if not self.pk:  # Doar pentru înregistrări noi
            existing_vote = LocalVote.objects.filter(
                user=self.user,
                candidate__position=self.candidate.position,
                candidate__county=self.candidate.county
            ).exists()
            
            if existing_vote:
                from django.core.exceptions import ValidationError
                raise ValidationError(f'Utilizatorul a votat deja pentru poziția {self.candidate.get_position_display()} în județul {self.candidate.county}')
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.candidate} - {self.vote_datetime.strftime('%d.%m.%Y, %H:%M')}"

class PresidentialCandidate(models.Model):
    """Model pentru candidații prezidențiali"""
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    photo_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order_nr = models.IntegerField(default=0)  # Pentru controlul ordinii de afișare
    gender = models.CharField(max_length=1, blank=True, null=True)  # M sau F
    
    class Meta:
        verbose_name = "Candidat Prezidențial"
        verbose_name_plural = "Candidați Prezidențiali"
        ordering = ['order_nr', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.party})"

class PresidentialVote(models.Model):
    """Model pentru voturile prezidențiale înregistrate"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    candidate = models.ForeignKey(PresidentialCandidate, on_delete=models.CASCADE)
    voting_section = models.ForeignKey(VotingSection, on_delete=models.CASCADE, null=True, blank=True)
    vote_datetime = models.DateTimeField(auto_now_add=True)
    vote_reference = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = "Vot Prezidențial"
        verbose_name_plural = "Voturi Prezidențiale"
        unique_together = ('user', 'vote_reference')
    
    def save(self, *args, **kwargs):
        # Verifică dacă utilizatorul a votat deja
        if not self.pk:  # Doar pentru înregistrări noi
            existing_vote = PresidentialVote.objects.filter(
                user=self.user
            ).exists()
            
            if existing_vote:
                from django.core.exceptions import ValidationError
                raise ValidationError('Utilizatorul a votat deja în acest scrutin prezidențial')
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.candidate} - {self.vote_datetime.strftime('%d.%m.%Y, %H:%M')}"
    

class ParliamentaryParty(models.Model):
    """Model pentru partidele parlamentare"""
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20, blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order_nr = models.IntegerField(default=0)  # Pentru controlul ordinii de afișare
    
    class Meta:
        verbose_name = "Partid Parlamentar"
        verbose_name_plural = "Partide Parlamentare"
        ordering = ['order_nr', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name

class ParliamentaryVote(models.Model):
    """Model pentru voturile parlamentare înregistrate"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    party = models.ForeignKey(ParliamentaryParty, on_delete=models.CASCADE)
    vote_datetime = models.DateTimeField(auto_now_add=True)
    vote_reference = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = "Vot Parlamentar"
        verbose_name_plural = "Voturi Parlamentare"
        unique_together = ('user', 'vote_reference')
    
    def save(self, *args, **kwargs):
        # Verifică dacă utilizatorul a votat deja
        if not self.pk:  # Doar pentru înregistrări noi
            existing_vote = ParliamentaryVote.objects.filter(
                user=self.user
            ).exists()
            
            if existing_vote:
                from django.core.exceptions import ValidationError
                raise ValidationError('Utilizatorul a votat deja în acest scrutin parlamentar')
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.party} - {self.vote_datetime.strftime('%d.%m.%Y, %H:%M')}"
    
class VoteSystem(models.Model):
    """Model pentru sistemele de vot personalizate"""
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='vote_systems')
    
    category = models.CharField(max_length=50, choices=[
        ('political', 'Politic'),
        ('organizational', 'Organizațional'),
        ('community', 'Comunitar'),
        ('survey', 'Sondaj'),
        ('decision', 'Decizie'),
        ('other', 'Altele'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Stocare JSON pentru reguli și setări
    rules = models.JSONField(default=dict)
    
    # Status-ul sistemului
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'În așteptare'),
        ('active', 'Activ'),
        ('completed', 'Încheiat'),
        ('rejected', 'Respins'),
    ])
    
    # Verificare manuală
    admin_verified = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Verificare prin email
    require_email_verification = models.BooleanField(default=False,
        help_text="Dacă este activat, utilizatorii vor trebui să verifice email-ul înainte de a vota")
    
    # Lista de emailuri permise să voteze
    allowed_emails = models.TextField(blank=True, null=True,
        help_text="Lista de emailuri permise să voteze, separate prin virgulă")
    
    class Meta:
        verbose_name = "Sistem de vot"
        verbose_name_plural = "Sisteme de vot"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (creat de {self.creator.email})"
    
    def update_status(self):
        """Actualizează automat status-ul în funcție de data curentă"""
        now = timezone.now()
        
        # Dacă nu a fost verificat de admin rămâne în așteptare
        if not self.admin_verified:
            self.status = 'pending'
            return self.status
        
        if now < self.start_date:
            self.status = 'pending'
        elif self.start_date <= now <= self.end_date:
            self.status = 'active'
        elif now > self.end_date:
            self.status = 'completed'
        
        return self.status


class VoteOption(models.Model):
    """Model pentru opțiunile din cadrul unui sistem de vot"""
    vote_system = models.ForeignKey(VoteSystem, on_delete=models.CASCADE, related_name='options')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Opțiune de vot"
        verbose_name_plural = "Opțiuni de vot"
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.title} ({self.vote_system.name})"


class VoteCast(models.Model):
    """Model pentru voturile efectuate"""
    vote_system = models.ForeignKey(VoteSystem, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(VoteOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    anonymous_id = models.CharField(max_length=100, blank=True, null=True)  # Pentru voturile anonime
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    vote_datetime = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vot"
        verbose_name_plural = "Voturi"
        # Un utilizator poate vota o singură dată pentru fiecare sistem (excepție: vot multiplu)
        constraints = [
            models.UniqueConstraint(
                fields=['vote_system', 'user'],
                name='unique_user_vote_per_system',
                condition=models.Q(user__isnull=False)
            )
        ]
    
    def __str__(self):
        if self.user:
            return f"Vot de {self.user.email} pentru {self.option.title}"
        return f"Vot anonim pentru {self.option.title}"
    
# Modele pentru one time tokens
class VoteToken(models.Model):
    """Model pentru token-uri de vot de unică folosință"""
    vote_system = models.ForeignKey(VoteSystem, on_delete=models.CASCADE, related_name='vote_tokens')
    email = models.EmailField()
    token = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Token vot"
        verbose_name_plural = "Token-uri vot"
        unique_together = ('vote_system', 'email')  # Un singur token per email per sistem de vot
    
    def __str__(self):
        status = "Folosit" if self.used else "Nefolosit"
        return f"Token pentru {self.email}: {self.token[:10]}... ({status})"
    
    def save(self, *args, **kwargs):
        # Generează un token aleator dacă nu există unul
        if not self.token:
            self.token = self.generate_token()
        
        # Setează data de expirare dacă nu există una (3 minute după creare)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=3)
            
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_token():
        """Generează un token unic de 6 caractere alfanumerice"""
        import random
        import string
        # Generăm un token scurt, ușor de introdus de către utilizator
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))
    
    def is_valid(self):
        """Verifică dacă token-ul este valid (nefolosit și neexpirat)"""
        now = timezone.now()
        return not self.used and now <= self.expires_at