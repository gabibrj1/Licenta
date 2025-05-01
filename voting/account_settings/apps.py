from django.apps import AppConfig


class AccountSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account_settings'
    
    def ready(self):
        """
        Initialize signals when the app is ready
        """
        import account_settings.signals