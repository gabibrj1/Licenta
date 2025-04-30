from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import (
    ElectionCycle, LocalElectionType, LocalPosition,
    LocalElectionRule, SignificantCandidate, ImportantEvent,
    LegislationChange
)
from .serializers import (
    ElectionCycleListSerializer, ElectionCycleDetailSerializer,
    LocalElectionTypeSerializer, LocalPositionSerializer,
    LocalElectionRuleSerializer, SignificantCandidateSerializer,
    ImportantEventSerializer, LegislationChangeSerializer
)

class ElectionCycleListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista tuturor ciclurilor electorale locale"""
        election_cycles = ElectionCycle.objects.all()
        serializer = ElectionCycleListSerializer(election_cycles, many=True)
        return Response(serializer.data)

class ElectionCycleDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, year):
        """Detalii despre un ciclu electoral local specific"""
        election_cycle = get_object_or_404(ElectionCycle, year=year)
        serializer = ElectionCycleDetailSerializer(election_cycle)
        return Response(serializer.data)

class LocalElectionTypeListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista tipurilor de alegeri locale"""
        election_types = LocalElectionType.objects.all()
        serializer = LocalElectionTypeSerializer(election_types, many=True)
        return Response(serializer.data)

class LocalPositionListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista funcțiilor publice locale"""
        # Filtrare opțională pe tipul de alegeri
        election_type_id = request.query_params.get('election_type')
        importance = request.query_params.get('importance')
        
        positions = LocalPosition.objects.all()
        
        if election_type_id:
            positions = positions.filter(election_type_id=election_type_id)
        
        if importance:
            positions = positions.filter(importance=importance)
            
        serializer = LocalPositionSerializer(positions, many=True)
        return Response(serializer.data)

class LocalElectionRuleListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista regulilor pentru alegerile locale"""
        # Filtrare opțională pe tipul de alegeri sau reguli curente
        election_type_id = request.query_params.get('election_type')
        current_only = request.query_params.get('current', '').lower() in ['true', '1', 'yes']
        
        rules = LocalElectionRule.objects.all()
        
        if election_type_id:
            rules = rules.filter(election_type_id=election_type_id)
        
        if current_only:
            rules = rules.filter(is_current=True)
            
        serializer = LocalElectionRuleSerializer(rules, many=True)
        return Response(serializer.data)

class SignificantCandidateListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista candidaților locali importanți"""
        # Filtrare opțională pe poziție, ciclu electoral sau locație
        position_id = request.query_params.get('position')
        election_cycle_id = request.query_params.get('election_cycle')
        location = request.query_params.get('location')
        
        candidates = SignificantCandidate.objects.all()
        
        if position_id:
            candidates = candidates.filter(position_id=position_id)
        
        if election_cycle_id:
            candidates = candidates.filter(election_cycle_id=election_cycle_id)
            
        if location:
            candidates = candidates.filter(location__icontains=location)
            
        serializer = SignificantCandidateSerializer(candidates, many=True)
        return Response(serializer.data)

class SignificantCandidateDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, slug=None, pk=None):
        """Detalii despre un candidat local important"""
        if slug:
            candidate = get_object_or_404(SignificantCandidate, slug=slug)
        else:
            candidate = get_object_or_404(SignificantCandidate, pk=pk)
            
        serializer = SignificantCandidateSerializer(candidate)
        return Response(serializer.data)

class ImportantEventListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista evenimentelor importante pentru alegerile locale"""
        # Filtrare opțională pe ciclu electoral sau importanță
        election_cycle_id = request.query_params.get('election_cycle')
        importance = request.query_params.get('importance')
        
        events = ImportantEvent.objects.all()
        
        if election_cycle_id:
            events = events.filter(election_cycle_id=election_cycle_id)
        
        if importance:
            events = events.filter(importance=importance)
            
        serializer = ImportantEventSerializer(events, many=True)
        return Response(serializer.data)

class LegislationChangeListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista modificărilor legislative relevante pentru alegerile locale"""
        # Filtrare opțională pe an
        year = request.query_params.get('year')
        
        changes = LegislationChange.objects.all()
        
        if year:
            changes = changes.filter(year=year)
            
        serializer = LegislationChangeSerializer(changes, many=True)
        return Response(serializer.data)