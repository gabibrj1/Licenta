# vote/services.py

import os
import re
import pickle
import numpy as np
from django.conf import settings
import tensorflow as tf
import logging

# Configurăm logging pentru a urmări mai ușor problemele
logger = logging.getLogger(__name__)

class VotingSectionAIService:
    """
    Serviciu pentru recomandarea secțiilor de votare folosind AI
    """
    
    def __init__(self):
        # Calea către modelele salvate
        model_dir = os.path.join(settings.BASE_DIR, 'vote', 'ai_models')
        self.model_loaded = False
        
        # Încărcăm modelul ML și datele asociate
        try:
            # Încărcăm vectorizatorul TF-IDF
            with open(os.path.join(model_dir, 'tfidf_vectorizer.pkl'), 'rb') as f:
                self.vectorizer = pickle.load(f)
                
            # Încărcăm indicii de caracteristici folosiți în antrenare
            with open(os.path.join(model_dir, 'feature_indices.pkl'), 'rb') as f:
                self.feature_indices = pickle.load(f)
                
            # Încărcăm encoder-ul de etichete
            with open(os.path.join(model_dir, 'label_encoder.pkl'), 'rb') as f:
                self.label_encoder = pickle.load(f)
                
            # Încărcăm detaliile secțiilor
            with open(os.path.join(model_dir, 'section_details.pkl'), 'rb') as f:
                self.section_details = pickle.load(f)
                
            # Încărcăm dicționarul îmbunătățit pentru căutare directă după stradă
            try:
                # Încercăm mai întâi noul format
                with open(os.path.join(model_dir, 'street_to_section_map.pkl'), 'rb') as f:
                    self.street_to_section_map = pickle.load(f)
                    self.using_improved_lookup = True
                    logger.info("S-a încărcat dicționarul îmbunătățit street_to_section_map.pkl")
                    
                # Încărcăm și dicționarul normalizat dacă există
                try:
                    with open(os.path.join(model_dir, 'normalized_street_map.pkl'), 'rb') as f:
                        self.normalized_street_map = pickle.load(f)
                        self.using_normalization = True
                        logger.info("S-a încărcat dicționarul normalized_street_map.pkl")
                except Exception as e:
                    logger.warning(f"Nu s-a putut încărca dicționarul normalizat: {e}")
                    self.using_normalization = False
                    # Vom construi un dicționar normalizat la cerere
                    self.normalized_street_map = {}
                    
            except Exception as e:
                logger.warning(f"Nu s-a putut încărca dicționarul îmbunătățit: {e}")
                # Fallback la formatul vechi dacă nu este disponibil cel nou
                with open(os.path.join(model_dir, 'street_to_section.pkl'), 'rb') as f:
                    self.street_to_section = pickle.load(f)
                    self.using_improved_lookup = False
                    self.using_normalization = False
                    logger.info("S-a încărcat dicționarul vechi street_to_section.pkl")
                
            # Încărcăm modelul TensorFlow - Încercăm toate metodele posibile
            try:
                # Prima încercare: formatul .keras
                keras_path = os.path.join(model_dir, 'voting_section_model.keras')
                if os.path.exists(keras_path):
                    self.model = tf.keras.models.load_model(keras_path)
                    self.model_loaded = True
                    self.is_categorical = self.model.output_shape[-1] > 1
                    logger.info("Model încărcat din formatul .keras")
            except Exception as e1:
                logger.warning(f"Încărcarea din format .keras a eșuat: {e1}")
                try:
                    # A doua încercare: formatul SavedModel
                    savedmodel_path = os.path.join(model_dir, 'voting_section_model_savedmodel')
                    if os.path.exists(savedmodel_path):
                        self.model = tf.saved_model.load(savedmodel_path)
                        self.model_loaded = True
                        # Nu putem verifica output_shape pentru SavedModel, presupunem că este regresie
                        self.is_categorical = False
                        logger.info("Model încărcat din formatul SavedModel")
                except Exception as e2:
                    logger.warning(f"Încărcarea din format SavedModel a eșuat: {e2}")
                    # Vom funcționa fără model, doar cu căutare directă
                    logger.info("Vom folosi doar căutarea directă")
                    self.model = None
            
            # Chiar dacă modelul nu se încarcă, serviciul poate funcționa parțial
            if not hasattr(self, 'model') or self.model is None:
                logger.warning("AVERTISMENT: Modelul nu a fost încărcat, vom folosi doar căutarea directă")
                self.model_loaded = False
            
        except Exception as e:
            logger.error(f"Eroare la încărcarea componentelor: {e}")
            self.model_loaded = False
    
    def normalize_street(self, street_name):
        """Normalizează numele străzii pentru a face potrivirea mai robustă"""
        if not street_name:
            return ''
        
        # Convertim la lowercase și eliminăm spațiile de la început și sfârșit
        result = str(street_name).lower().strip()
        
        # Înlocuim diacriticele
        mapping = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
            'Ă': 'a', 'Â': 'a', 'Î': 'i', 'Ș': 's', 'Ț': 't'
        }
        for k, v in mapping.items():
            result = result.replace(k, v)
        
        return result
    
    def preprocess_text(self, text):
        """
        Preprocesează textul pentru predicție
        """
        # Convertire la lowercase
        text = str(text).lower()
        
        # Eliminare caractere speciale și diacritice
        text = re.sub(r'[^\w\s]', ' ', text)
        mapping = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
            'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
        }
        for k, v in mapping.items():
            text = text.replace(k, v)
        
        return ' '.join(text.split())
    
    def extract_street_name(self, address):
        """
        Extrage numele străzii din adresă
        """
        street_patterns = [
            r'(strada|str\.)\s+([^,\d]+)',
            r'(bulevardul|bd\.)\s+([^,\d]+)',
            r'(aleea)\s+([^,\d]+)',
            r'(calea)\s+([^,\d]+)'
        ]
        
        for pattern in street_patterns:
            match = re.search(pattern, address.lower())
            if match:
                return match.group(2).strip()
        
        return None
    
    def find_voting_section(self, judet, uat, adresa, section_selection=None):
        """
        Găsește secția de votare pentru un utilizator pe baza adresei
        
        Parametri:
        judet -- codul județului (ex: AB, B, CJ)
        uat -- unitatea administrativ-teritorială (ex: MUNICIPIUL ALBA IULIA)
        adresa -- adresa utilizatorului
        section_selection -- (opțional) indexul secției selectate în cazul multiplelor opțiuni
        """
        try:
            # Verificăm dacă avem un județ și un UAT valid
            if not judet or not uat:
                return {
                    'error': True,
                    'message': 'Județul și UAT-ul sunt obligatorii'
                }
                
            # Normalizăm datele de intrare
            judet = judet.strip().upper()
            uat = uat.strip().upper()
            adresa = adresa.strip()
            
            # Logare pentru debugging
            logger.info(f"Căutare secție pentru: {judet}, {uat}, {adresa}")
            
            # 1. Încercăm mai întâi căutarea directă după numele străzii
            street_name = self.extract_street_name(adresa)
            if street_name:
                logger.info(f"Nume stradă extras: '{street_name}'")
                
                # Generăm diferite variante ale numelui străzii pentru căutare
                street_variants = [
                    f"Strada {street_name}",
                    f"Strada {street_name.capitalize()}",
                    street_name,
                    street_name.capitalize()
                ]
                
