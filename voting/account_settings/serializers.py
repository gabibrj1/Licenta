from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ProfileImage, AccountSettings

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for User model with minimal fields for profile display"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'cnp', 'series', 'number',
                  'place_of_birth', 'address', 'is_verified_by_id', 'is_active']
        read_only_fields = ['id', 'cnp', 'is_verified_by_id', 'is_active']

class ProfileImageSerializer(serializers.ModelSerializer):
    """Serializer for profile images"""
    image_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ProfileImage
        fields = ['id', 'image', 'image_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class AccountSettingsSerializer(serializers.ModelSerializer):
    """Serializer for account settings"""
    class Meta:
        model = AccountSettings
        fields = [
            'id', 'email_notifications', 'vote_reminders', 'security_alerts',
            'show_name_in_forums', 'show_activity_history', 
            'high_contrast', 'large_font', 'language', 'two_factor_enabled',
            'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']

class CompleteUserProfileSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for user profile including settings and image"""
    profile_image = ProfileImageSerializer(read_only=True)
    account_settings = AccountSettingsSerializer(read_only=True)
    auth_method = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'cnp', 'series', 'number',
            'place_of_birth', 'address', 'is_verified_by_id', 'is_active',
            'profile_image', 'account_settings', 'auth_method'
        ]
    
    def get_auth_method(self, obj):
        """Determine authentication method based on user data"""
        if obj.cnp and obj.is_verified_by_id:
            return 'id_card'
        return 'email'

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)
    
    def validate(self, data):
        """Check that new password and confirm password match"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Parolele nu se potrivesc"})
        return data