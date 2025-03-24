from django.contrib import admin
from .models import VoteSettings, VotingSection, LocalCandidate, LocalVote
from django import forms
from django.core.exceptions import ValidationError  

class VoteSettingsForm(forms.ModelForm):
    class Meta:
        model = VoteSettings
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        # Metoda clean a modelului va fi apelată automat la salvare
        return cleaned_data

@admin.register(VoteSettings)
class VoteSettingsAdmin(admin.ModelAdmin):
    form = VoteSettingsForm
    list_display = ('vote_type', 'is_active', 'start_datetime', 'end_datetime', 'created_at', 'updated_at')
    list_filter = ('vote_type', 'is_active')
    search_fields = ('vote_type',)
    actions = ['activate_sessions', 'deactivate_sessions']
    
    def activate_sessions(self, request, queryset):
        for obj in queryset:
            obj.is_active = True
            try:
                obj.save()
            except ValidationError as e:
                self.message_user(request, f"Nu s-a putut activa sesiunea {obj}: {e}", level='ERROR')
                return
        self.message_user(request, f"{queryset.count()} sesiuni au fost activate cu succes.")
    activate_sessions.short_description = "Activează sesiunile selectate"
    
    def deactivate_sessions(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} sesiuni au fost dezactivate cu succes.")
    deactivate_sessions.short_description = "Dezactivează sesiunile selectate"

@admin.register(VotingSection)
class VotingSectionAdmin(admin.ModelAdmin):
    list_display = ('section_id', 'name', 'city', 'county')
    list_filter = ('county', 'city')
    search_fields = ('section_id', 'name', 'address', 'city', 'county')

@admin.register(LocalCandidate)
class LocalCandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'position', 'city', 'county')
    list_filter = ('position', 'party', 'county', 'city')
    search_fields = ('name', 'party', 'city', 'county')

@admin.register(LocalVote)
class LocalVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'candidate', 'voting_section', 'vote_datetime')
    list_filter = ('vote_datetime', 'candidate__position', 'voting_section__county')
    search_fields = ('user__email', 'user__cnp', 'candidate__name')
    
    def get_queryset(self, request):
        # Preîncărcăm relațiile pentru a evita query-uri multiple
        return super().get_queryset(request).select_related(
            'user', 'candidate', 'voting_section'
        )