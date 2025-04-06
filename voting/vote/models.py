from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

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