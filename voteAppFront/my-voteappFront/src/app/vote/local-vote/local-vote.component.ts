import { Component, OnInit, ViewChild, ElementRef, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl } from '@angular/forms';
import { Router } from '@angular/router';
import { LocalVoteService } from '../../services/local-vote.service';
import { VoteMonitoringService } from '../../services/vote-monitoring.service';
import * as faceapi from 'face-api.js';
import { SecurityService } from '../../services/security.service';

@Component({
  selector: 'app-local-vote',
  templateUrl: './local-vote.component.html',
  styleUrls: ['./local-vote.component.scss']
})
export class LocalVoteComponent implements OnInit {
  currentStep = 1; // 1: verificare eligibilitate, 2: confirmare adresă, 3: secție vot, 4: buletinul de vot
  isEligible = false;
  authType = '';
  userInfo: any = null;
  addressForm: FormGroup;
  votingSection: any = null;
  candidates: any = null;
  isLoading = false;
  error = '';
  selectedCandidates: any = {};
  method: string = ''; // Adăugare proprietate pentru metoda de identificare
  countyExamples: string[] = ['B', 'CJ', 'IS', 'CT', 'TM', 'BV']; // Exemple de județe prescurtate
  multipleSections: any[] = []; // Lista de secții multiple
  streetName: string = ''; // Strada pentru care există multiple secții
  showMultipleSections = false; // Flag pentru afișarea paginii de selecție a secției
  matchedStreet: string = ''; // Strada potrivită în caz de potrivire parțială

  // Pentru monitorizarea video
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  videoStream: MediaStream | null = null;
  isMonitoringActive = false;
  faceDetectionInterval: any = null;
  videoCaptureInterval: any = null;
  showMonitoringWarning = false;
  faceDetected = false;
  faceBox: any = null;
  faceMatchMessage = '';
  faceBoxClass = 'face-box-default';
  isProcessingFrame = false;
  securityViolation = false;
  lastVerificationTime = 0;
  verificationInterval = 4000; // Verifică la fiecare 4 secunde
  consecutiveFailures = 0;
  maxConsecutiveFailures = 3;
  showSecurityAlert = false;

  // Timer pentru vot
  timeRemaining: number = 300;
  voteTimerInterval: any = null;
  formattedTimeRemaining: string = '05:00';
  isTimerWarning: boolean = false; // Pentru stilizare galbenă
  isTimerDanger: boolean = false; // Pentru stilizare roșie
  isTimerFlashing: boolean = false; // Pentru animație flash
  showTimerAlert: boolean = false; // Pentru alertele de timp rămas
  timerAlertMessage: string = '';

  stampSound: HTMLAudioElement | null = null;

  // Dialog de confirmare
  showConfirmDialog = false;
  candidatesForConfirmation: any[] = [];
  contactInfo = '';
  sendReceiptEmail = true;
  receiptMethod = 'email';
  confirmationInProgress = false;
  isContactInfoValid = false;
  
  


  constructor(
    private localVoteService: LocalVoteService,
    private voteMonitoringService: VoteMonitoringService,
    private fb: FormBuilder,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private securityService: SecurityService
  ) {
    this.loadStampSound();
    this.addressForm = this.fb.group({
      county: ['', [Validators.required, Validators.maxLength(2), this.countyValidator]],
      city: ['', [Validators.required]],
      address: ['', [Validators.required, this.addressValidator]]
    });

    // Transformă input-ul pentru județ și localitate în litere mari la schimbare
    this.addressForm.get('county')?.valueChanges.subscribe(value => {
      if (value) {
        this.addressForm.get('county')?.setValue(value.toUpperCase(), { emitEvent: false });
      }
    });

    this.addressForm.get('city')?.valueChanges.subscribe(value => {
      if (value) {
        this.addressForm.get('city')?.setValue(value.toUpperCase(), { emitEvent: false });
      }
    });
  }

