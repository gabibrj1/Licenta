import os
import logging
from threading import Lock
from django.conf import settings

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Singleton pentru managementul modelelor AI
    Încarcă modelele o singură dată și le reutilizează
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._models = {}
        self._model_paths = {
            'yolo_antispoofing': os.path.join(settings.MEDIA_ROOT, 'models', 'l_version_1_300.pt'),
            'yolo_id_card': os.path.join(settings.MEDIA_ROOT, 'models', 'best.pt'),
        }
        
        logger.info("ModelManager initialized")
    
    def get_model(self, model_name):
        """
        Returnează modelul cerut, încărcându-l dacă este necesar
        """
        if model_name not in self._models:
            self._load_model(model_name)
        return self._models.get(model_name)
    
    def _load_model(self, model_name):
        """
        Încarcă un model specific
        """
        try:
            if model_name not in self._model_paths:
                raise ValueError(f"Model necunoscut: {model_name}")
            
            model_path = self._model_paths[model_name]
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelul nu există la calea: {model_path}")
            
            logger.info(f"Încărcare model {model_name} de la {model_path}")
            
            # Import lazy pentru a evita import-urile la nivel de modul
            from ultralytics import YOLO
            
            model = YOLO(model_path)
            self._models[model_name] = model
            
            logger.info(f"Modelul {model_name} a fost încărcat cu succes!")
            
        except Exception as e:
            logger.error(f"Eroare la încărcarea modelului {model_name}: {e}")
            self._models[model_name] = None
            raise
    
    def is_model_loaded(self, model_name):
        """
        Verifică dacă un model este deja încărcat
        """
        return model_name in self._models and self._models[model_name] is not None
    
    def unload_model(self, model_name):
        """
        Descarcă un model din memorie
        """
        if model_name in self._models:
            del self._models[model_name]
            logger.info(f"Modelul {model_name} a fost descărcat din memorie")
    
    def unload_all_models(self):
        """
        Descarcă toate modelele din memorie
        """
        self._models.clear()
        logger.info("Toate modelele au fost descărcate din memorie")
    
    def get_memory_usage(self):
        """
        Returnează informații despre modelele încărcate
        """
        return {
            'loaded_models': list(self._models.keys()),
            'model_count': len(self._models)
        }

# Instanță globală
model_manager = ModelManager()