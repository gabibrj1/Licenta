import pytesseract
from PIL import Image
import re
import cv2
import numpy as np
from decouple import config

# Configurarea căii pentru Tesseract
pytesseract.pytesseract.tesseract_cmd = config('TESSERACT_CMD_PATH')

def preprocess_image(image):
    """aplica threshold și morfologie pentru a prelucra imaginea."""
    #convertim imaginea la tonuri de gri
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #aplicam threshold pentru a evidentia textul
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #eliminam zgomotul cu morfologie
    kernel = np.ones((1, 1), np.uint8)
    processed_image = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return processed_image

def extract_text_from_image(image_file):
    """Extrage textul din fisierul de imagine incarcat."""
    try:
        #citim continutul fis si il pastram in memorie
        image_data = image_file.read()
        #trnasf datele intr-un array numpy
        np_image = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

        #procesam imaginea
        processed_image = preprocess_image(image)
        pil_image = Image.fromarray(processed_image)
        text = pytesseract.image_to_string(pil_image, lang='ron')

        print("Text extras din imagine:\n", text)
        
        #resetam cursorul fisierului pentru alte functii care poate vor avea nevoie de el
        image_file.seek(0)
        
        return text
    except Exception as e:
        print(f"Eroare la extragerea textului: {e}")
        return ""

def parse_id_card(text):
    """Extrage datele de identificare din textul recunoscut."""
    data = {}

    # Extragem CNP-ul
    cnp_match = re.search(r'CNP\s*(\d{13})', text)  # Cauta formatul "CNP 1234567890123"
    if not cnp_match:
        cnp_match = re.search(r'\b\d{13}\b', text)  # Cauta doar un sir de 13 cifre, daca nu exista "CNP"
    if cnp_match:
        data['cnp'] = cnp_match.group(1) if cnp_match.group(1) else cnp_match.group(0)

    # extragem seria si numărul
    series_number_match = re.search(r'SERIA\s*([A-Z]{2})\s*NR\s*(\d{6})', text)
    if series_number_match:
        data['series'] = series_number_match.group(1)
        data['number'] = series_number_match.group(2)

    #extragem numele
    name_match = re.search(r'(Nume|Nom|Last name)\s*([A-Z\s\-]+)', text)
    if name_match:
        data['last_name'] = name_match.group(2).strip()

    #extragem prenumele
    first_name_match = re.search(r'(Prenume|Prenom|First name)\s*([A-Z\s\-]+)', text)
    if first_name_match:
        data['first_name'] = first_name_match.group(2).strip()

    #cetatenia
    cetatenie_match = re.search(r'(Cetățenie|Nationalite|Nationality)\s*([A-Z\s\-]+)', text)
    if cetatenie_match:
        data['citizenship'] = cetatenie_match.group(2).strip()

    #locul nasterii
    birth_place_match = re.search(r'(Loc naștere|Lieu de naissance|Place of birth)\s*([A-Z\s,\.\-]+)', text)
    if birth_place_match:
        data['place_of_birth'] = birth_place_match.group(2).strip()

    #domiciliul
    address_match = re.search(r'(Domiciliu|Adresse|Address)\s*([A-Z\s,\.\-]+)', text)
    if address_match:
        data['address'] = address_match.group(2).strip()

    #autoritatea emitenta
    issuing_authority_match = re.search(r'(Emisă de|Delivree par|Issued by)\s*([A-Z\s,\.\-]+)', text)
    if issuing_authority_match:
        data['issuing_authority'] = issuing_authority_match.group(2).strip()

    # Sex
    sex_match = re.search(r'(Sex|Sexe|Sex)\s*([MF])', text)
    if sex_match:
        data['sex'] = 'Male' if sex_match.group(2) == 'M' else 'Female'

    #valabilitate
    date_match = re.search(r'(Valabilitate|Validite|Validity)\s*(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})', text)
    if date_match:
        data['date_of_issue'] = date_match.group(2)
        data['date_of_expiry'] = date_match.group(3)

    return data if 'cnp' in data and 'series' in data else None

def is_valid_id_card(image_file):
    """Verifică dacă imaginea încărcată este un buletin valid."""
    try:
        # Citim continutul fisierului
        image_data = image_file.read()
        np_image = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        image_file.seek(0)

        #convertim imaginea in tonuri de gri si aplicăm detectia contururilor
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:
                return True
    except Exception as e:
        print(f"Eroare la validarea buletinului: {e}")
    
    return False