# 1.1 Prima încercare: potrivire exactă cu una din variante
                if hasattr(self, 'street_to_section_map'):
                    for street_variant in street_variants:
                        key = (judet, uat, street_variant)
                        if key in self.street_to_section_map:
                            sections = self.street_to_section_map[key]
                            if sections:
                                # Verifică dacă sunt mai multe secții pentru această arteră
                                if len(sections) > 1:
                                    # Dacă s-a specificat o selecție, returnăm secția selectată
                                    if section_selection is not None and 0 <= section_selection < len(sections):
                                        section_data = sections[section_selection]
                                        logger.info(f"Secție selectată manual: {section_data.get('SEDIU_SV')}")
                                        return {
                                            'success': True,
                                            'method': 'direct_lookup_exact_selected',
                                            'section': {
                                                'section_id': section_data['NR_SV'],
                                                'county': judet,
                                                'city': uat,
                                                'name': section_data.get('SEDIU_SV', 'Necunoscut'),
                                                'address': section_data.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                                'address_desc': section_data.get('ADRESA_SV_DESCRIPTIVA', ''),
                                                'locality': section_data.get('LOCALITATE_COMPONENTA', '')
                                            }
                                        }
                                    else:
                                        # Returnăm toate secțiile pentru ca utilizatorul să aleagă
                                        section_list = []
                                        for idx, section in enumerate(sections):
                                            section_list.append({
                                                'index': idx,
                                                'section_id': section['NR_SV'],
                                                'name': section.get('SEDIU_SV', 'Necunoscut'),
                                                'address': section.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                                'address_desc': section.get('ADRESA_SV_DESCRIPTIVA', ''),
                                                'locality': section.get('LOCALITATE_COMPONENTA', '')
                                            })
                                        
                                        logger.info(f"S-au găsit multiple secții ({len(sections)}) pentru {key[2]}")
                                        return {
                                            'success': True,
                                            'method': 'direct_lookup_exact_multiple',
                                            'multiple_sections': True,
                                            'sections': section_list,
                                            'street': key[2]
                                        }
                                else:
                                    # Avem o singură secție
                                    section_data = sections[0]
                                    logger.info(f"Secție găsită prin potrivire exactă: {section_data.get('SEDIU_SV')}")
                                    return {
                                        'success': True,
                                        'method': 'direct_lookup_exact',
                                        'section': {
                                            'section_id': section_data['NR_SV'],
                                            'county': judet,
                                            'city': uat,
                                            'name': section_data.get('SEDIU_SV', 'Necunoscut'),
                                            'address': section_data.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                            'address_desc': section_data.get('ADRESA_SV_DESCRIPTIVA', ''),
                                            'locality': section_data.get('LOCALITATE_COMPONENTA', '')
                                        }
                                    }
                
                # 1.2 A doua încercare: potrivire normalizată
                if hasattr(self, 'using_normalization') and self.using_normalization:
                    for street_variant in street_variants:
                        normalized_key = (judet, uat, self.normalize_street(street_variant))
                        if normalized_key in self.normalized_street_map:
                            original_key = self.normalized_street_map[normalized_key]
                            sections = self.street_to_section_map[original_key]
                            if sections:
                                # Verifică dacă sunt mai multe secții pentru această arteră
                                if len(sections) > 1:
                                    # Dacă s-a specificat o selecție, returnăm secția selectată
                                    if section_selection is not None and 0 <= section_selection < len(sections):
                                        section_data = sections[section_selection]
                                        logger.info(f"Secție selectată manual (normalizat): {section_data.get('SEDIU_SV')}")
                                        return {
                                            'success': True,
                                            'method': 'direct_lookup_normalized_selected',
                                            'section': {
                                                'section_id': section_data['NR_SV'],
                                                'county': judet,
                                                'city': uat,
                                                'name': section_data.get('SEDIU_SV', 'Necunoscut'),
                                                'address': section_data.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                                'address_desc': section_data.get('ADRESA_SV_DESCRIPTIVA', ''),
                                                'locality': section_data.get('LOCALITATE_COMPONENTA', '')
                                            }
                                        }
                                    else:
                                        # Returnăm toate secțiile pentru ca utilizatorul să aleagă
                                        section_list = []
                                        for idx, section in enumerate(sections):
                                            section_list.append({
                                                'index': idx,
                                                'section_id': section['NR_SV'],
                                                'name': section.get('SEDIU_SV', 'Necunoscut'),
                                                'address': section.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                                'address_desc': section.get('ADRESA_SV_DESCRIPTIVA', ''),
                                                'locality': section.get('LOCALITATE_COMPONENTA', '')
                                            })
                                        
                                        logger.info(f"S-au găsit multiple secții normalizate ({len(sections)}) pentru {original_key[2]}")
                                        return {
                                            'success': True,
                                            'method': 'direct_lookup_normalized_multiple',
                                            'multiple_sections': True,
                                            'sections': section_list,
                                            'street': original_key[2]
                                        }
                                else:
                                    # Avem o singură secție
                                    section_data = sections[0]
                                    logger.info(f"Secție găsită prin potrivire normalizată: {section_data.get('SEDIU_SV')}")
                                    return {
                                        'success': True,
                                        'method': 'direct_lookup_normalized',
                                        'section': {
                                            'section_id': section_data['NR_SV'],
                                            'county': judet,
                                            'city': uat,
                                            'name': section_data.get('SEDIU_SV', 'Necunoscut'),
                                            'address': section_data.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                            'address_desc': section_data.get('ADRESA_SV_DESCRIPTIVA', ''),
                                            'locality': section_data.get('LOCALITATE_COMPONENTA', '')
                                        }
                                    }
                
                # 1.3 A treia încercare: potrivire parțială
                if hasattr(self, 'street_to_section_map'):
                    normalized_street_name = self.normalize_street(street_name)
                    matching_sections = []
                    matching_streets = set()  # Pentru a evita duplicate

                    for original_key in self.street_to_section_map.keys():
                        if (original_key[0] == judet and 
                            original_key[1] == uat and 
                            normalized_street_name in self.normalize_street(original_key[2])):
                            
                            matching_streets.add(original_key[2])
                            sections = self.street_to_section_map[original_key]
                            for section in sections:
                                matching_sections.append({
                                    'street': original_key[2],
                                    'section_id': section['NR_SV'],
                                    'name': section.get('SEDIU_SV', 'Necunoscut'),
                                    'address': section.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                    'address_desc': section.get('ADRESA_SV_DESCRIPTIVA', ''),
                                    'locality': section.get('LOCALITATE_COMPONENTA', '')
                                })
                    
                    if matching_sections:
                        # Dacă am găsit mai multe secții potrivite
                        if len(matching_sections) > 1:
                            # Dacă s-a specificat o selecție, returnăm secția selectată
                            if section_selection is not None and 0 <= section_selection < len(matching_sections):
                                section_data = matching_sections[section_selection]
                                logger.info(f"Secție selectată manual (parțial): {section_data.get('name')}")
                                return {
                                    'success': True,
                                    'method': 'direct_lookup_partial_selected',
                                    'section': {
                                        'section_id': section_data['section_id'],
                                        'county': judet,
                                        'city': uat,
                                        'name': section_data.get('name', 'Necunoscut'),
                                        'address': section_data.get('address', 'Adresa nu este disponibilă'),
                                        'address_desc': section_data.get('address_desc', ''),
                                        'locality': section_data.get('locality', ''),
                                        'matched_street': section_data.get('street', '')
                                    }
                                }
                            else:
                                # Returnăm toate secțiile pentru ca utilizatorul să aleagă
                                logger.info(f"S-au găsit {len(matching_sections)} secții pentru potrivire parțială, străzi: {', '.join(list(matching_streets)[:3])}")
                                # Adăugăm indexul pentru fiecare secție
                                for idx, section in enumerate(matching_sections):
                                    section['index'] = idx
                                
                                return {
                                    'success': True,
                                    'method': 'direct_lookup_partial_multiple',
                                    'multiple_sections': True,
                                    'sections': matching_sections,
                                    'street': f"Potriviri parțiale pentru '{street_name}'"
                                }
                        else:
                            # Returnăm singura secție găsită
                            section_data = matching_sections[0]
                            logger.info(f"Secție găsită prin potrivire parțială: {section_data['name']} (pentru {section_data['street']})")
                            return {
                                'success': True,
                                'method': 'direct_lookup_partial',
                                'section': {
                                    'section_id': section_data['section_id'],
                                    'county': judet,
                                    'city': uat,
                                    'name': section_data.get('name', 'Necunoscut'),
                                    'address': section_data.get('address', 'Adresa nu este disponibilă'),
                                    'address_desc': section_data.get('address_desc', ''),
                                    'locality': section_data.get('locality', ''),
                                    'matched_street': section_data.get('street', '')
                                }
                            }
                
                # 1.4 Fallback la metoda veche
                if hasattr(self, 'street_to_section') and not hasattr(self, 'street_to_section_map'):
                    result = self.direct_lookup_old(judet, uat, street_name)
                    if result:
                        logger.info(f"Secție găsită prin metoda veche: {result.get('section', {}).get('name')}")
                        result['method'] = 'direct_lookup_old'
                        return result
            else:
                logger.info("Nu s-a putut extrage numele străzii din adresă")
            
            # 2. Dacă nu am găsit și modelul ML este încărcat, îl folosim
            if self.model_loaded and hasattr(self, 'model') and self.model is not None:
                logger.info("Încercare cu modelul ML...")
                text_input = f"{judet} {uat} {adresa}"
                processed_input = self.preprocess_text(text_input)
                
                try:
                    # Vectorizăm textul
                    input_vec = self.vectorizer.transform([processed_input])
                    
                    # Aplicăm aceiași indici de caracteristici utilizați în antrenare
                    input_vec_small = input_vec[:, self.feature_indices]
                    
                    # Facem predicția
                    if self.is_categorical:
                        prediction_probs = self.model.predict(input_vec_small.toarray())[0]
                        prediction_encoded = np.argmax(prediction_probs)
                    else:
                        # Pentru formatul SavedModel sau regresie
                        if hasattr(self.model, 'predict'):
                            prediction_raw = self.model.predict(input_vec_small.toarray())[0]
                            if isinstance(prediction_raw, np.ndarray) and len(prediction_raw.shape) > 0:
                                prediction_encoded = int(round(prediction_raw[0]))
                            else:
                                prediction_encoded = int(round(prediction_raw))
                        else:
                            # Dacă modelul e SavedModel și nu are predict
                            prediction_raw = self.model(tf.convert_to_tensor(input_vec_small.toarray(), dtype=tf.float32))
                            prediction_encoded = int(round(prediction_raw.numpy()[0][0]))
                    
                    # Ne asigurăm că predicția este în intervalul valid
                    prediction_encoded = max(0, min(prediction_encoded, len(self.label_encoder.classes_) - 1))
                    
                    # Decodificăm rezultatul
                    section_id = self.label_encoder.inverse_transform([prediction_encoded])[0]
                    
                    # Obținem informațiile despre secție
                    if section_id in self.section_details:
                        section_data = self.section_details[section_id]
                        logger.info(f"Secție găsită prin modelul ML: {section_data.get('SEDIU_SV')}")
                        return {
                            'success': True,
                            'method': 'ml_model',
                            'section': {
                                'section_id': section_data['NR_SV'],
                                'county': section_data['JUDET'],
                                'city': section_data['UAT'],
                                'name': section_data.get('SEDIU_SV', 'Necunoscut'),
                                'address': section_data.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                                'address_desc': section_data.get('ADRESA_SV_DESCRIPTIVA', ''),
                                'locality': section_data.get('LOCALITATE_COMPONENTA', '')
                            }
                        }
                except Exception as model_error:
                    logger.error(f"Eroare la utilizarea modelului ML: {model_error}")
                    # Continuăm cu fallback
            
            # 3. Fallback - returnăm o secție din UAT-ul potrivit
            logger.info("Încercare cu metoda fallback...")
            for section_id, details in self.section_details.items():
                if details['JUDET'] == judet and details['UAT'] == uat:
                    logger.info(f"Secție găsită prin fallback: {details.get('SEDIU_SV')}")
                    return {
                        'success': True,
                        'method': 'fallback',
                        'section': {
                            'section_id': details['NR_SV'],
                            'county': details['JUDET'],
                            'city': details['UAT'],
                            'name': details.get('SEDIU_SV', 'Necunoscut'),
                            'address': details.get('ADRESA_SV', 'Adresa nu este disponibilă'),
                            'address_desc': details.get('ADRESA_SV_DESCRIPTIVA', ''),
                            'locality': details.get('LOCALITATE_COMPONENTA', '')
                        }
                    }
            
            # Nu am găsit nicio secție potrivită
            logger.warning(f"Nu s-a găsit nicio secție pentru {judet}, {uat}")
            return {
                'error': True,
                'message': f'Nu s-a găsit nicio secție de votare pentru {judet}, {uat}'
            }
                
        except Exception as e:
            logger.error(f"Eroare generală în find_voting_section: {e}")
            return {
                'error': True,
                'message': f'Eroare la recomandarea secției de votare: {str(e)}'
            }
    
    def direct_lookup_old(self, judet, uat, artera):
        """
        Metoda veche de căutare directă în dicționar
        Păstrată pentru compatibilitate
        """
        key = (judet, uat, artera)
        if key in self.street_to_section:
            info = self.street_to_section[key]
            return {
                'success': True,
                'section': {
                    'section_id': info['NR_SV'],
                    'county': judet,
                    'city': uat,
                    'name': info.get('SEDIU_SV', 'Necunoscut'),
                    'address': info.get('ADRESA_SV', 'Adresa nu este disponibilă')
                }
            }
        
        return None