from django.contrib import admin
from .models import (
    PresidentialCandidate, ElectionYear, ElectionParticipation,
    HistoricalEvent, MediaInfluence, Controversy
)

@admin.register(PresidentialCandidate)
class PresidentialCandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'is_current')
    search_fields = ('name', 'party')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_current', 'party')

@admin.register(ElectionYear)
class ElectionYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'turnout_percentage')
    search_fields = ('year',)

@admin.register(ElectionParticipation)
class ElectionParticipationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'election_year', 'round', 'votes_percentage', 'position')
    search_fields = ('candidate__name', 'election_year__year')
    list_filter = ('election_year', 'round')

@admin.register(HistoricalEvent)
class HistoricalEventAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'importance')
    search_fields = ('year', 'title')
    list_filter = ('importance',)

@admin.register(MediaInfluence)
class MediaInfluenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'election_year', 'media_type', 'impact_level')
    search_fields = ('title',)
    list_filter = ('media_type', 'impact_level', 'election_year')

@admin.register(Controversy)
class ControversyAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'candidate', 'election_year')
    search_fields = ('title', 'candidate__name')
    list_filter = ('date', 'election_year')