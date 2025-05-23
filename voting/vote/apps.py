from django.apps import AppConfig

class VoteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vote'
    
    def ready(self):
        # Importă signal-urile pentru a fi sigur că sunt înregistrate
        try:
            import vote.models  # Acest import va înregistra signal-urile
        except ImportError:
            pass