from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

#obtine modelul de utilizator definit in aplicatie
User = get_user_model()

@receiver(post_save, sender=SocialAccount) #receiver - asculta semnalul post_save emis dupa salvarea unui obiect SocialAccount
def activate_user_on_google_login(sender, instance, created, **kwargs): # exec functia daca obiectul SocialAccount a fost creat pt prima data
    if created:
        user = instance.user
        if instance.provider in ['google', 'facebook']:
            user.is_active = True
            user.save()
