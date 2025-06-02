from django.core.management.base import BaseCommand, CommandError
from core.model_manager import model_manager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Gestionează modelele AI (încărcare, descărcare, status)'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['load', 'unload', 'status', 'reload', 'preload_all'],
            help='Acțiunea de executat'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Numele modelului (pentru load/unload)'
        )

    def handle(self, *args, **options):
        action = options['action']
        model_name = options.get('model')

        try:
            if action == 'status':
                self.show_status()
            elif action == 'load':
                if not model_name:
                    raise CommandError('Specificați numele modelului cu --model')
                self.load_model(model_name)
            elif action == 'unload':
                if not model_name:
                    raise CommandError('Specificați numele modelului cu --model')
                self.unload_model(model_name)
            elif action == 'reload':
                if not model_name:
                    raise CommandError('Specificați numele modelului cu --model')
                self.reload_model(model_name)
            elif action == 'preload_all':
                self.preload_all_models()

        except Exception as e:
            raise CommandError(f'Eroare: {e}')

    def show_status(self):
        """Afișează statusul modelelor"""
        memory_info = model_manager.get_memory_usage()
        
        self.stdout.write(
            self.style.SUCCESS('=== STATUS MODELE AI ===')
        )
        
        if memory_info['loaded_models']:
            self.stdout.write(
                self.style.SUCCESS(f"Modele încărcate ({memory_info['model_count']}):")
            )
            for model in memory_info['loaded_models']:
                status = "✓ Încărcat" if model_manager.is_model_loaded(model) else "✗ Eroare"
                self.stdout.write(f"  - {model}: {status}")
        else:
            self.stdout.write(
                self.style.WARNING("Niciun model încărcat în memorie")
            )

    def load_model(self, model_name):
        """Încarcă un model specific"""
        self.stdout.write(f"Încărcare model: {model_name}...")
        
        try:
            model = model_manager.get_model(model_name)
            if model is not None:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Modelul {model_name} a fost încărcat cu succes")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Modelul {model_name} nu a putut fi încărcat")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Eroare la încărcarea modelului {model_name}: {e}")
            )

    def unload_model(self, model_name):
        """Descarcă un model din memorie"""
        self.stdout.write(f"Descărcare model: {model_name}...")
        
        try:
            model_manager.unload_model(model_name)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Modelul {model_name} a fost descărcat din memorie")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Eroare la descărcarea modelului {model_name}: {e}")
            )

    def reload_model(self, model_name):
        """Reîncarcă un model"""
        self.stdout.write(f"Reîncărcare model: {model_name}...")
        
        try:
            # Descarcă modelul
            model_manager.unload_model(model_name)
            
            # Încarcă din nou
            model = model_manager.get_model(model_name)
            if model is not None:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Modelul {model_name} a fost reîncărcat cu succes")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Modelul {model_name} nu a putut fi reîncărcat")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Eroare la reîncărcarea modelului {model_name}: {e}")
            )

    def preload_all_models(self):
        """Pre-încarcă toate modelele disponibile"""
        self.stdout.write("Pre-încărcare toate modelele disponibile...")
        
        available_models = ['yolo_antispoofing', 'yolo_id_card']
        
        for model_name in available_models:
            try:
                self.stdout.write(f"  Încărcare {model_name}...")
                model = model_manager.get_model(model_name)
                if model is not None:
                    self.stdout.write(
                        self.style.SUCCESS(f"    ✓ {model_name} încărcat")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"    ✗ {model_name} nu a putut fi încărcat")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"    ✗ {model_name} - Eroare: {e}")
                )
        
        # Afișează statusul final
        self.show_status()