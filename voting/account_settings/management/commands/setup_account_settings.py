from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from account_settings.models import AccountSettings
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create account settings for all existing users'

    def handle(self, *args, **kwargs):
        self.stdout.write("Inițializare setări de cont pentru utilizatori existenți...")
        
        users = User.objects.filter(account_settings__isnull=True)
        count = 0
        
        for user in users:
            AccountSettings.objects.get_or_create(user=user)
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f"✅ Setări de cont create pentru {count} utilizatori!"))
        
        # Update existing settings with new fields that might have been added
        account_settings = AccountSettings.objects.all()
        self.stdout.write(f"Verificare {account_settings.count()} seturi de setări existente...")
        
        # This will force the save method to run, ensuring any default values for new fields are set
        for settings in account_settings:
            settings.save()
        
        self.stdout.write(self.style.SUCCESS("✅ Procesul de inițializare a setărilor de cont a fost finalizat!"))