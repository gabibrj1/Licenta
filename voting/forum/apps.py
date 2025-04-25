from django.apps import AppConfig

class ForumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forum'
    verbose_name = 'Forum'
    
    def ready(self):
        import forum.signals  # Importăm semnalele