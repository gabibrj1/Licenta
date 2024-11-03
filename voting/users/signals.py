from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=SocialAccount)
def activate_user_on_google_login(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        if instance.provider in ['google', 'facebook']:
            user.is_active = True
            user.save()
