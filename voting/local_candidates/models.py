from django.db import models
from django.utils.text import slugify

class ElectionCycle(models.Model):
    """Model pentru ciclurile electorale locale"""
    year = models.IntegerField(unique=True, verbose_name="Anul alegerilor locale")
    description = models.TextField(blank=True, null=True, verbose_name="Descriere generală despre alegerile locale")
    turnout_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                         verbose_name="Prezența la vot (%)")
    total_voters = models.IntegerField(null=True, blank=True, verbose_name="Număr total de alegători")
    
    class Meta:
        verbose_name = "Ciclu electoral local"
        verbose_name_plural = "Cicluri electorale locale"
        ordering = ['-year']
    
    def __str__(self):
        return f"Alegeri locale {self.year}"

class LocalElectionType(models.Model):
    """Model pentru tipurile de alegeri locale"""
    name = models.CharField(max_length=100, verbose_name="Denumire")
    description = models.TextField(verbose_name="Descriere")
    
    class Meta:
        verbose_name = "Tip alegeri locale"
        verbose_name_plural = "Tipuri alegeri locale"
    
    def __str__(self):
        return self.name

class LocalPosition(models.Model):
    """Model pentru funcțiile publice locale"""
    name = models.CharField(max_length=100, verbose_name="Denumire funcție")
    description = models.TextField(verbose_name="Descriere responsabilități")
    election_type = models.ForeignKey(LocalElectionType, on_delete=models.CASCADE, related_name="positions",
                                   verbose_name="Tip alegeri")
    importance = models.IntegerField(default=2, choices=[
        (1, "Importanță redusă"),
        (2, "Importanță medie"),
        (3, "Importanță majoră")
    ], verbose_name="Nivel importanță")
    
    class Meta:
        verbose_name = "Funcție publică locală"
        verbose_name_plural = "Funcții publice locale"
    
    def __str__(self):
        return f"{self.name} ({self.get_importance_display()})"

class LocalElectionRule(models.Model):
    """Model pentru regulile alegerilor locale"""
    title = models.CharField(max_length=200, verbose_name="Titlu regulă")
    description = models.TextField(verbose_name="Descriere regulă")
    election_type = models.ForeignKey(LocalElectionType, on_delete=models.CASCADE, related_name="rules",
                                  verbose_name="Tip alegeri")
    since_year = models.IntegerField(verbose_name="Aplicabilă din anul")
    is_current = models.BooleanField(default=True, verbose_name="Regulă curentă")
    
    class Meta:
        verbose_name = "Regulă alegeri locale"
        verbose_name_plural = "Reguli alegeri locale"
    
    def __str__(self):
        return f"{self.title} (din {self.since_year})"

class SignificantCandidate(models.Model):
    """Model pentru candidați locali importanți istoric"""
    name = models.CharField(max_length=100, verbose_name="Nume complet")
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    position = models.ForeignKey(LocalPosition, on_delete=models.CASCADE, related_name="candidates",
                             verbose_name="Funcție")
    location = models.CharField(max_length=100, verbose_name="Localitate/Județ")
    election_cycle = models.ForeignKey(ElectionCycle, on_delete=models.CASCADE, related_name="candidates",
                                    verbose_name="Ciclu electoral")
    party = models.CharField(max_length=100, verbose_name="Partid/Alianță politică")
    photo_url = models.URLField(blank=True, null=True, verbose_name="URL fotografie")
    achievement = models.TextField(verbose_name="Realizare notabilă")
    
    class Meta:
        verbose_name = "Candidat local notabil"
        verbose_name_plural = "Candidați locali notabili"
        ordering = ['-election_cycle__year', 'position', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.location}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.position} ({self.location}, {self.election_cycle.year})"

class ImportantEvent(models.Model):
    """Model pentru evenimente importante în alegeri locale"""
    year = models.IntegerField(verbose_name="Anul evenimentului")
    title = models.CharField(max_length=200, verbose_name="Titlul evenimentului")
    description = models.TextField(verbose_name="Descrierea evenimentului")
    election_cycle = models.ForeignKey(ElectionCycle, on_delete=models.CASCADE, related_name="events",
                                   null=True, blank=True, verbose_name="Ciclu electoral")
    importance = models.IntegerField(default=1, choices=[
        (1, "Normal"),
        (2, "Important"),
        (3, "Foarte important")
    ], verbose_name="Importanța evenimentului")
    
    class Meta:
        verbose_name = "Eveniment important"
        verbose_name_plural = "Evenimente importante"
        ordering = ['-year', 'title']
    
    def __str__(self):
        return f"{self.year} - {self.title}"

class LegislationChange(models.Model):
    """Model pentru modificări legislative relevante pentru alegerile locale"""
    title = models.CharField(max_length=200, verbose_name="Titlu")
    description = models.TextField(verbose_name="Descriere")
    year = models.IntegerField(verbose_name="Anul modificării")
    law_number = models.CharField(max_length=50, verbose_name="Număr lege/ordonanță", blank=True, null=True)
    impact = models.TextField(verbose_name="Impactul asupra alegerilor locale")
    
    class Meta:
        verbose_name = "Modificare legislativă"
        verbose_name_plural = "Modificări legislative"
        ordering = ['-year']
    
    def __str__(self):
        return f"{self.year} - {self.title}"