from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class VotingPresence(models.Model):
    """Model pentru prezența la vot"""
    
    # Informații geografice
    county = models.CharField(max_length=50, verbose_name="Județ")
    uat = models.CharField(max_length=100, verbose_name="UAT", blank=True, null=True)
    locality = models.CharField(max_length=100, verbose_name="Localitate", blank=True, null=True)
    siruta = models.CharField(max_length=20, verbose_name="Cod SIRUTA", blank=True, null=True)
    
    # Informații secție de votare
    section_number = models.IntegerField(verbose_name="Numărul secției de votare", blank=True, null=True)
    section_name = models.CharField(max_length=200, verbose_name="Numele secției de votare", blank=True, null=True)
    environment = models.CharField(max_length=10, choices=[
        ('urban', 'Urban'),
        ('rural', 'Rural'),
    ], verbose_name="Mediu")
    
    # Tipul de vot și perioada
    vote_type = models.CharField(max_length=25, choices=[
        ('prezidentiale', 'Alegeri Prezidențiale'),
        ('prezidentiale_tur2', 'Alegeri Prezidențiale Turul 2'),
        ('parlamentare', 'Alegeri Parlamentare'),
        ('locale', 'Alegeri Locale'),
    ])
    
    vote_datetime = models.DateTimeField(verbose_name="Data și ora votului")
    location_type = models.CharField(max_length=15, choices=[
        ('romania', 'România'),
        ('strainatate', 'Străinătate'),
    ], default='romania')
    
    # Date despre înscriși și votanți
    registered_permanent = models.IntegerField(default=0, verbose_name="Înscriși pe liste permanente")
    voters_permanent = models.IntegerField(default=0, verbose_name="Votanți liste permanente")
    voters_supplementary = models.IntegerField(default=0, verbose_name="Votanți pe liste suplimentare")
    voters_mobile = models.IntegerField(default=0, verbose_name="Votanți cu urnă mobilă")
    
    # Date demografice pe grupe de vârstă
    men_18_24 = models.IntegerField(default=0, verbose_name="Bărbați 18-24 ani")
    men_25_34 = models.IntegerField(default=0, verbose_name="Bărbați 25-34 ani")
    men_35_44 = models.IntegerField(default=0, verbose_name="Bărbați 35-44 ani")
    men_45_64 = models.IntegerField(default=0, verbose_name="Bărbați 45-64 ani")
    men_65_plus = models.IntegerField(default=0, verbose_name="Bărbați 65+ ani")
    
    women_18_24 = models.IntegerField(default=0, verbose_name="Femei 18-24 ani")
    women_25_34 = models.IntegerField(default=0, verbose_name="Femei 25-34 ani")
    women_35_44 = models.IntegerField(default=0, verbose_name="Femei 35-44 ani")
    women_45_64 = models.IntegerField(default=0, verbose_name="Femei 45-64 ani")
    women_65_plus = models.IntegerField(default=0, verbose_name="Femei 65+ ani")
    
    # Date demografice detaliate pe vârstă (pentru analize avansate)
    demographic_data = models.JSONField(default=dict, verbose_name="Date demografice detaliate", blank=True)
    
    # Metadate
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Prezență la Vot"
        verbose_name_plural = "Prezență la Vot"
        indexes = [
            models.Index(fields=['vote_type', 'location_type']),
            models.Index(fields=['county', 'vote_datetime']),
            models.Index(fields=['vote_datetime']),
            models.Index(fields=['environment']),
        ]
    
    @property
    def total_voters(self):
        """Calculează total votanți"""
        return self.voters_permanent + self.voters_supplementary + self.voters_mobile
    
    @property
    def total_men(self):
        """Calculează total bărbați"""
        return self.men_18_24 + self.men_25_34 + self.men_35_44 + self.men_45_64 + self.men_65_plus
    
    @property
    def total_women(self):
        """Calculează total femei"""
        return self.women_18_24 + self.women_25_34 + self.women_35_44 + self.women_45_64 + self.women_65_plus
    
    @property
    def participation_rate(self):
        """Calculează rata de participare"""
        if self.registered_permanent > 0:
            return (self.total_voters / self.registered_permanent) * 100
        return 0
    
    def __str__(self):
        return f"Prezență {self.county} - {self.vote_type} ({self.vote_datetime.strftime('%d.%m.%Y')})"

class PresenceSummary(models.Model):
    """Model pentru sumarele de prezență pe județe/țări"""
    
    vote_type = models.CharField(max_length=25, choices=[
        ('prezidentiale', 'Alegeri Prezidențiale'),
        ('prezidentiale_tur2', 'Alegeri Prezidențiale Turul 2'),
        ('parlamentare', 'Alegeri Parlamentare'),
        ('locale', 'Alegeri Locale'),
    ])
    
    location_type = models.CharField(max_length=15, choices=[
        ('romania', 'România'),
        ('strainatate', 'Străinătate'),
    ])
    
    county = models.CharField(max_length=50, verbose_name="Județ/Țară")
    vote_datetime = models.DateTimeField(verbose_name="Data și ora")
    
    # Totale pe județ/țară
    total_registered = models.IntegerField(default=0, verbose_name="Total înscriși")
    total_voters = models.IntegerField(default=0, verbose_name="Total votanți")
    total_permanent = models.IntegerField(default=0, verbose_name="Total liste permanente")
    total_supplementary = models.IntegerField(default=0, verbose_name="Total liste suplimentare")
    total_mobile = models.IntegerField(default=0, verbose_name="Total urnă mobilă")
    
    # Mediu urban/rural
    urban_voters = models.IntegerField(default=0, verbose_name="Votanți urban")
    rural_voters = models.IntegerField(default=0, verbose_name="Votanți rural")
    
    # Demografie
    total_men = models.IntegerField(default=0, verbose_name="Total bărbați")
    total_women = models.IntegerField(default=0, verbose_name="Total femei")
    
    class Meta:
        verbose_name = "Sumar Prezență"
        verbose_name_plural = "Sumare Prezență"
        unique_together = ['vote_type', 'location_type', 'county', 'vote_datetime']
    
    @property
    def participation_rate(self):
        """Rata de participare"""
        if self.total_registered > 0:
            return (self.total_voters / self.total_registered) * 100
        return 0
    
    def __str__(self):
        return f"Sumar {self.county} - {self.vote_type} ({self.vote_datetime.strftime('%d.%m.%Y')})"