from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation,
    HistoricalEvent, MediaInfluence, Controversy
)
from .serializers import (
    PresidentialCandidateListSerializer, PresidentialCandidateDetailSerializer,
    ElectionYearListSerializer, ElectionYearDetailSerializer,
    ElectionParticipationSerializer, HistoricalEventSerializer,
    MediaInfluenceSerializer, ControversySerializer
)

class PresidentialCandidateListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista tuturor candidaților prezidențiali"""
        # Opțional filtrare pentru candidații actuali
        current_only = request.query_params.get('current', '').lower() in ['true', '1', 'yes']
        
        if current_only:
            candidates = PresidentialCandidate.objects.filter(is_current=True)
        else:
            candidates = PresidentialCandidate.objects.all()
            
        serializer = PresidentialCandidateListSerializer(candidates, many=True)
        return Response(serializer.data)

class PresidentialCandidateDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, slug=None, pk=None):
        """Detalii despre un candidat prezidențial specific"""
        if slug:
            candidate = get_object_or_404(PresidentialCandidate, slug=slug)
        else:
            candidate = get_object_or_404(PresidentialCandidate, pk=pk)
            
        serializer = PresidentialCandidateDetailSerializer(candidate)
        return Response(serializer.data)

class ElectionYearListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista tuturor anilor electorali"""
        election_years = ElectionYear.objects.all()
        serializer = ElectionYearListSerializer(election_years, many=True)
        return Response(serializer.data)

class ElectionYearDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, year):
        """Detalii despre un an electoral specific"""
        election_year = get_object_or_404(ElectionYear, year=year)
        serializer = ElectionYearDetailSerializer(election_year)
        return Response(serializer.data)

class HistoricalEventListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista evenimentelor istorice legate de alegerile prezidențiale"""
        events = HistoricalEvent.objects.all()
        serializer = HistoricalEventSerializer(events, many=True)
        return Response(serializer.data)

class MediaInfluenceListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista influențelor media asupra alegerilor"""
        influences = MediaInfluence.objects.all()
        
        # Filtrare opțională pe tipul de media
        media_type = request.query_params.get('type')
        if media_type:
            influences = influences.filter(media_type=media_type)
            
        serializer = MediaInfluenceSerializer(influences, many=True)
        return Response(serializer.data)

class ControversyListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista controverselor legate de alegerile prezidențiale"""
        controversies = Controversy.objects.all()
        
        # Filtrare opțională pe candidat sau an electoral
        candidate_id = request.query_params.get('candidate_id')
        election_year = request.query_params.get('election_year')
        
        if candidate_id:
            controversies = controversies.filter(candidate_id=candidate_id)
        if election_year:
            controversies = controversies.filter(election_year__year=election_year)
            
        serializer = ControversySerializer(controversies, many=True)
        return Response(serializer.data)