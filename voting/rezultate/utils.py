import random
from datetime import datetime, date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import VoteResult
from vote.models import PresidentialCandidate, PresidentialRound2Candidate, ParliamentaryParty, LocalCandidate
from statistici.models import VoteStatistics

User = get_user_model()

class ResultsPopulator:
    """Utility pentru popularea rezultatelor folosind candidații existenți din vote app"""
    
    @classmethod
    def populate_results_from_statistics(cls, vote_type='prezidentiale', location_type='romania'):
        """Populează rezultatele pe baza statisticilor existente folosind candidații din vote app"""
        
        # Obține statisticile existente pentru tipul de vot specificat
        statistics = VoteStatistics.objects.filter(
            vote_type=vote_type,
            location_type=location_type
        )
        
        if not statistics.exists():
            return []
        
        created_results = []
        
        # Obține candidații/partidele disponibile din vote app
        if vote_type == 'prezidentiale':
            candidates = list(PresidentialCandidate.objects.filter(name__isnull=False))
            vote_probabilities = cls.get_presidential_vote_probabilities(len(candidates))
            
        elif vote_type == 'prezidentiale_tur2':
            candidates = list(PresidentialRound2Candidate.objects.filter(name__isnull=False))
            vote_probabilities = cls.get_presidential_round2_vote_probabilities(len(candidates))
            
        elif vote_type == 'parlamentare':
            candidates = list(ParliamentaryParty.objects.filter(name__isnull=False))
            vote_probabilities = cls.get_parliamentary_vote_probabilities(len(candidates))
            
        elif vote_type == 'locale':
            # Pentru locale, grupăm pe județe
            counties = statistics.values_list('county', flat=True).distinct()
            county_candidates = {}
            for county in counties:
                if county:
                    county_candidates[county] = list(
                        LocalCandidate.objects.filter(
                            name__isnull=False,
                            county=county
                        )
                    )
            vote_probabilities = cls.get_local_vote_probabilities()
        
        # Verifică dacă avem candidați
        if vote_type != 'locale' and not candidates:
            print(f"Nu s-au găsit candidați pentru {vote_type} în vote app!")
            return []
        
        # Creează rezultatele pe baza statisticilor
        for stat in statistics:
            # Alege candidatul pe baza probabilităților
            if vote_type in ['prezidentiale', 'prezidentiale_tur2', 'parlamentare']:
                chosen_candidate = cls.choose_candidate_by_probability(candidates, vote_probabilities)
                result = VoteResult.create_from_statistics(stat, chosen_candidate)
                
            elif vote_type == 'locale':
                county = stat.county or 'București'
                if county in county_candidates and county_candidates[county]:
                    chosen_candidate = cls.choose_candidate_by_probability(
                        county_candidates[county], 
                        vote_probabilities
                    )
                    result = VoteResult.create_from_statistics(stat, chosen_candidate)
                else:
                    result = None
            
            if result:
                created_results.append(result)
        
        return created_results
    
    @classmethod
    def get_presidential_vote_probabilities(cls, num_candidates):
        """Returnează probabilitățile de vot pentru candidații prezidențiali"""
        # Probabilități realiste bazate pe sondaje
        base_probabilities = [0.24, 0.23, 0.19, 0.14, 0.08, 0.05, 0.03, 0.02, 0.01, 0.01]
        
        # Ajustează la numărul de candidați disponibili
        if num_candidates <= len(base_probabilities):
            return base_probabilities[:num_candidates]
        else:
            # Adaugă probabilități mici pentru candidații suplimentari
            extra_probs = [0.005] * (num_candidates - len(base_probabilities))
            return base_probabilities + extra_probs
    
    @classmethod
    def get_presidential_round2_vote_probabilities(cls, num_candidates):
        """Returnează probabilitățile de vot pentru turul 2 prezidențial"""
        # Pentru turul 2, de obicei sunt doar 2 candidați
        if num_candidates == 2:
            return [0.52, 0.48]  # Diferență mică între candidați
        elif num_candidates == 1:
            return [1.0]
        else:
            # Distribuție uniformă dacă sunt mai mulți
            prob = 1.0 / num_candidates
            return [prob] * num_candidates
    
    @classmethod
    def get_parliamentary_vote_probabilities(cls, num_parties):
        """Returnează probabilitățile de vot pentru partidele parlamentare"""
        base_probabilities = [0.30, 0.25, 0.20, 0.15, 0.05, 0.03, 0.01, 0.01]
        
        if num_parties <= len(base_probabilities):
            return base_probabilities[:num_parties]
        else:
            # Adaugă probabilități mici pentru partidele suplimentare
            extra_probs = [0.002] * (num_parties - len(base_probabilities))
            return base_probabilities + extra_probs
    
    @classmethod
    def get_local_vote_probabilities(cls):
        """Returnează probabilitățile de vot pentru candidații locali"""
        return [0.40, 0.30, 0.20, 0.07, 0.03]  # Pentru până la 5 candidați per județ
    
    @classmethod
    def choose_candidate_by_probability(cls, candidates, probabilities):
        """Alege un candidat pe baza probabilităților specificate"""
        if not candidates:
            return None
        
        # Ajustează probabilitățile la numărul de candidați disponibili
        num_candidates = len(candidates)
        adjusted_probabilities = probabilities[:num_candidates] if len(probabilities) >= num_candidates else probabilities
        
        # Completează cu probabilități mici dacă avem mai mulți candidați decât probabilități
        if len(adjusted_probabilities) < num_candidates:
            remaining_prob = max(0.001, (1.0 - sum(adjusted_probabilities)) / (num_candidates - len(adjusted_probabilities)))
            adjusted_probabilities.extend([remaining_prob] * (num_candidates - len(adjusted_probabilities)))
        
        # Normalizează probabilitățile să însumeze 1
        total_prob = sum(adjusted_probabilities)
        if total_prob > 0:
            adjusted_probabilities = [p / total_prob for p in adjusted_probabilities]
        else:
            # Distribuție uniformă dacă nu avem probabilități
            adjusted_probabilities = [1.0 / num_candidates] * num_candidates
        
        # Alege candidatul folosind probabilitățile
        rand_val = random.random()
        cumulative_prob = 0
        
        for i, prob in enumerate(adjusted_probabilities):
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return candidates[i]
        
        # Fallback la ultimul candidat
        return candidates[-1]
    
    @classmethod
    def clear_results(cls, vote_type=None, location_type=None):
        """Șterge rezultatele existente"""
        query = VoteResult.objects.all()
        
        if vote_type:
            query = query.filter(vote_type=vote_type)
        
        if location_type:
            query = query.filter(location_type=location_type)
        
        deleted_count = query.count()
        query.delete()
        
        return deleted_count
    
    @classmethod
    def get_available_candidates_info(cls):
        """Returnează informații despre candidații disponibili în vote app"""
        info = {
            'presidential_candidates': PresidentialCandidate.objects.count(),
            'presidential_round2_candidates': PresidentialRound2Candidate.objects.count(),
            'parliamentary_parties': ParliamentaryParty.objects.count(),
            'local_candidates': LocalCandidate.objects.count(),
        }
        
        # Afișează câțiva candidați pentru verificare
        info['sample_presidential'] = list(
            PresidentialCandidate.objects.values('name', 'party', 'order_nr')[:5]
        )
        info['sample_parliamentary'] = list(
            ParliamentaryParty.objects.values('name', 'abbreviation', 'order_nr')[:5]
        )
        info['sample_local'] = list(
            LocalCandidate.objects.values('name', 'party', 'county', 'position')[:5]
        )
        
        return info