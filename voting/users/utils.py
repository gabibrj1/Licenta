import pytesseract
from PIL import Image
import re
import cv2
import os
from ultralytics import YOLO
from decouple import config
import numpy as np
import tensorflow as tf
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import csv
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from typing import List, Dict
from fuzzywuzzy import process
from rapidfuzz import fuzz
from unidecode import unidecode





# Configurare Tesseract
pytesseract.pytesseract.cmd = config('TESSERACT_CMD_PATH')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'media', 'models', 'best.pt')

class LocalityMatcher:
    def __init__(self, csv_path: str):
        """
        Constructor îmbunătățit pentru încărcarea și procesarea localităților.
        """
        self.localitati_df = pd.read_csv(csv_path)
        # Umplem valorile NaN cu un șir gol pentru a evita erori
        self.localitati_df.fillna('', inplace=True)

        # Preprocesăm toate numele de localități
        self.localitati_df['search_key'] = self.localitati_df['nume'].apply(self.preprocess_locality)
        # Creăm o copie fără diacritice pentru căutare
        self.localitati_df['search_key_normalized'] = self.localitati_df['search_key'].apply(
            lambda x: unidecode(x.lower())
        )

        # Tratăm special cazul București pentru a preveni erorile
        self.localitati_df.loc[
            self.localitati_df['nume'].str.contains(r'Bucure', na=False, case=False), 'search_key_normalized'
        ] = 'bucuresti'

        # Inițializăm vectorizatorul cu parametri optimizați
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',  # Folosim n-grame de caractere
            ngram_range=(2, 4),  # Considerăm secvențe de 2-4 caractere
            min_df=1,
            max_df=0.95
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.localitati_df['search_key_normalized'])

    def preprocess_locality(self, text: str) -> str:
        """
        Preprocesare îmbunătățită pentru numele localităților.
        """
        if not isinstance(text, str):
            return ''
        
        # Convertim la lowercase și eliminăm spațiile în plus
        text = text.lower().strip()

        # Eliminăm prefixele comune și codurile de județ
        prefixes_pattern = r'\b(jud|mun|oras|or|com)\b\.?\s*'
        county_codes_pattern = r'\b[a-z]{1,2}\b'

        text = re.sub(prefixes_pattern, '', text, flags=re.IGNORECASE)
        text = re.sub(county_codes_pattern, '', text, flags=re.IGNORECASE)

        # Curățăm caracterele speciale și spațiile multiple
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def find_best_matches(self, input_text: str, top_n: int = 5, min_similarity: float = 0.1) -> List[Dict]:
        """
        Găsirea potrivirilor îmbunătățită cu praguri de similaritate și procesare mai robustă.
        """
        # Preprocesăm textul de intrare
        cleaned_input = self.preprocess_locality(input_text)
        normalized_input = unidecode(cleaned_input.lower())

        # Verificăm mai întâi potriviri exacte (ignorând diacritice)
        exact_matches = self.localitati_df[
            self.localitati_df['search_key_normalized'] == normalized_input
        ]

        if not exact_matches.empty:
            return [
                {
                    'localitate': row.to_dict(),
                    'similarity': 1.0,
                    'match_type': 'exact'
                }
                for _, row in exact_matches.iterrows()
            ]

        # Căutăm potriviri parțiale
        input_vector = self.vectorizer.transform([normalized_input])
        similarities = cosine_similarity(input_vector, self.tfidf_matrix).flatten()

        # Filtrăm rezultatele sub pragul de similaritate
        valid_indices = np.where(similarities >= min_similarity)[0]

        if len(valid_indices) == 0:
            return []

        # Sortăm rezultatele după similaritate
        best_indices = valid_indices[np.argsort(similarities[valid_indices])[-top_n:][::-1]]

        results = []
        for idx in best_indices:
            locality_data = self.localitati_df.iloc[idx].to_dict()
            similarity_score = float(similarities[idx])

            # Adăugăm informații despre tipul de potrivire
            match_type = 'high' if similarity_score > 0.7 else 'partial'

            results.append({
                'localitate': locality_data,
                'similarity': similarity_score,
                'match_type': match_type
            })

        return results
