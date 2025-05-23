from django.contrib import admin
from .models import VoteSettings, VotingSection, LocalCandidate, LocalVote, PresidentialCandidate, PresidentialVote
from .models import ParliamentaryParty, ParliamentaryVote
from django import forms
from django.core.exceptions import ValidationError  
from .models import VoteSystem, VoteOption, VoteCast
from django.utils import timezone
from django.utils.html import format_html
from .models import PresidentialRound2Candidate, PresidentialRound2Vote
from django.contrib import messages

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
    actions = ['activate_sessions', 'deactivate_sessions', 'clear_vote_data']
    
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
    
    def clear_vote_data(self, request, queryset):
        """
        Acțiune admin pentru ștergerea manuală a datelor de vot pentru tipurile selectate
        """
        total_deleted = 0
        
        for vote_setting in queryset:
            vote_type = vote_setting.vote_type
            
            try:
                if vote_type == 'locale':
                    count = LocalVote.objects.all().count()
                    LocalVote.objects.all().delete()
                    total_deleted += count
                    
                elif vote_type == 'prezidentiale':
                    count = PresidentialVote.objects.all().count()
                    PresidentialVote.objects.all().delete()
                    total_deleted += count
                    
                elif vote_type == 'prezidentiale_tur2':
                    count = PresidentialRound2Vote.objects.all().count()
                    PresidentialRound2Vote.objects.all().delete()
                    total_deleted += count
                    
                elif vote_type == 'parlamentare':
                    count = ParliamentaryVote.objects.all().count()
                    ParliamentaryVote.objects.all().delete()
                    total_deleted += count
                    
                elif vote_type == 'simulare':
                    # Pentru simulare, șterge toate tipurile
                    local_count = LocalVote.objects.all().count()
                    presidential_count = PresidentialVote.objects.all().count()
                    presidential_r2_count = PresidentialRound2Vote.objects.all().count()
                    parliamentary_count = ParliamentaryVote.objects.all().count()
                    
                    LocalVote.objects.all().delete()
                    PresidentialVote.objects.all().delete()
                    PresidentialRound2Vote.objects.all().delete()
                    ParliamentaryVote.objects.all().delete()
                    
                    total_deleted += local_count + presidential_count + presidential_r2_count + parliamentary_count
                    
            except Exception as e:
                self.message_user(
                    request, 
                    f"Eroare la ștergerea datelor pentru {vote_type}: {str(e)}", 
                    level=messages.ERROR
                )
                
        if total_deleted > 0:
            self.message_user(
                request, 
                f"Au fost șterse {total_deleted} voturi în total.", 
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                "Nu au fost găsite voturi de șters.", 
                level=messages.INFO
            )
    
    clear_vote_data.short_description = "Șterge datele de vot pentru tipurile selectate"
    
    def delete_model(self, request, obj):
        """
        Suprascrie metoda de ștergere pentru a afișa un mesaj de confirmare
        """
        vote_type = obj.vote_type
        
        # Calculează câte voturi vor fi șterse
        vote_counts = {}
        if vote_type == 'locale':
            vote_counts['locale'] = LocalVote.objects.all().count()
        elif vote_type == 'prezidentiale':
            vote_counts['prezidentiale'] = PresidentialVote.objects.all().count()
        elif vote_type == 'prezidentiale_tur2':
            vote_counts['prezidentiale_tur2'] = PresidentialRound2Vote.objects.all().count()
        elif vote_type == 'parlamentare':
            vote_counts['parlamentare'] = ParliamentaryVote.objects.all().count()
        elif vote_type == 'simulare':
            vote_counts['locale'] = LocalVote.objects.all().count()
            vote_counts['prezidentiale'] = PresidentialVote.objects.all().count()
            vote_counts['prezidentiale_tur2'] = PresidentialRound2Vote.objects.all().count()
            vote_counts['parlamentare'] = ParliamentaryVote.objects.all().count()
        
        total_votes = sum(vote_counts.values())
        
        # Execută ștergerea
        super().delete_model(request, obj)
        
        # Afișează mesajul de confirmare
        if total_votes > 0:
            messages.success(
                request, 
                f"Configurația '{vote_type}' a fost ștearsă și {total_votes} voturi asociate au fost eliminate automat."
            )
        else:
            messages.success(
                request, 
                f"Configurația '{vote_type}' a fost ștearsă (nu existau voturi asociate)."
            )
    
    def delete_queryset(self, request, queryset):
        """
        Suprascrie metoda de ștergere în masă
        """
        total_votes_deleted = 0
        vote_types = []
        
        for obj in queryset:
            vote_types.append(obj.vote_type)
            
            # Calculează voturile care vor fi șterse
            if obj.vote_type == 'locale':
                total_votes_deleted += LocalVote.objects.all().count()
            elif obj.vote_type == 'prezidentiale':
                total_votes_deleted += PresidentialVote.objects.all().count()
            elif obj.vote_type == 'prezidentiale_tur2':
                total_votes_deleted += PresidentialRound2Vote.objects.all().count()
            elif obj.vote_type == 'parlamentare':
                total_votes_deleted += ParliamentaryVote.objects.all().count()
            elif obj.vote_type == 'simulare':
                total_votes_deleted += (LocalVote.objects.all().count() + 
                                      PresidentialVote.objects.all().count() + 
                                      PresidentialRound2Vote.objects.all().count() + 
                                      ParliamentaryVote.objects.all().count())
        
        # Execută ștergerea
        super().delete_queryset(request, queryset)
        
        # Afișează mesajul de confirmare
        messages.success(
            request, 
            f"Au fost șterse {len(vote_types)} configurații de vot ({', '.join(set(vote_types))}) "
            f"și {total_votes_deleted} voturi asociate au fost eliminate automat."
        )

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

