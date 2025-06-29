# 🚀 VoteAI - Platformă Inteligentă de Vot Electronic cu AI

## 🌟 Descriere Proiect

VoteAI este o platformă inovatoare de votare electronică care integrează tehnologii avansate de inteligență artificială pentru a moderniza procesele electorale din România. Aplicația oferă o alternativă sigură și accesibilă la votul tradițional, fiind deosebit de utilă pentru persoanele cu mobilitate redusă și cetățenii din diaspora.

Sistemul se bazează pe o arhitectură tehnologică complexă care combină recunoașterea facială cu detectarea anti-spoofing pentru autentificarea biometrică a utilizatorilor, procesarea automată a buletinelor românești prin modele YOLO personalizate și identificarea inteligentă a secțiilor de votare.

---

<<<<<<< HEAD
## 📌 Progres Dezvoltare (Iunie 2024 - Iunie 2025)
=======
## 📌 Progres Dezvoltare (Mai 2024 - Iunie 2025)
>>>>>>> a332d14d532ab2630f2357dea9011928667c80ff

### 🔥 Ultimele Actualizări (Iunie 2025)
- ✅ **Recunoaștere facială obligatorie** pentru autentificare cu buletin cu posibilitate de dezactivare
- ✅ **ModelManager singleton** pentru optimizarea modelelor AI și reducerea consumului de memorie
- ✅ **Protecție anti-navigare** cu validare token în AuthGuard
- ✅ **Teste automate complete** pentru Django și Angular

### 🗳️ **Sistem Complet de Vot Electoral**
- **Voturi oficiale**: Prezidențiale (Tur 1 & 2), Parlamentare, Locale
- **Monitorizare video în timp real** cu detectare anti-spoofing
- **Identificare automată secții de vot** prin algoritmi AI
- **Timer de vot** cu alerte progresive (5 minute)
- **Confirmări digitale** cu posibilitate de trimitere PDF pe email

### 🔐 **Securitate și Autentificare Multi-Modal**
- **Autentificare cu buletin**: Procesare automată + verificare biometrică
- **Autentificare clasică**: Email/parolă cu validare prin mail
- **2FA (Two-Factor Authentication)**: TOTP cu Google Authenticator
- **Autentificare socială**: Google și Facebook (în dezvoltare)
- **RECAPTCHA obligatoriu** pentru toate procesele de autentificare
- **Recuperare parolă securizată** cu validări multiple

### 🤖 **Inteligență Artificială Avansată**
- **Model YOLO personalizat** antrenat pe 660 imagini de buletine românești (mAP50: 99.2%)
- **Anti-spoofing detection** cu YOLO specializat pentru detectarea falsificărilor
- **Recunoaștere facială** cu encoding-uri de 128 dimensiuni și prag euclidian 0.6
- **Validare localități** prin similaritatea cosinus și TF-IDF
- **Identificare secții** cu model neural hibrid (căutare directă + ML)

### 🗺️ **Vizualizare Geografică Interactivă**
- **Hărți județe România** cu prezență în timp real
- **Hărți UAT** pentru fiecare județ (ex: BV.geojson, PH.geojson)
- **Hartă internațională** pentru diaspora
- **Statistici live** actualizate la 10 secunde
- **Export CSV** cu date complete de prezență

### 🎯 **Sistem Vot Personalizat**
- **Creare sisteme custom** pentru organizații și comunități
- **Distribuire prin QR codes** și linkuri în rețeaua locală
- **Managementul participanților** prin email cu token-uri temporare
- **Rezultate în timp real** cu grafice Chart.js
- **Aprobare admin** pentru sistemele create

### ♿ **Accesibilitate și Incluziune**
- **Screen reader integrat** cu voce în română pentru toate elementele
- **Navigare completă cu tastatura** prin toate meniurile
- **Personalizare interfață** (contrast, dimensiune text/butoane)
- **Suport pentru persoane cu deficiențe** de vedere și mobilitate

### 📊 **Analize și Raportare**
- **Statistici demografice** pe baza CNP-urilor (vârstă, gen)
- **Analize electorale** cu grafice comparative
- **Prezență în timp real** pe județe și UAT-uri
- **Export complet** în format CSV pentru procesare oficială

### 🛡️ **Monitorizare Securitate**
- **Dashboard securitate** cu scor dinamic și evenimente
- **Device fingerprinting** pentru identificarea dispozitivelor
- **Sesiuni active** cu posibilitatea de terminare în masă
- **Logging complet** al tuturor activităților cu nivele de risc

### 📰 **Funcționalități Complementare**
- **Știri și analize politice** cu articole din baza de date
- **Forum comunitate** cu categorii, subiecte și notificări
- **Candidați prezidențiali și locali** cu informații complete
- **Simulare procese de vot** pentru educație electorală

---

## 🔗 Stack Tehnologic

### **Backend (Django)**
- **Framework**: Django + Django REST Framework
- **Bază de date**: MySQL cu arhitectură 3-Tier
- **Securitate**: JWT tokens, 2FA, CSRF protection
- **AI Integration**: TensorFlow, YOLO, Face Recognition
- **APIs**: RESTful cu autentificare JWT

### **Frontend (Angular)**
- **Framework**: Angular cu TypeScript
- **Styling**: SCSS cu design responsive
- **UI Components**: Angular Material + componente custom
- **Maps**: GeoJSON cu visualizări interactive
- **Real-time**: Polling controlat pentru actualizări live

