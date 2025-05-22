from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime, date
import re

User = get_user_model()

class VoteStatistics(models.Model):
    """Model pentru stocarea statisticilor de vot"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=25, choices=[
        ('prezidentiale', 'Alegeri Prezidențiale'),
        ('prezidentiale_tur2', 'Alegeri Prezidențiale Turul 2'),
        ('parlamentare', 'Alegeri Parlamentare'),
        ('locale', 'Alegeri Locale'),
    ])
    vote_datetime = models.DateTimeField()
    
    # Date calculate din CNP
    age_group = models.CharField(max_length=10, choices=[
        ('18-24', '18-24 ani'),
        ('25-34', '25-34 ani'),
        ('35-44', '35-44 ani'),
        ('45-64', '45-64 ani'),
        ('65+', '65+ ani'),
    ])
    gender = models.CharField(max_length=1, choices=[
        ('M', 'Masculin'),
        ('F', 'Feminin'),
    ])
    birth_year = models.IntegerField()
    age_at_vote = models.IntegerField()
    
    # Date calculate din adresă sau alte surse
    environment = models.CharField(max_length=10, choices=[
        ('urban', 'Urban'),
        ('rural', 'Rural'),
    ], null=True, blank=True)
    
    # Locația votului
    location_type = models.CharField(max_length=15, choices=[
        ('romania', 'România'),
        ('strainatate', 'Străinătate'),
    ], default='romania')
    
    county = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadate
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Statistică Vot"
        verbose_name_plural = "Statistici Vot"
        unique_together = ('user', 'vote_type')
    
    @staticmethod
    def calculate_age_from_cnp(cnp):
        """Calculează vârsta din CNP"""
        if not cnp or len(cnp) != 13:
            return None, None, None
            
        try:
            # Prima cifră determină secolul și genul
            first_digit = int(cnp[0])
            
            # Determinarea secolului
            if first_digit in [1, 2]:
                century = 1900
            elif first_digit in [3, 4]:
                century = 2000
            elif first_digit in [5, 6]:
                century = 1800
            else:
                return None, None, None  # Străini sau alte cazuri
            
            # Determinarea genului
            gender = 'M' if first_digit % 2 == 1 else 'F'
            
            # Extragerea datei de naștere
            year = century + int(cnp[1:3])
            month = int(cnp[3:5])
            day = int(cnp[5:7])
            
            # Verificarea validității datei
            birth_date = date(year, month, day)
            
            # Calcularea vârstei
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            return age, gender, year
            
        except (ValueError, TypeError):
            return None, None, None
    
    @staticmethod
    def calculate_age_group(age):
        """Calculează grupa de vârstă"""
        if age is None:
            return None
        elif 18 <= age <= 24:
            return '18-24'
        elif 25 <= age <= 34:
            return '25-34'
        elif 35 <= age <= 44:
            return '35-44'
        elif 45 <= age <= 64:
            return '45-64'
        elif age >= 65:
            return '65+'
        else:
            return None
    
    @staticmethod
    def determine_environment_from_address(address):
        """Determină mediul (urban/rural) din adresă"""
        if not address:
            return None
            
        address_lower = address.lower()
        
        # Cuvinte cheie pentru urban
        urban_keywords = ['municipiu', 'oraș', 'oras', 'municipiul', 'orasul', 'sector', 'sectorul']
        # Cuvinte cheie pentru rural
        rural_keywords = ['comună', 'comuna', 'sat', 'satul', 'cătun', 'catun', 'cătunul', 'catunul']
        
        # Verifică cuvintele cheie urbane
        for keyword in urban_keywords:
            if keyword in address_lower:
                return 'urban'
        
        # Verifică cuvintele cheie rurale
        for keyword in rural_keywords:
            if keyword in address_lower:
                return 'rural'
        
        # Default: considerăm urban dacă nu găsim indicatori clari
        return 'urban'
    
    @classmethod
    def create_from_vote(cls, user, vote_type, vote_datetime, location_type='romania', county=None, city=None):
        """Creează o statistică din datele de vot"""
        # Calculează datele din CNP
        age, gender, birth_year = cls.calculate_age_from_cnp(user.cnp)
        
        if age is None or gender is None:
            return None
        
        age_group = cls.calculate_age_group(age)
        if not age_group:
            return None
        
        # Determină mediul din adresă (dacă este disponibilă)
        environment = None
        if hasattr(user, 'address') and user.address:
            environment = cls.determine_environment_from_address(user.address)
        
        # Creează statistica
        stat, created = cls.objects.get_or_create(
            user=user,
            vote_type=vote_type,
            defaults={
                'vote_datetime': vote_datetime,
                'age_group': age_group,
                'gender': gender,
                'birth_year': birth_year,
                'age_at_vote': age,
                'environment': environment,
                'location_type': location_type,
                'county': county,
                'city': city,
            }
        )
        
        return stat

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.vote_type} - {self.age_group} {self.gender}"