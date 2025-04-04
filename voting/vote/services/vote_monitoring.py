import logging
import numpy as np
import cv2
from ultralytics import YOLO
import face_recognition
import concurrent.futures
from PIL import Image
import io

logger = logging.getLogger(__name__)

class VoteMonitoringService:
    MODEL_PATH = r"C:\Users\brj\Desktop\voting\media\models\l_version_1_300.pt"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = YOLO(self.MODEL_PATH)
        print("Inițializez serviciul de monitorizare vot...")
        try:
            self.model = YOLO(self.MODEL_PATH)
            print("Modelul incarcat cu succes din: {self.MODEL_PATH}")
        except Exception as e:
            print(f"Eroare la incarcarea modelului YOLO: {e}")

    def detect_spoofing(self, image_array):
        """Verifică dacă imaginea este reală sau falsă folosind YOLO."""
        try:
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
            results = self.model(image_array, stream=True, verbose=False, conf=0.6)

            for r in results:
                for box in r.boxes:
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())  # 0 = fake, 1 = real
                    
                    logger.info(f"Detectare spoofing în votare - Scor: {conf}, Clasificare: {cls}")
                    
                    return cls == 1  # Returăm imediat primul rezultat care depășește pragul

            return False
        except Exception as e:
            logger.error(f"Eroare la detectarea spoofing-ului în monitorizarea votului: {e}")
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
                return None, "Nicio față detectată", 0
            
            num_faces = len(face_locations)
            if num_faces > 1:
                return None, "S-au detectat mai multe fețe", num_faces

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
                return None, "Codificarea feței a eșuat", 0

            return face_encodings[0], None, 1
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