  // Metodă pentru a încărca sunetul de ștampilă
loadStampSound(): void {
  try {
    this.stampSound = new Audio();
    this.stampSound.src = './assets/sounds/stamp-sound.mp3'; // Asigură-te că acest fișier există
    this.stampSound.load();
  } catch (error) {
    console.error('Eroare la încărcarea sunetului de ștampilă:', error);
  }
}

// Metodă pentru a reda sunetul de ștampilă
playStampSound(): void {
  if (this.stampSound) {
    this.stampSound.currentTime = 0;
    this.stampSound.play().catch(error => {
      console.error('Eroare la redarea sunetului de ștampilă:', error);
    });
  }
}

  // Metodă pentru pornirea timer-ului de vot
startVoteTimer(): void {
  // Resetăm timer-ul și stările asociate
  this.timeRemaining = 300; // 5 minute în secunde
  this.formattedTimeRemaining = '05:00';
  this.isTimerWarning = false;
  this.isTimerDanger = false;
  this.isTimerFlashing = false;
  this.showTimerAlert = false;
  
  // Pornim intervalul pentru actualizarea timer-ului
  this.voteTimerInterval = setInterval(() => {
    this.timeRemaining--;
    this.updateTimerDisplay();
    
    // Verificăm diferite praguri de timp pentru a actualiza stările
    if (this.timeRemaining === 60) { // 1 minut rămas
      this.showTimerNotification('Mai aveți 1 minut pentru a finaliza votul!');
    } else if (this.timeRemaining === 30) { // 30 secunde rămase
      this.showTimerNotification('Atenție! Mai aveți doar 30 de secunde!');
    } else if (this.timeRemaining === 10) { // 10 secunde rămase
      this.showTimerNotification('10 secunde rămase!');
      this.isTimerFlashing = true;
    } else if (this.timeRemaining <= 0) { // Timpul a expirat
      this.handleExpiredTimer();
    }
    
    // Actualizăm stilurile în funcție de timpul rămas
    this.updateTimerStyles();
    
    this.cdr.detectChanges();
  }, 1000);
}

// Metodă pentru oprirea timer-ului
stopVoteTimer(): void {
  if (this.voteTimerInterval) {
    clearInterval(this.voteTimerInterval);
    this.voteTimerInterval = null;
  }
}

// Metodă pentru actualizarea afișării timer-ului în format MM:SS
updateTimerDisplay(): void {
  const minutes = Math.floor(this.timeRemaining / 60);
  const seconds = this.timeRemaining % 60;
  this.formattedTimeRemaining = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Metodă pentru actualizarea stilurilor timer-ului în funcție de timpul rămas
updateTimerStyles(): void {
  if (this.timeRemaining <= 60) { // Sub 1 minut
    this.isTimerWarning = false;
    this.isTimerDanger = true;
  } else if (this.timeRemaining <= 120) { // Sub 2 minute
    this.isTimerWarning = true;
    this.isTimerDanger = false;
  } else {
    this.isTimerWarning = false;
    this.isTimerDanger = false;
  }
}

// Metodă pentru afișarea notificărilor de timer
showTimerNotification(message: string): void {
  this.showTimerAlert = true;
  this.timerAlertMessage = message;
  
  // Ascunde notificarea după 3 secunde
  setTimeout(() => {
    this.showTimerAlert = false;
    this.cdr.detectChanges();
  }, 3000);
}

// Metodă pentru gestionarea expirării timer-ului
handleExpiredTimer(): void {
  this.stopVoteTimer();
  this.error = 'Timpul pentru completarea buletinului de vot a expirat.';
  
  // Afișăm un mesaj de alertă
  alert('Timpul alocat pentru vot a expirat. Veți fi redirecționat înapoi la pagina principală.');
  
  // Redirecționăm utilizatorul către pagina principală
  setTimeout(() => {
    this.router.navigate(['/menu'], { 
      queryParams: { 
        vote_expired: true
      } 
    });
  }, 1000);
}


  // Validator pentru județ
  countyValidator(control: AbstractControl): {[key: string]: any} | null {
    const value = control.value;
    if (value && !/^[A-Z]{1,2}$/.test(value)) {
      return { 'invalidCounty': true };
    }
    return null;
  }
  async waitForVideoElement(): Promise<boolean> {
    if (this.videoElement) {
      return true;
    }
    
    // Așteaptă maxim 2 secunde pentru ca elementul să fie disponibil
    return new Promise((resolve) => {
      let attempts = 0;
      const checkInterval = setInterval(() => {
        attempts++;
        if (this.videoElement) {
          clearInterval(checkInterval);
          resolve(true);
        } else if (attempts > 20) { // 20 * 100ms = 2 secunde
          clearInterval(checkInterval);
          resolve(false);
        }
      }, 100);
    });
  }
  

  // Validator pentru adresă (fără prescurtări)
  addressValidator(control: AbstractControl): {[key: string]: any} | null {
    const value = control.value;
    const abbreviations = /\b(str|nr|bl|sc|ap|et)\b/i;
    
    if (value && abbreviations.test(value)) {
      return { 'abbreviationsNotAllowed': true };
    }
    return null;
  }

  async ngOnInit() {
        this.securityService.logUserAction('access', 'vote_local', {
      vote_type: 'local'
    });
  
    await this.loadFaceDetectionModels();
    this.checkEligibility();
    this.localVoteService.checkUserVoteStatus().subscribe(
      (response) => {
        if (response.has_voted) {
          this.error = response.message;
          // Alternativ, poți redirecționa utilizatorul
          // this.router.navigate(['/menu']);
        }
      },
      (error) => {
        console.error('Error checking vote status:', error);
      }
    );
  }
    
  async loadFaceDetectionModels(): Promise<void> {
    try {
      console.log("Încărcăm modelele Face API pentru monitorizarea votului...");
      await faceapi.nets.tinyFaceDetector.loadFromUri('./assets/models/tiny_face_detector');
      await faceapi.nets.ssdMobilenetv1.loadFromUri('./assets/models/ssd_mobilenetv1');
      console.log("Modelele Face API au fost încărcate cu succes!");
    } catch (error) {
      console.error("Eroare la încărcarea modelelor Face API:", error);
      throw error;
    }
  }

  // Metoda pentru afisarea avertismentului de monitorizare
  showMonitoringConsent(): void {
    this.showMonitoringWarning = true;
  }
  
  // Metodă pentru începerea monitorizării
  startVoteMonitoring(): void {
    console.log("startVoteMonitoring apelat");
    this.isMonitoringActive = true;
    
    // Verificare existență element video
    console.log("videoElement există:", !!this.videoElement);
    if (this.videoElement) {
      console.log("videoElement nativeElement:", !!this.videoElement.nativeElement);
    }
    
    this.startCamera();
  }
  
  // Metodă pentru refuzarea monitorizării
  refuseMonitoring(): void {
    this.showMonitoringWarning = false;
    this.router.navigate(['/menu']);
  }
  
  async startCamera(): Promise<void> {
    console.log("startCamera apelat");
    if (!navigator.mediaDevices?.getUserMedia) {
      console.error("Camera nu este suportată pe acest dispozitiv.");
      return;
    }

    const videoElementAvailable = await this.waitForVideoElement();
    if (!videoElementAvailable) {
      console.error("Elementul video nu a devenit disponibil după așteptare");
      return;
    }
    

    try {
      console.log("Pornim camera pentru monitorizarea votului...");
      this.faceDetected = false;
      this.faceMatchMessage = '🔍 Se verifică identitatea...';
      this.faceBoxClass = 'face-box-default';
      this.isProcessingFrame = false;
      this.consecutiveFailures = 0;

      this.videoStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        } 
      });
      console.log("Stream video obținut:", !!this.videoStream);
      if (this.videoStream) {
        const video = this.videoElement.nativeElement;
        video.srcObject = this.videoStream;
        video.onloadedmetadata = () => {
          video.play();
          this.detectFaces();
          this.startContinuousVerification();
        };
        console.log("Camera a fost pornită cu succes pentru monitorizare!");
      }
    } catch (error) {
      console.error("Eroare la pornirea camerei pentru monitorizare:", error);
    }
  }
  
  detectFaces(): void {
    if (!this.videoElement?.nativeElement) {
      console.error("Eroare: videoElement nu este disponibil pentru detecție!");
      return;
    }

    const video = this.videoElement.nativeElement;
    const detectionOptions = new faceapi.TinyFaceDetectorOptions({
      inputSize: 416,
      scoreThreshold: 0.3
    });

    this.faceDetectionInterval = window.setInterval(async () => {
      if (!this.isMonitoringActive) {
        this.stopFaceDetection();
        return;
      }
      
      try {
        const detections = await faceapi.detectAllFaces(video, detectionOptions);

        if (detections && detections.length > 0) {
          if (detections.length > 1) {
            this.faceDetected = false;
            this.faceMatchMessage = '⚠️ S-au detectat multiple fețe! Aceasta este o încălcare de securitate.';
            this.faceBoxClass = 'face-match-error';
            this.securityViolation = true;
            this.showSecurityAlert = true;
            this.consecutiveFailures++;
            
            if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
              this.handleSecurityViolation('multiple_faces');
            }
            
            this.cdr.detectChanges();
            return;
          }

          const detection = detections[0];
          this.faceDetected = true;
          const videoRect = video.getBoundingClientRect();

          const scaleX = videoRect.width / video.videoWidth;
          const scaleY = videoRect.height / video.videoHeight;

          this.faceBox = {
            top: detection.box.y * scaleY,
            left: detection.box.x * scaleX,
            width: detection.box.width * scaleX,
            height: detection.box.height * scaleY
          };

          if (!this.isProcessingFrame && this.needsVerification()) {
            this.captureAndVerifyFrame();
          }
        } else {
          this.faceDetected = false;
          this.faceMatchMessage = '🔍 Nu se detectează o față în cadru...';
          this.consecutiveFailures++;
          
          if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
            this.handleSecurityViolation('no_face');
          }
        }

        this.cdr.detectChanges();
      } catch (error) {
        console.error("Eroare la detecția feței:", error);
      }
    }, 500);
  }
  
  needsVerification(): boolean {
    const now = Date.now();
    if (now - this.lastVerificationTime > this.verificationInterval) {
      this.lastVerificationTime = now;
      return true;
    }
    return false;
  }
  
  startContinuousVerification(): void {
    // Verificare imediată inițială
    setTimeout(() => {
      this.captureAndVerifyFrame();
    }, 2000);
  }
  
  async captureAndVerifyFrame(): Promise<void> {
    if (this.isProcessingFrame) return;
    this.isProcessingFrame = true;
    
    const canvas = document.createElement('canvas');
    const video = this.videoElement.nativeElement;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (!ctx || !video) {
      this.isProcessingFrame = false;
      return;
    }
    
    try {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (!blob) {
          this.isProcessingFrame = false;
          return;
        }
        
        this.verifyIdentity(blob);
      }, 'image/jpeg', 0.9);
    } catch (e) {
      console.error("Eroare la capturarea cadrului:", e);
      this.isProcessingFrame = false;
    }
  }
  
  verifyIdentity(imageBlob: Blob): void {
    this.faceMatchMessage = '🔄 Se verifică identitatea...';
    this.cdr.detectChanges();
    
    this.voteMonitoringService.verifyVoterIdentity(imageBlob).subscribe({
      next: (response) => {
        this.isProcessingFrame = false;
        
        if (response.num_faces > 1) {
          this.faceMatchMessage = '⚠️ S-au detectat multiple fețe! Aceasta este o încălcare de securitate.';
          this.faceBoxClass = 'face-match-error';
          this.securityViolation = true;
          this.showSecurityAlert = true;
          this.consecutiveFailures++;
          
          if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
            this.handleSecurityViolation('multiple_faces');
          }
        } else if (response.match) {
          this.faceMatchMessage = '✅ Identitate verificată';
          this.faceBoxClass = 'face-match-success';
          this.securityViolation = false;
          this.showSecurityAlert = false;
          this.consecutiveFailures = 0;
        } else {
          this.faceMatchMessage = '❌ ' + response.message;
          this.faceBoxClass = 'face-match-error';
          this.consecutiveFailures++;
          
          if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
            this.handleSecurityViolation('identity_mismatch');
          }
        }
        
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Eroare la verificarea identității:', error);
        this.faceMatchMessage = '❌ Eroare la verificarea identității';
        this.isProcessingFrame = false;
        this.cdr.detectChanges();
      }
    });
  }
  
  handleSecurityViolation(type: string): void {
    // Oprește procesul de vot și redirecționează
    this.stopCamera();
    this.error = 'Încălcare de securitate detectată. Sesiunea de vot a fost întreruptă.';
    
    setTimeout(() => {
      this.router.navigate(['/menu'], { 
        queryParams: { 
          security_violation: true,
          violation_type: type
        } 
      });
    }, 3000);
  }
  
  stopFaceDetection(): void {
    if (this.faceDetectionInterval !== null) {
      clearInterval(this.faceDetectionInterval);
      this.faceDetectionInterval = null;
    }
  }
  
  stopCamera(): void {
    console.log("Oprim camera de monitorizare...");
    
    this.stopFaceDetection();
    
    if (this.videoCaptureInterval) {
      clearInterval(this.videoCaptureInterval);
      this.videoCaptureInterval = null;
    }
  
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }
  
    if (this.videoElement?.nativeElement) {
      this.videoElement.nativeElement.srcObject = null;
    }
    
    this.isMonitoringActive = false;
    this.faceDetected = false;
    console.log("Camera de monitorizare oprită!");
  }

  checkEligibility(): void {
    this.isLoading = true;
    this.localVoteService.checkEligibility().subscribe(
      (response) => {
        this.isLoading = false;
        this.isEligible = response.eligible;
        this.authType = response.auth_type;
        if (response.eligible) {
          this.userInfo = response.user_info;
          this.currentStep = 2; // Trecem la pasul de confirmare adresă
        }
      },
      (error) => {
        this.isLoading = false;
        this.error = 'A apărut o eroare la verificarea eligibilității.';
        console.error('Error checking eligibility:', error);
      }
    );
  }
  selectSection(sectionIndex: number): void {
    this.isLoading = true;
    
    // Adaugăm section_selection la obiectul trimis către backend
    const requestData = {
      ...this.addressForm.value,
      section_selection: sectionIndex
    };
    
    this.localVoteService.findVotingSection(requestData).subscribe(
      (response) => {
        this.isLoading = false;
        this.votingSection = response.section;
        this.method = response.method;
        
        if (response.matched_street) {
          this.matchedStreet = response.matched_street;
        }
        
        this.showMultipleSections = false;
        console.log('Secție selectată manual:', this.votingSection.name);
      },
      (error) => {
        this.isLoading = false;
        this.error = error.error?.error || 'A apărut o eroare la selectarea secției de vot.';
        console.error('Error selecting voting section:', error);
      }
    );
  }
  
  backToAddressForm(): void {
    this.showMultipleSections = false;
    this.currentStep = 2;
  }

  submitAddress(): void {
    if (this.addressForm.valid) {
      this.isLoading = true;
      this.error = ''; // Resetăm mesajul de eroare
      this.method = ''; // Resetăm metoda de identificare
      this.matchedStreet = ''; // Resetăm strada potrivită
      this.multipleSections = []; // Resetăm lista de secții multiple
      this.showMultipleSections = false; // Resetăm flag-ul pentru multiple secții
      
      this.localVoteService.findVotingSection(this.addressForm.value).subscribe(
        (response) => {
          this.isLoading = false;
          
          // Verificăm dacă avem multiple secții
          if (response.multiple_sections) {
            this.multipleSections = response.sections;
            this.streetName = response.street;
            this.method = response.method;
            this.showMultipleSections = true;
            this.currentStep = 3; // Păstrăm pasul 3, dar cu afișare diferită
            console.log('Multiple secții găsite:', this.multipleSections.length);
            return;
          }
          
          // Avem o singură secție
          this.votingSection = response.section;
          this.method = response.method; // Salvează metoda de identificare
          
          // Salvează strada potrivită dacă există
          if (response.matched_street) {
            this.matchedStreet = response.matched_street;
          }
          
          // Adaugă logging pentru metoda AI folosită
          console.log('Metoda AI folosită pentru identificare:', response.method);
          
          this.currentStep = 3; // Trecem la pasul de afișare a secției de vot
        },
        (error) => {
          this.isLoading = false;
          this.error = error.error?.error || 'A apărut o eroare la căutarea secției de vot.';
          console.error('Error finding voting section:', error);
        }
      );
    }
  }