### **Inteligență Artificială**
- **Computer Vision**: OpenCV pentru procesarea imaginilor
- **Deep Learning**: YOLOv8 personalizat pentru detectarea câmpurilor
- **OCR**: Tesseract cu configurări optimizate pentru română
- **Face Recognition**: Biblioteca face_recognition cu ResNet
- **NLP**: TF-IDF și NLTK pentru procesarea localităților
- **Anti-spoofing**: Model YOLO specializat pentru detectarea falsificărilor

### **Dezvoltare și Testare**
- **Version Control**: Git cu Git LFS pentru fișiere mari
- **Testing**: Django unittest + Angular Jasmine/Karma
- **Training**: Google Colab cu GPU Tesla T4
- **Annotation**: CVAT pentru adnotarea dataset-urilor

### **Web Technologies**
- **Multimedia**: WebRTC pentru capturarea video în timp real
- **Audio**: Web Speech API pentru screen reader
- **Storage**: LocalStorage pentru persistența datelor
- **Security**: SSL/TLS, HTTPS, secure headers

---

## 🧠 Modele AI Dezvoltate

### **1. Detectare Buletine (YOLO)**
- **Dataset**: 660 imagini annotate în CVAT
- **Clase**: 20 câmpuri (CNP, nume, prenume, serie, etc.)
- **Performanță**: mAP50: 99.2%, mAP50-95: 81.9%
- **Viteză**: 10.8ms per imagine

### **2. Anti-Spoofing (YOLO)**
- **Funcție**: Detectarea fotografiilor, ecranelor, măștilor
- **Clasificare**: Binary (fake/real)
- **Preprocesare**: Equalize histogram pentru detectarea artefactelor

### **3. Recunoaștere Facială**
- **Algoritm**: ResNet cu 29 straturi
- **Encoding**: Vectori de 128 dimensiuni
- **Comparare**: Distanța euclidiană cu prag 0.6
- **Features**: 68 puncte de referință faciale

### **4. Identificare Secții Vot**
- **Arhitectură**: Model neural hibrid cu TF-IDF
- **Dataset**: 18,000+ secții din RSV oficial
- **Căutare**: 4 nivele (exactă → normalizată → fuzzy → ML)
- **NLP**: NLTK pentru limba română

---

## 📋 Funcționalități Detaliate

### **Procesul de Vot Oficial**
1. **Verificare eligibilitate** - Validare autentificare cu buletin
2. **Identificare secție** - AI găsește secția pe baza adresei
3. **Monitorizare video** - Supraveghere continuă anti-spoofing
4. **Votare** - Interfețe specifice pentru fiecare tip de scrutin
5. **Confirmare** - Chitanță digitală cu cod de referință

### **Sistem Vot Personalizat**
1. **Creare sistem** - Configurare nume, descriere, perioada
2. **Adăugare opțiuni** - Candidați/alegeri personalizate
3. **Lista participanți** - Gestionare email-uri eligibile
4. **Aprobare admin** - Verificare și activare
5. **Distribuire** - QR codes și linkuri în rețeaua locală
6. **Rezultate live** - Grafice și statistici în timp real

### **Securitate Avansată**
- **Device fingerprinting** cu caracteristici hardware
- **Session management** cu multiple dispozitive
- **Security events** cu nivele de risc (low/medium/high/critical)
- **CAPTCHA attempts** cu statistici complete
- **Activity monitoring** cu alerting automatic

---

## 🔜 Roadmap Dezvoltare

### **Optimizări Imediate**
- [ ] Containerizare Docker completă
- [ ] Optimizarea modelelor AI pentru producție
- [ ] Teste automate pentru toate componentele
- [ ] Performance monitoring și alerting

### **Funcționalități Viitoare**
- [ ] Aplicație mobilă nativă (iOS/Android)
- [ ] Integrare blockchain pentru transparență
- [ ] Suport pentru documente europene
- [ ] API public pentru dezvoltatori
- [ ] Machine learning pentru predicții electorale

### **Scalabilitate**
- [ ] Kubernetes pentru orchestrare
- [ ] Load balancing pentru trafic mare
- [ ] CDN pentru distribuția conținutului
- [ ] Cache distributed pentru performanță

---

## 📊 Metrici și Performanță

### **AI Models Performance**
- **YOLO Buletine**: 99.2% mAP50, 10.8ms inferență
- **Face Recognition**: Prag euclidian 0.6, encoding 128D
- **Anti-spoofing**: Clasificare binară cu preprocessing
- **Secții Vot**: 4-level search cu fallback neural

### **System Statistics**
- **Dataset**: 660+ imagini buletine annotate
- **Localități**: 3,000+ localități românești
- **Secții vot**: 18,000+ secții din RSV oficial
- **Teste**: 56 teste automate (23 Django + 33 Angular)

---

## 🤝 Contribuție și Contact

Proiectul VoteAI este dezvoltat ca cercetare academică pentru modernizarea proceselor electorale prin inteligența artificială. Pentru colaborări sau întrebări tehnice, vă rugăm să deschideți un issue în repository.

---

## 📄 Licență

Acest proiect este dezvoltat în scop educațional și de cercetare pentru procesele democratice moderne.
