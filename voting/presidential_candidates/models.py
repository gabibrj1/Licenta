from django.db import models
from django.utils.text import slugify

class HistoricalEvent(models.Model):
    """Model pentru evenimente istorice legate de alegerile prezidențiale"""
    year = models.IntegerField(verbose_name="Anul evenimentului")
    title = models.CharField(max_length=200, verbose_name="Titlul evenimentului")
    description = models.TextField(verbose_name="Descrierea evenimentului")
    importance = models.IntegerField(default=1, choices=[
        (1, "Normal"),
        (2, "Important"),
        (3, "Foarte important")
    ], verbose_name="Importanța evenimentului")
    
    class Meta:
        verbose_name = "Eveniment istoric"
        verbose_name_plural = "Evenimente istorice"
        ordering = ['-year', 'title']
    
    def __str__(self):
        return f"{self.year} - {self.title}"

class ElectionYear(models.Model):
    """Model pentru anii electorali"""
    year = models.IntegerField(unique=True, verbose_name="Anul alegerilor")
    description = models.TextField(blank=True, null=True, verbose_name="Descriere generală despre alegeri")
    turnout_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                         verbose_name="Prezența la vot (%)")
    total_voters = models.IntegerField(null=True, blank=True, verbose_name="Număr total de alegători")
    
    class Meta:
        verbose_name = "An electoral"
        verbose_name_plural = "Ani electorali"
        ordering = ['-year']
    
    def __str__(self):
        return f"Alegeri {self.year}"

class MediaInfluence(models.Model):
    """Model pentru influența mass-media asupra alegerilor"""
    title = models.CharField(max_length=200, verbose_name="Titlu")
    description = models.TextField(verbose_name="Descriere")
    election_year = models.ForeignKey(ElectionYear, on_delete=models.CASCADE, related_name="media_influences",
                                   verbose_name="Anul electoral")
    media_type = models.CharField(max_length=50, choices=[
        ('traditional', 'Mass-media tradițională'),
        ('social', 'Social media'),
        ('online', 'Media online'),
        ('other', 'Altele')
    ], verbose_name="Tip de media")
    impact_level = models.IntegerField(default=2, choices=[
        (1, "Impact redus"),
        (2, "Impact mediu"),
        (3, "Impact major")
    ], verbose_name="Nivelul de impact")
    
    class Meta:
        verbose_name = "Influență media"
        verbose_name_plural = "Influențe media"
    
    def __str__(self):
        return f"{self.title} ({self.get_media_type_display()}, {self.election_year.year})"

class PresidentialCandidate(models.Model):
    """Model pentru candidații prezidențiali"""
    name = models.CharField(max_length=100, verbose_name="Nume complet")
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data nașterii")
    party = models.CharField(max_length=100, verbose_name="Partid/Alianță politică")
    photo_url = models.URLField(blank=True, null=True, verbose_name="URL fotografie")
    biography = models.TextField(verbose_name="Biografie")
    political_experience = models.TextField(blank=True, null=True, verbose_name="Experiență politică")
    education = models.TextField(blank=True, null=True, verbose_name="Educație")
    
    # Flag pentru candidații actuali (2025)
    is_current = models.BooleanField(default=False, verbose_name="Candidat actual (2025)")
    
    class Meta:
        verbose_name = "Candidat prezidențial"
        verbose_name_plural = "Candidați prezidențiali"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.party})"

class ElectionParticipation(models.Model):
    """Model pentru participarea unui candidat la alegeri"""
    candidate = models.ForeignKey(PresidentialCandidate, on_delete=models.CASCADE, related_name="participations",
                               verbose_name="Candidat")
    election_year = models.ForeignKey(ElectionYear, on_delete=models.CASCADE, related_name="participations",
                                   verbose_name="Anul alegerilor")
    votes_count = models.IntegerField(null=True, blank=True, verbose_name="Număr de voturi")
    votes_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                        verbose_name="Procent voturi (%)")
    position = models.IntegerField(null=True, blank=True, verbose_name="Poziția în clasament")
    round = models.IntegerField(default=1, choices=[
        (1, "Primul tur"),
        (2, "Al doilea tur")
    ], verbose_name="Turul electoral")
    campaign_slogan = models.CharField(max_length=255, blank=True, null=True, verbose_name="Slogan de campanie")
    notable_events = models.TextField(blank=True, null=True, verbose_name="Evenimente notabile din campanie")
    
    class Meta:
        verbose_name = "Participare electorală"
        verbose_name_plural = "Participări electorale"
        unique_together = ('candidate', 'election_year', 'round')
        ordering = ['election_year', 'round', 'position']
    
    def __str__(self):
        return f"{self.candidate.name} - Alegeri {self.election_year.year} (Turul {self.round})"

class Controversy(models.Model):
    """Model pentru controversele legate de candidați sau alegeri"""
    title = models.CharField(max_length=200, verbose_name="Titlu")
    description = models.TextField(verbose_name="Descriere")
    date = models.DateField(verbose_name="Data")
    candidate = models.ForeignKey(PresidentialCandidate, on_delete=models.CASCADE, 
                               related_name="controversies", null=True, blank=True,
                               verbose_name="Candidat implicat")
    election_year = models.ForeignKey(ElectionYear, on_delete=models.CASCADE, 
                                   related_name="controversies", null=True, blank=True,
                                   verbose_name="Anul electoral")
    impact = models.TextField(blank=True, null=True, verbose_name="Impactul asupra alegerilor")
    
    class Meta:
        verbose_name = "Controversă"
        verbose_name_plural = "Controverse"
        ordering = ['-date']
    
    def __str__(self):
        return self.title