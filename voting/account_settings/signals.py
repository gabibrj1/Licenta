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
        print(f"Setări de cont create pentru utilizatorul {instance.id}")
    else:
        # Asigură-te că există setări pentru toți utilizatorii existenți
        if not hasattr(instance, 'account_settings'):
            try:
                AccountSettings.objects.get(user=instance)
            except AccountSettings.DoesNotExist:
                AccountSettings.objects.create(user=instance)
                print(f"Setări de cont create retroactiv pentru utilizatorul {instance.id}")