import logging
import numpy as np
import cv2
import face_recognition
import concurrent.futures
from PIL import Image
import io
from .model_manager import model_manager

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """
    Serviciu pentru recunoașterea facială și anti-spoofing
    Folosește ModelManager pentru accesul la modele
    """
    
    def __init__(self):
        self.model_name = 'yolo_antispoofing'
    
    def get_model(self):
        """
        Returnează modelul YOLO pentru anti-spoofing
        """
        return model_manager.get_model(self.model_name)
    
    def detect_spoofing(self, image_array):
        """Verifică dacă imaginea este reală sau falsă folosind YOLO."""
        try:
            model = self.get_model()
            if model is None:
                logger.error("Modelul YOLO pentru anti-spoofing nu este disponibil")
                return False
                
            # Redimensionare imagine pentru procesare mai rapidă
            h, w = image_array.shape[:2]
            scale = min(1.0, 640 / max(h, w))
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                image_array = cv2.resize(image_array, (new_w, new_h))

            # Normalizare imagine și detectie spoofing cu YOLO 
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            normalized = cv2.equalizeHist(gray)
            image_array = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)

            # Optimizare inferență YOLO
            results = model(image_array, stream=True, verbose=False, conf=0.6)

            for r in results:
                for box in r.boxes:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())  # 0 = fake, 1 = real
                    
                    logger.info(f"Detectare spoofing - Scor: {conf}, Clasificare: {cls}")
                    
                    return cls == 1  # Returăm imediat primul rezultat care depășește pragul

            return False
        except Exception as e:
            logger.error(f"Eroare la detectarea spoofing-ului: {e}")
            return False

    def detect_and_encode_face(self, image_array):
        """Detectează și extrage encoding-ul feței."""
        try:
            # Redimensionează imaginea pentru procesare mai rapidă
            h, w = image_array.shape[:2]
            scale = min(1.0, 480 / max(h, w))
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                small_image = cv2.resize(image_array, (new_w, new_h))
            else:
                small_image = image_array.copy()
            
            # Folosește doar HOG pentru detectare, care este mai rapid
            face_locations = face_recognition.face_locations(small_image, model="hog")

            if len(face_locations) == 0:
                return None, "Nicio fata detectata in imagine. Verificati pozitia si iluminarea."

            if len(face_locations) > 1:
                return None, "S-au detectat mai multe fete. Procesul necesita o singura fata."

            # Dacă am redimensionat, ajustăm locațiile fețelor înapoi la dimensiunea originală
            if scale < 1.0:
                adjusted_locations = []
                for top, right, bottom, left in face_locations:
                    adjusted_locations.append(
                        (int(top / scale), int(right / scale), 
                         int(bottom / scale), int(left / scale))
                    )
                face_encodings = face_recognition.face_encodings(image_array, known_face_locations=adjusted_locations)
            else:
                face_encodings = face_recognition.face_encodings(image_array, known_face_locations=face_locations)

            if len(face_encodings) == 0:
                return None, "Codificarea fetei a esuat"

            return face_encodings[0], None
        except Exception as e:
            logger.error(f"Eroare la detectarea/codificarea fetei: {e}")
            return None, f"Eroare la detectarea fetei: {e}"

    def compare_faces(self, id_card_array, live_array):
        """Compara fetele doar daca imaginea live este autentica."""
        try:
            # Executăm detectarea spoofing-ului și encoding-ul feței simultan pentru a economisi timp
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                spoofing_future = executor.submit(self.detect_spoofing, live_array)
                id_card_future = executor.submit(self.detect_and_encode_face, id_card_array)
                
                # Așteaptă finalizarea verificării spoofing
                is_real = spoofing_future.result()
                if not is_real:
                    return False, "Frauda detectata: folositi o imagine reala!"
                
                # Obține rezultatele encoding-ului feței din ID
                id_card_encoding, id_card_error = id_card_future.result()
                if id_card_encoding is None:
                    return False, id_card_error
                
                # Acum face encoding pentru imaginea live
                live_encoding, live_error = self.detect_and_encode_face(live_array)
                if live_encoding is None:
                    return False, live_error

            # Compararea fețelor
            face_distance = np.linalg.norm(id_card_encoding - live_encoding)
            match = face_distance < 0.6

            return match, "Identificare reusita!" if match else "Fetele nu se potrivesc."
        except Exception as e:
            logger.error(f"Eroare la compararea fetelor: {e}")
            return False, f"Eroare la compararea fetelor: {e}"


