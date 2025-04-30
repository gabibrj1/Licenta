from rest_framework import serializers
from .models import (
    ElectionCycle, LocalElectionType, LocalPosition,
    LocalElectionRule, SignificantCandidate, ImportantEvent,
    LegislationChange
)

class LocalElectionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalElectionType
        fields = '__all__'

class LocalPositionSerializer(serializers.ModelSerializer):
    election_type_name = serializers.CharField(source='election_type.name', read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    
    class Meta:
        model = LocalPosition
        fields = '__all__'

class LocalElectionRuleSerializer(serializers.ModelSerializer):
    election_type_name = serializers.CharField(source='election_type.name', read_only=True)
    
    class Meta:
        model = LocalElectionRule
        fields = '__all__'

class SignificantCandidateSerializer(serializers.ModelSerializer):
    position_name = serializers.CharField(source='position.name', read_only=True)
    election_year = serializers.IntegerField(source='election_cycle.year', read_only=True)
    
    class Meta:
        model = SignificantCandidate
        fields = '__all__'

class ImportantEventSerializer(serializers.ModelSerializer):
    election_year = serializers.IntegerField(source='election_cycle.year', read_only=True, required=False)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    
    class Meta:
        model = ImportantEvent
        fields = '__all__'

class LegislationChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegislationChange
        fields = '__all__'

class ElectionCycleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionCycle
        fields = ['id', 'year', 'turnout_percentage', 'total_voters']

class ElectionCycleDetailSerializer(serializers.ModelSerializer):
    candidates = SignificantCandidateSerializer(many=True, read_only=True)
    events = ImportantEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = ElectionCycle
        fields = '__all__'