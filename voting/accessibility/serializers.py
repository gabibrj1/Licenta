from rest_framework import serializers
from .models import AccessibilitySettings

class AccessibilitySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessibilitySettings
        fields = [
            'font_size', 'contrast_mode', 'animations', 'focus_highlights',
            'extended_time', 'simplified_interface', 'audio_assistance', 'keyboard_navigation',
            'extra_confirmations', 'large_buttons', 'screen_reader_support', 'audio_notifications'
        ]