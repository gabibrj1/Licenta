from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import re

from .models import Post, Notification, Topic

@receiver(post_save, sender=Post)
def create_mention_notifications(sender, instance, created, **kwargs):
    """
    Când o postare este creată, verificăm dacă utilizatorul a menționat pe cineva
    și creăm notificări pentru cei menționați
    
    IMPORTANT: Modificat pentru a căuta după email în loc de username
    """
    if created:
        # Regex pentru a găsi mențiuni în format @email
        # Adaptează regex-ul pentru a căuta un format de email valid
        mentions = re.findall(r'@([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', instance.content)
        
        if mentions:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            for email in mentions:
                # Găsește utilizatorul și creează o notificare dacă există
                try:
                    mentioned_user = User.objects.get(email=email)
                    
                    # Nu creăm notificare pentru autor sau dacă există deja
                    if mentioned_user != instance.author and not Notification.objects.filter(
                            user=mentioned_user,
                            post=instance,
                            notification_type='mention'
                        ).exists():
                        
                        Notification.objects.create(
                            user=mentioned_user,
                            topic=instance.topic,
                            post=instance,
                            notification_type='mention'
                        )
                
                except User.DoesNotExist:
                    # Utilizatorul menționat nu există, ignorăm
                    pass

@receiver(pre_delete, sender=Topic)
def cleanup_topic_notifications(sender, instance, **kwargs):
    """
    Când un subiect este șters, ștergem toate notificările asociate
    """
    Notification.objects.filter(topic=instance).delete()

@receiver(pre_delete, sender=Post)
def cleanup_post_notifications(sender, instance, **kwargs):
    """
    Când o postare este ștearsă, ștergem toate notificările asociate
    """
    Notification.objects.filter(post=instance).delete()