from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import AccountSettings

User = get_user_model()

@receiver(post_save, sender=User)
def create_account_settings(sender, instance, created, **kwargs):
    """
    Create account settings for new users
    """
    if created:
        AccountSettings.objects.create(user=instance)