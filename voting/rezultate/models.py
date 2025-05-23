from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime, date

User = get_user_model()

class VoteResult(models.Model):
    """Model pentru rezultatele voturilor - folosește candidații din vote app"""
    vote_type = models.CharField(max_length=25, choices=[
        ('prezidentiale', 'Alegeri Prezidențiale'),
        ('prezidentiale_tur2', 'Alegeri Prezidențiale Turul 2'),
        ('parlamentare', 'Alegeri Parlamentare'),
        ('locale', 'Alegeri Locale'),
    ])
    
    # Referencias către modelele din vote app
    presidential_candidate = models.ForeignKey(
        'vote.PresidentialCandidate', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    presidential_round2_candidate = models.ForeignKey(
        'vote.PresidentialRound2Candidate', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    parliamentary_party = models.ForeignKey(
        'vote.ParliamentaryParty', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    local_candidate = models.ForeignKey(
        'vote.LocalCandidate', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Informații despre vot
    vote_datetime = models.DateTimeField()
    location_type = models.CharField(max_length=15, choices=[
        ('romania', 'România'),
        ('strainatate', 'Străinătate'),
    ], default='romania')
    county = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Informații despre alegător (pentru verificări de integritate)
    voter_age_group = models.CharField(max_length=10, choices=[
        ('18-24', '18-24 ani'),
        ('25-34', '25-34 ani'),
        ('35-44', '35-44 ani'),
        ('45-64', '45-64 ani'),
        ('65+', '65+ ani'),
    ])
    voter_gender = models.CharField(max_length=1, choices=[
        ('M', 'Masculin'),
        ('F', 'Feminin'),
    ])
    
    # Metadate
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Rezultat Vot"
        verbose_name_plural = "Rezultate Vot"
        indexes = [
            models.Index(fields=['vote_type', 'location_type']),
            models.Index(fields=['vote_datetime']),
            models.Index(fields=['county', 'city']),
        ]
    
    @classmethod
    def create_from_statistics(cls, vote_stats, candidate_choice=None):
        """Creează rezultate pe baza statisticilor existente"""
        from statistici.models import VoteStatistics
        
        # Verifică dacă vote_stats este o instanță de VoteStatistics
        if not isinstance(vote_stats, VoteStatistics):
            return None
        
        vote_result = cls(
            vote_type=vote_stats.vote_type,
            vote_datetime=vote_stats.vote_datetime,
            location_type=vote_stats.location_type,
            county=vote_stats.county,
            city=vote_stats.city,
            voter_age_group=vote_stats.age_group,
            voter_gender=vote_stats.gender
        )
        
        # Atribuie candidatul/partidul pe baza tipului de vot
        if vote_stats.vote_type == 'prezidentiale':
            if candidate_choice:
                vote_result.presidential_candidate = candidate_choice
            else:
                # Alege candidat aleatoriu din tabelele vote
                from vote.models import PresidentialCandidate
                candidates = PresidentialCandidate.objects.filter(name__isnull=False)
                if candidates.exists():
                    import random
                    vote_result.presidential_candidate = random.choice(candidates)
        
        elif vote_stats.vote_type == 'prezidentiale_tur2':
            if candidate_choice:
                vote_result.presidential_round2_candidate = candidate_choice
            else:
                # Alege candidat aleatoriu din turul 2
                from vote.models import PresidentialRound2Candidate
                candidates = PresidentialRound2Candidate.objects.filter(name__isnull=False)
                if candidates.exists():
                    import random
                    vote_result.presidential_round2_candidate = random.choice(candidates)
        
        elif vote_stats.vote_type == 'parlamentare':
            if candidate_choice:
                vote_result.parliamentary_party = candidate_choice
            else:
                # Alege partid aleatoriu
                from vote.models import ParliamentaryParty
                parties = ParliamentaryParty.objects.filter(name__isnull=False)
                if parties.exists():
                    import random
                    vote_result.parliamentary_party = random.choice(parties)
        
        elif vote_stats.vote_type == 'locale':
            if candidate_choice:
                vote_result.local_candidate = candidate_choice
            else:
                # Alege candidat local aleatoriu pentru județul respectiv
                from vote.models import LocalCandidate
                candidates = LocalCandidate.objects.filter(
                    name__isnull=False,
                    county=vote_stats.county or 'București'
                )
                if candidates.exists():
                    import random
                    vote_result.local_candidate = random.choice(candidates)
        
        vote_result.save()
        return vote_result
    
    def get_candidate_name(self):
        """Returnează numele candidatului votat"""
        if self.presidential_candidate:
            return self.presidential_candidate.name
        elif self.presidential_round2_candidate:
            return self.presidential_round2_candidate.name
        elif self.parliamentary_party:
            return self.parliamentary_party.name
        elif self.local_candidate:
            return self.local_candidate.name
        return "Necunoscut"
    
    def get_candidate_party(self):
        """Returnează partidul candidatului votat"""
        if self.presidential_candidate:
            return self.presidential_candidate.party or 'Independent'
        elif self.presidential_round2_candidate:
            return self.presidential_round2_candidate.party or 'Independent'
        elif self.parliamentary_party:
            return self.parliamentary_party.abbreviation or self.parliamentary_party.name
        elif self.local_candidate:
            return self.local_candidate.party or 'Independent'
        return 'Necunoscut'
    
    def __str__(self):
        candidate_name = self.get_candidate_name()
        return f"{self.vote_type} - {candidate_name} ({self.vote_datetime.strftime('%d.%m.%Y %H:%M')})"