def load_localitati():
    """
    Încărcarea localităților cu tratarea erorilor îmbunătățită.
    """
    try:
        localitati = pd.read_csv(settings.LOCALITATI_CSV_PATH)
        if localitati.empty:
            raise ValueError("Fișierul CSV cu localități este gol")
        
        required_columns = ['nume', 'judet']
        missing_columns = [col for col in required_columns if col not in localitati.columns]
        if missing_columns:
            raise ValueError(f"Lipsesc coloanele necesare: {', '.join(missing_columns)}")
            
        return localitati
    except FileNotFoundError:
        raise FileNotFoundError(f"Fișierul CSV cu localități nu a fost găsit la calea: {settings.LOCALITATI_CSV_PATH}")
    except Exception as e:
        raise Exception(f"Eroare la încărcarea localităților: {str(e)}")

class ImageManipulator:
    @staticmethod
    def rotate_image(image_path, angle):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Nu s-a putut încărca imaginea")
            
        # Normalizează unghiul la 0-360
        angle = angle % 360
        
        if angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(image, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return image

    @staticmethod
    def flip_image(image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Nu s-a putut încărca imaginea")
        return cv2.flip(image, 1)  # 1 pentru oglindire orizontala
        

class IDCardDetector:
    def __init__(self):
        self.model_path = os.path.join('media', 'models', 'id-card-detector', 'frozen_inference_graph.pb')
        self.label_map_path = os.path.join('media', 'models', 'id-card-detector', 'label_map.pbtxt')

        # Load the TensorFlow model
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(self.model_path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        self.session = tf.compat.v1.Session(graph=self.detection_graph)

    def detect_id_card(self, image_path):
        """
        Detectează și decupează cartea de identitate folosind TensorFlow.
        """
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_np = np.array(image_rgb)

        # Prepare input and output tensors
        image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

        # Run inference
        (boxes, scores, classes, num_detections) = self.session.run(
            [boxes, scores, classes, num_detections],
            feed_dict={image_tensor: np.expand_dims(image_np, axis=0)}
        )

        # Filter boxes with high confidence
        height, width, _ = image.shape
        for i in range(int(num_detections[0])):
            if scores[0][i] > 0.6:  # Threshold de încredere
                box = boxes[0][i]
                y1, x1, y2, x2 = int(box[0] * height), int(box[1] * width), int(box[2] * height), int(box[3] * width)
                cropped_image = image[y1:y2, x1:x2]
                return cropped_image

        return None  # Returnăm None dacă nu s-a detectat niciun ID
    
def extract_text(image_path):
    """
    Extrage textul dintr-o imagine folosind Tesseract OCR.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='ron')
        return text
    except Exception as e:
        print(f"Eroare la extragerea textului: {e}")
        return ""
    
def load_valid_keywords(file_path):
    """
    Încarcă lista de cuvinte cheie valide dintr-un fișier CSV.
    """
    keywords = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            keywords = [row['keyword'] for row in reader]
    except Exception as e:
        print(f"Eroare la citirea cuvintelor cheie: {e}")
    return keywords




    
@dataclass
class CNPValidationResult:
    cnp: str
    valid: bool
    errors: List[str]
    componente: Dict[str, str]

class ProcessorCNP:
    def __init__(self):
        self.NUMAR_CONTROL = "279146358279"
        self.CODURI_SEX = set(range(1, 9))
        self.CODURI_JUDETE = set(range(1, 53))
        self.ZILE_LUNA = {
            1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }

    def preprocesare_imagine_cnp(self, regiune: np.ndarray) -> Optional[np.ndarray]:
        """
        Preprocesează regiunea imaginii pentru extragerea optimă a CNP-ului
        """
        if regiune is None:
            return None
            
        # Conversie la grayscale
        gri = cv2.cvtColor(regiune, cv2.COLOR_BGR2GRAY)
        
        # Îmbunătățire contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        imbunatatit = clahe.apply(gri)
        
        # Reducere zgomot
        denoised = cv2.bilateralFilter(imbunatatit, 9, 75, 75)
        
        # Binarizare adaptivă
        binar = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Operații morfologice
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        curatat = cv2.morphologyEx(binar, cv2.MORPH_CLOSE, kernel)
        
        return curatat

    def extrage_cnp(self, text: str) -> Optional[str]:
        """
        Extrage CNP-ul din textul detectat
        """
        # Corecție erori OCR comune
        text_curatat = text.replace('O', '0').replace('I', '1').replace('l', '1')
        text_curatat = re.sub(r'[^0-9]', '', text_curatat)
        
        # Caută secvențe de 13 cifre
        cnp_potentiale = re.findall(r'\d{13}', text_curatat)
        
        for cnp in cnp_potentiale:
            if self._verifica_structura(cnp):
                return cnp
                
        return None

    def _verifica_structura(self, cnp: str) -> bool:
        """
        Verifică dacă structura CNP-ului este validă
        """
        if len(cnp) != 13:
            return False
            
        sex = int(cnp[0])
        luna = int(cnp[3:5])
        zi = int(cnp[5:7])
        judet = int(cnp[7:9])
        
        if not (sex in self.CODURI_SEX and
                1 <= luna <= 12 and
                1 <= zi <= self.ZILE_LUNA[luna] and
                judet in self.CODURI_JUDETE):
            return False
            
        return True

    def valideaza_cnp(self, cnp: str) -> CNPValidationResult:
        """
        Validează complet CNP-ul și returnează rezultatul
        """
        if not cnp or len(cnp) != 13:
            return CNPValidationResult(
                cnp=cnp,
                valid=False,
                errors=["CNP-ul trebuie să aibă exact 13 cifre"],
                componente={}
            )

        componente = {
            "sex_secol": cnp[0],
            "an": cnp[1:3],
            "luna": cnp[3:5],
            "zi": cnp[5:7],
            "judet": cnp[7:9],
            "secventa": cnp[9:12],
            "cifra_control": cnp[12]
        }

        erori = []

        # Validare sex și secol
        sex = int(componente["sex_secol"])
        if sex not in self.CODURI_SEX:
            erori.append(f"Cod sex/secol invalid: {sex}")

        # Validare lună
        luna = int(componente["luna"])
        if not 1 <= luna <= 12:
            erori.append(f"Lună invalidă: {luna}")

        # Validare zi
        zi = int(componente["zi"])
        if luna in self.ZILE_LUNA:
            if not 1 <= zi <= self.ZILE_LUNA[luna]:
                erori.append(f"Zi invalidă pentru luna {luna}: {zi}")
        else:
            erori.append("Nu se poate valida ziua din cauza lunii invalide")

        # Validare județ
        judet = int(componente["judet"])
        if judet not in self.CODURI_JUDETE:
            erori.append(f"Cod județ invalid: {judet}")

        # Validare cifră de control
        cifra_control_asteptata = self._calculeaza_cifra_control(cnp)
        cifra_control_actuala = int(componente["cifra_control"])
        if cifra_control_asteptata != cifra_control_actuala:
            erori.append(
                f"Cifră de control invalidă. Așteptată: {cifra_control_asteptata}, "
                f"Actuală: {cifra_control_actuala}"
            )

        return CNPValidationResult(
            cnp=cnp,
            valid=len(erori) == 0,
            errors=erori,
            componente=componente
        )

    def _calculeaza_cifra_control(self, cnp: str) -> int:
        """
        Calculează cifra de control pentru CNP
        """
        suma_control = sum(
            int(cnp[i]) * int(self.NUMAR_CONTROL[i])
            for i in range(12)
        )
        rest = suma_control % 11
        return 1 if rest == 10 else rest

    def proceseaza_regiune_cnp(self, imagine: np.ndarray, box: Tuple[int, int, int, int]) -> CNPValidationResult:
        """
        Procesează o regiune care conține un CNP folosind multiple încercări
        """
        x1, y1, x2, y2 = map(int, box)
        regiune = imagine[y1:y2, x1:x2]
        
        # Metode de preprocesare
        metode_preprocesare = [
            self.preprocesare_imagine_cnp,
            lambda r: cv2.threshold(cv2.cvtColor(r, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        ]
        
        # Configurări OCR
        configurari_ocr = [
            '--psm 7 -c tessedit_char_whitelist=0123456789',
            '--psm 6 -c tessedit_char_whitelist=0123456789',
            '--psm 8 -c tessedit_char_whitelist=0123456789'
        ]
        
        for preprocesare in metode_preprocesare:
            regiune_procesata = preprocesare(regiune)
            for config in configurari_ocr:
                try:
                    text = pytesseract.image_to_string(
                        regiune_procesata,
                        config=config
                    ).strip()
                    
                    cnp = self.extrage_cnp(text)
                    if cnp:
                        rezultat = self.valideaza_cnp(cnp)
                        if rezultat.valid:
                            return rezultat
                except Exception as e:
                    continue
        
        return CNPValidationResult(
            cnp="",
            valid=False,
            errors=["CNP-ul nu a putut fi extras"],
            componente={}
        )
    


class IDCardProcessor:
    def __init__(self):
        self.procesor_cnp = ProcessorCNP()
        try:
            print(f"Loading YOLO model from {MODEL_PATH}")
            self.model = YOLO(MODEL_PATH)
            print("YOLO model loaded successfully!")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")

    def preprocess_black_white(self, region):
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def extract_text_with_retries(self, region, lang='ron', max_retries=2):
        text = ""
        for attempt in range(max_retries):
            try:
                custom_config = '--psm 7' if attempt == 0 else '--psm 6'
                text = pytesseract.image_to_string(region, lang=lang, config=custom_config).strip()
                if text:
                    break
            except Exception as e:
                print(f"Retry {attempt+1} failed with error: {e}")
        return text or "Text nedetectat"

    def extract_text_from_region(self, image, box, field_name=None):
        x1, y1, x2, y2 = map(int, box)
        region = image[y1:y2, x1:x2]
        
        if field_name == "CNP":
            processed_region = self.procesor_cnp.preprocesare_imagine_cnp(region)
            custom_config = '--psm 7'
        else:
            processed_region = self.preprocess_black_white(region)
            custom_config = '--psm 6'

        text = pytesseract.image_to_string(processed_region, lang='ron', config=custom_config).strip()

        if not text and field_name == "CNP":
            text = self.extract_text_with_retries(processed_region, lang='ron')

        return text if text else "Text nedetectat"

    def clean_extracted_text(self, text: str, field_name: str) -> str:
        if field_name == "Valabilitate":
            match = re.findall(r'\d{2}\.\d{2}\.\d{2,4}', text)
            return " ".join(match) if match else "Text nedetectat"
        if field_name in ["CNP", "SERIA", "NR", "cod_identity"]:
            return re.sub(r'[^A-Za-z0-9]', '', text).strip()
        if field_name == "Domiciliu":
            text = re.sub(r'[^A-Za-z0-9ăîșțâ()\-\. ]', '', text)
            text = re.sub(r'\bRA\s*N\s*(?=(?:Bd|Str|B-dul)\.?)', '', text)
            text = re.sub(r'\bN\s*(?=(?:Bd|Str|B-dul)\.?)', '', text)

            numar_pattern = r'(nr\.\s*\d+|Nr\.\s*\d+|număr\s*\d+|nr\s*\d+)'
            bloc_pattern = r'(bl\.\s*[A-Za-z0-9]+|bloc\s*[A-Za-z0-9]+)'
            etaj_pattern = r'(et\.\s*\d+|etaj\s*\d+)'
            ap_pattern = r'(ap\.\s*\d+|apartament\s*\d+)'
            final_text = text
            all_patterns = [
            (numar_pattern, ''),
            (bloc_pattern, ''),
            (etaj_pattern, ''),
            (ap_pattern, '')
            ]
            for pattern, _ in all_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    final_text = text[:match.end()]
                    for next_pattern, _ in all_patterns:
                        next_match = re.search(next_pattern, text[match.end():], re.IGNORECASE)
                        if next_match:
                            final_text += text[match.end():match.end() + next_match.end()]

            return re.sub(r'\s+', ' ', final_text).strip()
        
        if field_name == "LocNastere":
            text = re.sub(r'[^A-Za-z0-9ăîșțâ\- ]', '', text).strip()
            text = re.sub(r'MunBucurești\s*Sec[tf]?\s*(\d?)', lambda m: f'MunBucurești Sec.{m.group(1)}' if m.group(1) else 'MunBucurești', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

            
        if field_name in ["Nume", "Prenume", "Cetatenie", "EmisaDe"]:
            return re.sub(r'[^A-Za-zăîșțâȚĂÂȘÎ\- ]', '', text).strip()
        return text.strip()

    def process_id_card(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        results = self.model.predict(image_path)
        extracted_info = {}

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                class_name = self.model.names[int(box.cls[0].cpu().numpy())]

                if class_name == "CNP":
                    rezultat_cnp = self.procesor_cnp.proceseaza_regiune_cnp(
                        image, 
                        (x1, y1, x2, y2)
                    )
                    if rezultat_cnp.valid:
                        extracted_info["CNP"] = {
                            "value": rezultat_cnp.cnp,
                            "status": "CNP valid",
                            "errors": []
                        }
                    else:
                        extracted_info["CNP"] = {
                            "value": rezultat_cnp.cnp if rezultat_cnp.cnp else "",
                            "status": "CNP invalid",
                            "errors": rezultat_cnp.errors
                        }
                else:
                    raw_text = self.extract_text_from_region(image, [x1, y1, x2, y2], field_name=class_name)
                    extracted_info[class_name] = self.clean_extracted_text(raw_text, class_name)

        return extracted_info
