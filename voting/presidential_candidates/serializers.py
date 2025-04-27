from rest_framework import serializers
from .models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation,
    HistoricalEvent, MediaInfluence, Controversy
)

class HistoricalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalEvent
        fields = '__all__'

class MediaInfluenceSerializer(serializers.ModelSerializer):
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)
    impact_level_display = serializers.CharField(source='get_impact_level_display', read_only=True)
    
    class Meta:
        model = MediaInfluence
        fields = '__all__'

class ControversySerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    election_year_value = serializers.IntegerField(source='election_year.year', read_only=True)
    
    class Meta:
        model = Controversy
        fields = '__all__'

class ElectionParticipationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    candidate_party = serializers.CharField(source='candidate.party', read_only=True)
    year = serializers.IntegerField(source='election_year.year', read_only=True)
    round_display = serializers.CharField(source='get_round_display', read_only=True)
    
    class Meta:
        model = ElectionParticipation
        fields = '__all__'

class ElectionYearListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionYear
        fields = ['id', 'year', 'turnout_percentage', 'total_voters']

class ElectionYearDetailSerializer(serializers.ModelSerializer):
    participations = ElectionParticipationSerializer(many=True, read_only=True)
    media_influences = MediaInfluenceSerializer(many=True, read_only=True)
    controversies = ControversySerializer(many=True, read_only=True)
    
    class Meta:
        model = ElectionYear
        fields = '__all__'

class PresidentialCandidateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresidentialCandidate
        fields = ['id', 'name', 'party', 'photo_url', 'slug', 'is_current']

class PresidentialCandidateDetailSerializer(serializers.ModelSerializer):
    participations = ElectionParticipationSerializer(many=True, read_only=True)
    controversies = ControversySerializer(many=True, read_only=True)
    
    class Meta:
        model = PresidentialCandidate
        fields = '__all__'