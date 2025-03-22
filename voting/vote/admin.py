# vote/admin.py
from django.contrib import admin
from .models import VoteSettings
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
    list_display = ('vote_type', 'is_active', 'start_datetime', 'end_datetime', 'created_at')
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