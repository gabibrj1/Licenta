from django.contrib import admin
from .models import (
    ElectionCycle, LocalElectionType, LocalPosition,
    LocalElectionRule, SignificantCandidate, ImportantEvent,
    LegislationChange
)

@admin.register(ElectionCycle)
class ElectionCycleAdmin(admin.ModelAdmin):
    list_display = ('year', 'turnout_percentage', 'total_voters')
    search_fields = ('year', 'description')
    list_filter = ('year',)

@admin.register(LocalElectionType)
class LocalElectionTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(LocalPosition)
class LocalPositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'election_type', 'importance')
    list_filter = ('election_type', 'importance')
    search_fields = ('name', 'description')

@admin.register(LocalElectionRule)
class LocalElectionRuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'election_type', 'since_year', 'is_current')
    list_filter = ('election_type', 'since_year', 'is_current')
    search_fields = ('title', 'description')

@admin.register(SignificantCandidate)
class SignificantCandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'location', 'election_cycle', 'party')
    list_filter = ('position', 'election_cycle', 'location')
    search_fields = ('name', 'location', 'party', 'achievement')
    prepopulated_fields = {'slug': ('name', 'location')}

@admin.register(ImportantEvent)
class ImportantEventAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'election_cycle', 'importance')
    list_filter = ('year', 'election_cycle', 'importance')
    search_fields = ('title', 'description')

@admin.register(LegislationChange)
class LegislationChangeAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'law_number')
    list_filter = ('year',)
    search_fields = ('title', 'description', 'law_number')