// Cand confirmam sectia de vot si trecem la buletinul de vot, initiem monitorizarea
confirmVotingSection(): void {
  if (this.votingSection) {
    this.isLoading = true;
    
    this.localVoteService.getCandidates(
      this.votingSection.county, 
      this.votingSection.city
    ).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.candidates = response.positions;
        
        if (Object.keys(this.candidates || {}).length === 0) {
          this.error = "Nu există candidați înregistrați pentru această localitate.";
        } else {
          // Afișăm avertismentul de monitorizare înainte de a începe votul
          this.showMonitoringConsent();
        }
      },
      error: (error) => {
        this.isLoading = false;
        this.error = 'A apărut o eroare la încărcarea candidaților: ' + 
                    (error.error?.error || error.message || JSON.stringify(error));
      }
    });
  }
}
// Cand utilizatorul aproba monitorizarea; trecem la buletinul de vot
acceptMonitoring(): void {
  console.log("acceptMonitoring apelat");
  this.showMonitoringWarning = false;
  this.currentStep = 4; // Trecem la buletinul de vot
  setTimeout(() => {
    console.log("Start monitorizare video după delay");
    this.startVoteMonitoring();

    // Pornim timer-ul de vot
    this.startVoteTimer();
  }, 500);
}

ngOnDestroy(): void {
  this.stopCamera();
  this.stopVoteTimer(); 
}
selectCandidate(position: string, candidateId: number): void {
  // Verificăm dacă alegem același candidat sau unul diferit
  const isToggle = this.selectedCandidates[position] === candidateId;
  
  if (isToggle) {
    // Dacă este același candidat, anulăm selecția (un-vote)
    delete this.selectedCandidates[position];
  } else {
    // Selectăm un candidat nou
    this.selectedCandidates[position] = candidateId;
    
    // Redăm sunetul de ștampilă
    this.playStampSound();
    
    // Efect de vibrație ușoară pentru feedback tactil (opțional, pentru dispozitive mobile)
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
  }
  
  // Forțăm detectarea schimbărilor pentru a actualiza interfața imediat
  this.cdr.detectChanges();
}

