import pytesseract
from PIL import Image
import re
import cv2
import os
from ultralytics import YOLO
from decouple import config
import numpy as np
import tensorflow as tf

# Configurare Tesseract
pytesseract.pytesseract.cmd = config('TESSERACT_CMD_PATH')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'media', 'models', 'best.pt')

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

class IDCardProcessor:
    def __init__(self):
        try:
            print(f"Loading YOLO model from {MODEL_PATH}")
            self.model = YOLO(MODEL_PATH)
            print("YOLO model loaded successfully!")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")

    def preprocess_black_white(self, region):
        """
        Preprocessing for general black and white ID card images.
        """
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def preprocess_black_white_cnp(self, region):
        """
        Specific preprocessing for regions likely to contain the CNP.
        Includes higher contrast and threshold adjustments.
        """
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)
        _, binary = cv2.threshold(contrast_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def extract_text_with_retries(self, region, lang='ron', max_retries=2):
        """
        Retry extraction with different preprocessing if the first attempt fails.
        """
        text = ""
        for attempt in range(max_retries):
            try:
                custom_config = '--psm 7' if attempt == 0 else '--psm 6'
                text = pytesseract.image_to_string(region, lang=lang, config=custom_config).strip()
                if text:  # If any text is detected, break the loop
                    break
            except Exception as e:
                print(f"Retry {attempt+1} failed with error: {e}")
        return text or "Text nedetectat"

    def extract_text_from_region(self, image, box, field_name=None):
        """
        Extract text from a specific region using Tesseract OCR.

        :param field_name: Optional. If provided, applies specific preprocessing for fields like 'CNP'.
        """
        x1, y1, x2, y2 = map(int, box)
        region = image[y1:y2, x1:x2]
        
        # Specific preprocessing for 'CNP' field
        if field_name == "CNP":
            processed_region = self.preprocess_black_white_cnp(region)
            custom_config = '--psm 7'  # Adjust for better numeric extraction
        else:
            processed_region = self.preprocess_black_white(region)
            custom_config = '--psm 6'

        text = pytesseract.image_to_string(processed_region, lang='ron', config=custom_config).strip()

        # Retry logic if the extracted text is empty or invalid
        if not text and field_name == "CNP":
            text = self.extract_text_with_retries(processed_region, lang='ron')

        return text if text else "Text nedetectat"

    def clean_extracted_text(self, text, field_name):
        """
        Clean extracted text to remove unwanted characters.
        """
        if field_name == "Valabilitate":
            match = re.findall(r'\d{2}\.\d{2}\.\d{2,4}', text)
            return " ".join(match) if match else "Text nedetectat"
        if field_name in ["CNP", "SERIA", "NR", "cod_identity"]:
            return re.sub(r'[^A-Za-z0-9]', '', text).strip()
        if field_name in ["Nume", "Prenume", "Cetatenie", "LocNastere", "Domiciliu", "EmisaDe"]:
            return re.sub(r'[^A-Za-zăîșțâ\- ]', '', text).strip()
        return text.strip()

    def extract_cnp(self, text):
        """
        Extract a valid CNP from the given text using regex.
        """
        cnp_pattern = r'\b[1-8]\d{12}\b'
        match = re.search(cnp_pattern, text)
        if match:
            cnp = match.group()
            # Correct common OCR errors (e.g., replace 'O' with '0')
            cnp = cnp.replace('O', '0').replace('I', '1')
            return cnp
        return None

    def validate_cnp_with_details(self, cnp):
        """
        Validate the structure and checksum of a CNP, providing detailed feedback.
        """
        details = {"extracted_text": cnp, "errors": []}

        if len(cnp) != 13 or not cnp.isdigit():
            details["errors"].append("Lungimea CNP-ului trebuie să fie exact 13 cifre.")
            return details

        # Extract components
        sex = int(cnp[0])
        year = int(cnp[1:3])
        month = int(cnp[3:5])
        day = int(cnp[5:7])
        county = int(cnp[7:9])
        control_digit = int(cnp[12])

        # Validate sex and century
        if sex not in range(1, 9):
            details["errors"].append("Prima cifră a CNP-ului (S) nu este validă.")

        # Validate month and day
        if not (1 <= month <= 12):
            details["errors"].append("Luna nașterii (LL) nu este validă.")
        if not (1 <= day <= 31):
            details["errors"].append("Ziua nașterii (ZZ) nu este validă.")

        # Validate county code
        if county < 1 or county > 52:
            details["errors"].append("Codul județului (JJ) nu este valid.")

        # Validate control digit
        weights = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]
        control_sum = sum(int(cnp[i]) * weights[i] for i in range(12))
        expected_control_digit = control_sum % 11
        if expected_control_digit == 10:
            expected_control_digit = 1

        if control_digit != expected_control_digit:
            details["errors"].append(
                f"Cifra de control (C) este incorectă. A fost detectată: {control_digit}, trebuia să fie: {expected_control_digit}."
            )

        if not details["errors"]:
            details["status"] = "CNP valid"
        else:
            details["status"] = "CNP invalid"

        return details

    def process_id_card(self, image_path):
        """
        Process an ID card image to extract and validate information.
        """
        image = cv2.imread(image_path)
        results = self.model.predict(image_path)
        extracted_info = {}
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                region = image[y1:y2, x1:x2]
                class_name = self.model.names[int(box.cls[0].cpu().numpy())]

                # Use field-specific preprocessing if applicable
                raw_text = self.extract_text_from_region(image, [x1, y1, x2, y2], field_name=class_name)
                cleaned_text = self.clean_extracted_text(raw_text, class_name)

                if class_name == "CNP":
                    cnp = self.extract_cnp(cleaned_text)
                    if cnp:
                        validation_details = self.validate_cnp_with_details(cnp)
                        extracted_info[class_name] = {
                            "value": cnp,
                            "status": validation_details["status"],
                            "errors": validation_details["errors"]
                        }
                    else:
                        extracted_info[class_name] = {
                            "value": "",
                            "status": "CNP nedetectat",
                            "errors": ["CNP nu a fost detectat corect din imagine."]
                        }
                else:
                    extracted_info[class_name] = cleaned_text

        return extracted_info