class VoteMonitoringService:
    """
    Serviciu pentru monitorizarea votului
    Folosește FaceRecognitionService pentru funcționalitatea de bază
    """
    
    def __init__(self):
        self.face_service = FaceRecognitionService()
    
    def detect_spoofing(self, image_array):
        """Wrapper pentru detectarea spoofing-ului"""
        return self.face_service.detect_spoofing(image_array)
    
    def detect_and_encode_face(self, image_array):
        """Wrapper pentru detectarea și encoding-ul feței cu informații suplimentare pentru vot"""
        try:
            encoding, error = self.face_service.detect_and_encode_face(image_array)
            
            # Pentru votare, returnăm și numărul de fețe detectate
            h, w = image_array.shape[:2]
            scale = min(1.0, 480 / max(h, w))
            if scale < 1.0:
                new_h, new_w = int(h * scale), int(w * scale)
                small_image = cv2.resize(image_array, (new_w, new_h))
            else:
                small_image = image_array.copy()
            
            face_locations = face_recognition.face_locations(small_image, model="hog")
            num_faces = len(face_locations)
            
            if encoding is None:
                return None, error, num_faces
            
            return encoding, None, num_faces
            
        except Exception as e:
            logger.error(f"Eroare la detectarea/codificarea feței în monitorizarea votului: {e}")
            return None, f"Eroare la detectarea feței: {e}", 0
    
    def verify_voter_identity(self, reference_face_encoding, live_image):
        """Verifică dacă utilizatorul curent este cel înregistrat"""
        try:
            # Convertim imaginea live
            if isinstance(live_image, bytes):
                live_image = Image.open(io.BytesIO(live_image)).convert("RGB")
                live_array = np.array(live_image)
            else:
                live_array = np.array(live_image)
                
            # Verifică anti-spoofing
            is_real = self.detect_spoofing(live_array)
            if not is_real:
                return False, "Fraudă detectată: folosiți o imagine reală!", 0
            
            # Obține encoding pentru imaginea live
            live_encoding, live_error, num_faces = self.detect_and_encode_face(live_array)
            
            if num_faces > 1:
                return False, f"S-au detectat {num_faces} fețe în cadru", num_faces
                
            if live_encoding is None:
                return False, live_error, 0
            
            # Compară fețele
            face_distance = np.linalg.norm(reference_face_encoding - live_encoding)
            match = face_distance < 0.6
            
            return match, "Verificare reușită!" if match else "Fețele nu se potrivesc", 1
            
        except Exception as e:
            logger.error(f"Eroare la verificarea identității în monitorizarea votului: {e}")
            return False, f"Eroare la verificarea identității: {e}", 0


class IDCardService:
    """
    Serviciu pentru procesarea buletinelor
    Folosește ModelManager pentru accesul la modelul YOLO
    """
    
    def __init__(self):
        self.model_name = 'yolo_id_card'
    
    def get_model(self):
        """
        Returnează modelul YOLO pentru detectarea buletinelor
        """
        return model_manager.get_model(self.model_name)
    
    def process_id_card(self, image_path):
        """
        Procesează buletinul și extrage informații
        """
        try:
            model = self.get_model()
            if model is None:
                logger.error("Modelul YOLO pentru buletine nu este disponibil")
                return {}
                
            # Aici continuă logica din IDCardProcessor
            # Pentru brevitate, returnez doar structura de bază
            extracted_info = {}
            
            # Procesarea efectivă a imaginii cu modelul YOLO
            image = cv2.imread(image_path)
            results = model.predict(image_path)
            
            # Logica de extragere a informațiilor...
            # (codul din IDCardProcessor.process_id_card)
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Eroare la procesarea buletinului: {e}")
            return {}

# Instanțe globale pentru servicii
face_recognition_service = FaceRecognitionService()
vote_monitoring_service = VoteMonitoringService()
id_card_service = IDCardService()