submitVote(): void {
  if (Object.keys(this.selectedCandidates).length === 0) {
    this.error = 'Trebuie să selectați cel puțin un candidat.';
    return;
  }

  // Extragem informațiile despre candidații selectați pentru confirmare
  this.candidatesForConfirmation = [];
  
  Object.keys(this.selectedCandidates).forEach(positionKey => {
    const candidateId = this.selectedCandidates[positionKey];
    const candidateList = this.candidates[positionKey];
    const candidate = candidateList.find((c: any) => c.id === candidateId);
    
    if (candidate) {
      this.candidatesForConfirmation.push({
        id: candidate.id,
        name: candidate.name,
        party: candidate.party,
        position: this.getPositionLabel(positionKey),
        position_key: positionKey
      });
    }
  });
  
  // Arată dialogul de confirmare cu detaliile candidaților
  this.showConfirmDialog = true;
  
  // Oprim timer-ul când afișăm dialogul de confirmare
  this.stopVoteTimer();
}
validateContactInfo(): void {
  if (this.receiptMethod === 'email') {
    // Verifică email-ul
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    this.isContactInfoValid = emailRegex.test(this.contactInfo);
  } else if (this.receiptMethod === 'sms') {
    // Verifică numărul de telefon (simplificat)
    this.isContactInfoValid = this.contactInfo.length >= 10;
  } else {
    this.isContactInfoValid = false;
  }
}
// Adaugă metoda de confirmare finală
confirmFinalVote(): void {
  // Validează informațiile de contact dacă se dorește primirea confirmării
  if (this.sendReceiptEmail) {
    this.validateContactInfo();
    if (!this.isContactInfoValid) {
      if (this.receiptMethod === 'email') {
        this.error = 'Vă rugăm să introduceți o adresă de email validă.';
      } else {
        this.error = 'Vă rugăm să introduceți un număr de telefon valid.';
      }
      return;
    }
  }

  this.confirmationInProgress = true;
  this.error = '';
  
  // Ne asigurăm că transmitem și detaliul despre poziție (primar, consilier)
  const candidatesToSend = this.candidatesForConfirmation.map(candidate => ({
    id: candidate.id,
    position_key: candidate.position_key, // Folosit în backend pentru a identifica poziția
    name: candidate.name,
    party: candidate.party
  }));
  
  // Pregătește datele pentru cerere
  const requestData = {
    candidates: candidatesToSend,
    voting_section_id: this.votingSection.id,
    send_receipt: this.sendReceiptEmail,
    receipt_method: this.receiptMethod,
    contact_info: this.sendReceiptEmail ? this.contactInfo : '',
    county_code: this.votingSection.county, // Adăugăm și codul județului
    uat: this.votingSection.city // Adăugăm UAT-ul

  };
  
  console.log('Trimit datele pentru confirmare:', requestData);
  
  this.localVoteService.confirmVoteAndSendReceipt(requestData).subscribe({
    next: (response) => {
      this.confirmationInProgress = false;
      this.showConfirmDialog = false;
      
      // Afișează un mesaj de succes
      let message = 'Votul dumneavoastră a fost înregistrat cu succes!';
      if (this.sendReceiptEmail) {
        if (this.receiptMethod === 'email') {
          message += ' O confirmare a fost trimisă la adresa de email furnizată.';
        } else {
          message += ' O confirmare va fi trimisă prin SMS (serviciu momentan indisponibil).';
        }
      }
      
      // Adaugă și mesajele de eroare, dacă există
      if (response.errors && response.errors.length > 0) {
        message += '\n\nAtenție: ' + response.errors.join('\n');
      }
      
      alert(message);
      
      // Redirecționează către pagina principală
      this.router.navigate(['/menu']);
    },
    error: (error) => {
      this.confirmationInProgress = false;
      this.error = error.error?.error || 'A apărut o eroare la înregistrarea votului.';
      if (error.error?.errors && error.error.errors.length > 0) {
        this.error += '\n' + error.error.errors.join('\n');
      }
      console.error('Error submitting vote:', error);
    }
  });
}
// Metoda pentru anularea confirmării
cancelConfirmation(): void {
  this.showConfirmDialog = false;
  this.candidatesForConfirmation = [];
  this.error = '';
  
  // Repornim timer-ul dacă anulăm confirmarea
  this.startVoteTimer();
}
updateReceiptMethod(method: string): void {
  this.receiptMethod = method;
  this.contactInfo = ''; // resetăm informațiile de contact
  this.isContactInfoValid = false;
}



  redirectToIDRegistration(): void {
    this.router.navigate(['/auth'], { queryParams: { mode: 'id_card' }});
  }

  get objectKeys() {
    return Object.keys;
  }

  getPositionLabel(positionKey: string): string {
    const positionLabels: {[key: string]: string} = {
      'mayor': 'Primar',
      'councilor': 'Consilier Local',
      'county_president': 'Președinte Consiliu Județean',
      'county_councilor': 'Consilier Județean'
    };
    
    return positionLabels[positionKey] || positionKey;
  }
  
  // Helper pentru a afișa numele metodei într-un format mai prietenos
// Helper pentru a afișa numele metodei într-un format mai prietenos
getMethodName(methodCode: string): string {
  const methodNames: {[key: string]: string} = {
    'direct_lookup_exact': 'căutare directă',
    'direct_lookup_normalized': 'căutare normalizată',
    'direct_lookup_partial': 'potrivire parțială',
    'direct_lookup_exact_multiple': 'căutare directă (multiple secții)',
    'direct_lookup_normalized_multiple': 'căutare normalizată (multiple secții)',
    'direct_lookup_partial_multiple': 'potrivire parțială (multiple secții)',
    'direct_lookup_exact_selected': 'secție selectată manual',
    'direct_lookup_normalized_selected': 'secție selectată manual',
    'direct_lookup_partial_selected': 'secție selectată manual',
    'direct_lookup': 'căutare directă',
    'ml_model': 'model de inteligență artificială',
    'fallback': 'metodă alternativă',
    'unknown': 'metodă necunoscută'
  };
  
  return methodNames[methodCode] || 'metodă necunoscută';
}

  // Metoda care returnează un județ aleator din lista de exemple
  getRandomCountyExample(): string {
    const randomIndex = Math.floor(Math.random() * this.countyExamples.length);
    return this.countyExamples[randomIndex];
  }
}