@admin.register(PresidentialCandidate)
class PresidentialCandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'order_nr')  # Modificat din 'order' în 'order_nr'
    search_fields = ('name', 'party')
    list_filter = ('party',)
    ordering = ('order_nr', 'name')  # Modificat din 'order' în 'order_nr'

@admin.register(PresidentialVote)
class PresidentialVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'candidate', 'vote_datetime', 'vote_reference')
    search_fields = ('user__email', 'user__cnp', 'user__first_name', 'user__last_name', 'candidate__name', 'vote_reference')
    list_filter = ('vote_datetime', 'candidate')
    readonly_fields = ('user', 'candidate', 'vote_datetime', 'vote_reference')
    date_hierarchy = 'vote_datetime'
    
    def get_queryset(self, request):
        # Preîncărcăm relațiile pentru a evita query-uri multiple
        return super().get_queryset(request).select_related(
            'user', 'candidate'
        )
    
@admin.register(ParliamentaryParty)
class ParliamentaryPartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'order_nr')
    search_fields = ('name', 'abbreviation')
    list_filter = ('abbreviation',)
    ordering = ('order_nr', 'name')

@admin.register(ParliamentaryVote)
class ParliamentaryVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'party', 'vote_datetime', 'vote_reference')
    search_fields = ('user__email', 'user__cnp', 'user__first_name', 'user__last_name', 'party__name', 'vote_reference')
    list_filter = ('vote_datetime', 'party')
    readonly_fields = ('user', 'party', 'vote_datetime', 'vote_reference')
    date_hierarchy = 'vote_datetime'
    
    def get_queryset(self, request):
        # Preîncărcăm relațiile pentru a evita query-uri multiple
        return super().get_queryset(request).select_related(
            'user', 'party'
        )
    
# Verificare manuala a sistemului de vot de catre admin

class VoteOptionInline(admin.TabularInline):
    model = VoteOption
    extra = 0

@admin.register(VoteSystem)
class VoteSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'created_at', 'status', 'admin_verified_display')
    list_filter = ('status', 'admin_verified', 'category')
    search_fields = ('name', 'description', 'creator__email')
    readonly_fields = ('created_at',)
    inlines = [VoteOptionInline]
    actions = ['approve_vote_systems', 'reject_vote_systems']
    
    def admin_verified_display(self, obj):
        # Make sure to return a boolean value, not HTML
        return obj.admin_verified
    admin_verified_display.short_description = 'Admin Verified'
    admin_verified_display.boolean = True
    
    def approve_vote_systems(self, request, queryset):
        for system in queryset:
            system.admin_verified = True
            system.status = 'active' if timezone.now() >= system.start_date else 'pending'
            system.verification_date = timezone.now()
            system.save()
        
        self.message_user(request, f'{queryset.count()} sisteme de vot au fost aprobate.')
    approve_vote_systems.short_description = "Aprobă sistemele de vot selectate"
    
    def reject_vote_systems(self, request, queryset):
        for system in queryset:
            system.status = 'rejected'
            system.verification_date = timezone.now()
            system.save()
        
        self.message_user(request, f'{queryset.count()} sisteme de vot au fost respinse.')
    reject_vote_systems.short_description = "Respinge sistemele de vot selectate"


@admin.register(PresidentialRound2Candidate)
class PresidentialRound2CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'order_nr', 'round1_votes', 'round1_percentage')
    search_fields = ('name', 'party')
    list_filter = ('party',)
    ordering = ('order_nr', 'name')
    
    fieldsets = (
        ('Informații Candidate', {
            'fields': ('name', 'party', 'photo_url', 'description', 'order_nr', 'gender')
        }),
        ('Rezultate Turul 1', {
            'fields': ('round1_votes', 'round1_percentage'),
            'description': 'Rezultatele candidatului din turul 1 (pentru context)'
        }),
    )

@admin.register(PresidentialRound2Vote)
class PresidentialRound2VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'candidate', 'vote_datetime', 'vote_reference')
    search_fields = ('user__email', 'user__cnp', 'user__first_name', 'user__last_name', 'candidate__name', 'vote_reference')
    list_filter = ('vote_datetime', 'candidate')
    readonly_fields = ('user', 'candidate', 'vote_datetime', 'vote_reference')
    date_hierarchy = 'vote_datetime'
    
    def get_queryset(self, request):
        # Preîncărcăm relațiile pentru a evita query-uri multiple
        return super().get_queryset(request).select_related(
            'user', 'candidate'
        )