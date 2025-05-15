// Actualizare la auth.component.ts
import { Component, ElementRef, ViewChild, Renderer2, OnInit, ChangeDetectorRef, NgZone,ViewEncapsulation  } from '@angular/core';
import { Router, ActivatedRoute, NavigationEnd } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { MatSnackBar, MatSnackBarHorizontalPosition, MatSnackBarVerticalPosition } from '@angular/material/snack-bar';
import * as faceapi from 'face-api.js';
import { environment } from '../../src/environments/environment';


@Component({
  selector: 'app-auth',
  templateUrl: './auth.component.html',
  encapsulation: ViewEncapsulation.None,
  styleUrls: ['./auth.component.scss']
})
export class AuthComponent implements OnInit {
  email: string = '';
  password: string = '';
  cnp: string = '';
  series: string = '';
  firstName: string = '';
  lastName: string = '';
  loginError: boolean = false;
  useIdCardAuth: boolean = false;
  darkMode: boolean = false;
  isCameraOpen: boolean = false;
  capturedImage: string | null = null;
  uploadedImageName: string | null = null;
  isLoading: boolean = false;
  showPassword: boolean = false;

  // proprietati reCAPTCHA
  captchaResponse: string | null = null;
  isCaptchaVerified: boolean = false;
  captchaWidgetId: any = null;
  private recaptchaSiteKey: string = environment.recaptcha.siteKey;
  
  // Face recognition related properties
  isFaceRecognitionActive: boolean = false;
  faceDetected: boolean = false;
  faceMatched: boolean = false;
  faceMatchMessage: string = '';
  faceBoxClass: string = 'face-box-default';
  isProcessingFrame: boolean = false;
  recognitionComplete: boolean = false;
  faceBox: any = null;
  isBlurring: boolean = false;
  showResultIcon: boolean = false;
  hideFaceBox: boolean = false;
  resultIcon: string = '';
  faceDetectionInterval: any = null;
  videoCaptureInterval: any = null;
  videoStream: MediaStream | null = null;

  // Adaugă aceste proprietăți la clasa AuthComponent:
  showTwoFactorForm: boolean = false;
  twoFactorCode: string = '';
  twoFactorEmail: string | null = null;
  twoFactorCNP: string | null = null;
  isTwoFactorProcessing: boolean = false;
  
  @ViewChild('video') videoElement!: ElementRef;

  constructor(
    private authService: AuthService,
    private router: Router,
    private renderer: Renderer2, 
    private snackBar: MatSnackBar,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {
    
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd && this.router.url.includes('/auth')) {
        setTimeout(() => {
          this.reloadCaptcha();
        }, 500);
      }
    });
  }
  

  async ngOnInit() {
    console.log('Initializare componenta auth...');

    //Adaugam functiile de callback reCAPTCHA la window
    (window as any).onCaptchaResolved = (response: string) => this.ngZone.run(() => this.onCaptchaResolved(response));
    (window as any).onCaptchaExpired = () => this.ngZone.run(() => this.onCaptchaExpired());
    (window as any).onCaptchaLoad = () => this.ngZone.run(() => this.renderCaptcha());
    console.log('CAPTCHA script încărcat - forțăm renderizarea imediată');
    this.renderCaptcha();
    setTimeout(() => {
      this.showCaptchaChallenge();
    }, 300);

    this.checkSocialLoginRedirect();
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode) {
      this.darkMode = JSON.parse(savedDarkMode);
      this.applyDarkMode();
    }
    
    // Încărcarea modelelor pentru face-api.js
    try {
      await this.loadFaceApiModels();
    } catch (error) {
      console.error("Eroare la încărcarea modelelor Face API:", error);
    }
    this.loadCaptchaScript();
  } 
  loadCaptchaScript() {
    console.log('Încărcăm script-ul CAPTCHA');
    
    // Eliminăm orice script existent pentru a evita conflicte
    const existingScript = document.querySelector('script[src*="recaptcha/api.js"]');
    if (existingScript) {
      existingScript.remove();
    }
    
    // Adăugăm script-ul cu parametri pentru a forța CAPTCHA v2 vizibil
    const script = document.createElement('script');
    script.src = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=onCaptchaLoad&hl=ro';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    
    console.log('Script CAPTCHA adăugat la document');
  }
    private showMessage(
    message: string, 
    type: 'success' | 'error' | 'warning' | 'info', 
    duration: number = 5000,
    horizontalPosition: MatSnackBarHorizontalPosition = 'center',
    verticalPosition: MatSnackBarVerticalPosition = 'top'
  ) {
    // Define dynamic styling classes based on message type
    const typeClasses = {
      'success': ['success-snackbar', 'bg-green-500', 'text-white'],
      'error': ['error-snackbar', 'bg-red-500', 'text-white'],
      'warning': ['warning-snackbar', 'bg-yellow-500', 'text-black'],
      'info': ['info-snackbar', 'bg-blue-500', 'text-white']
    };

    // Construct icon based on type
    const typeIcons = {
      'success': '✅',
      'error': '❌',
      'warning': '⚠️',
      'info': 'ℹ️'
    };

    // Enhance message with icon and type-specific styling
    const enhancedMessage = `${typeIcons[type]} ${message}`;

    this.snackBar.open(enhancedMessage, 'Închide', {
      duration,
      horizontalPosition,
      verticalPosition,
      panelClass: [
        ...typeClasses[type],
        'custom-snackbar', // Add a base custom class for consistent styling
        'rounded-lg',      // Rounded corners
        'shadow-lg',       // Shadow effect
        'font-medium',     // Medium font weight
        'text-sm',         // Slightly smaller text
        'animate-slide-in' // Optional slide-in animation (you'll need to define this in CSS)
      ]
    });
  }
  
  
    // Reîncarcă widget-ul reCAPTCHA (utilă când avem nevoie să resetăm CAPTCHA)
    resetCaptcha() {
      if ((window as any).grecaptcha && (window as any).grecaptcha.reset) {
        console.log('Resetare reCAPTCHA');
        (window as any).grecaptcha.reset(this.captchaWidgetId || 0);
        this.captchaResponse = null;
        this.isCaptchaVerified = false;
        this.cdr.detectChanges();
        
        // Forțează challenge-ul după resetare
        setTimeout(() => {
          this.showCaptchaChallenge();
        }, 500);
      }
    }
    ngAfterViewInit() {
      // Forțează renderizarea CAPTCHA după ce view-ul este inițializat
      setTimeout(() => {
        this.reloadCaptcha();
      }, 500);
    }
    renderCaptcha() {
      if ((window as any).grecaptcha && (window as any).grecaptcha.render) {
        try {
          console.log('Renderizare explicită reCAPTCHA cu challenge');
          const captchaElement = document.querySelector('.g-recaptcha');
          
          if (captchaElement && !captchaElement.hasChildNodes()) {
            // Stochează ID-ul widget-ului pentru referințe ulterioare
            this.captchaWidgetId = (window as any).grecaptcha.render(captchaElement, {
              'sitekey': this.recaptchaSiteKey,
              'callback': (window as any).onCaptchaResolved,
              'expired-callback': (window as any).onCaptchaExpired,
              'theme': 'light',
              'type': 'image',  // Forțează tipul image pentru challenge
              'size': 'normal',
              'tabindex': '0'
            });
    
            // Forțează executarea manuală a challenge-ului imediat după render
            setTimeout(() => {
              this.showCaptchaChallenge();
            }, 500);
          } else {
            this.resetCaptcha();
            setTimeout(() => {
              this.showCaptchaChallenge();
            }, 300);
          }
        } catch (e) {
          console.error('Eroare la renderizarea reCAPTCHA:', e);
          // Dacă apare o eroare, reîncercăm
          this.reloadCaptcha();
        }
      }
    }
    showCaptchaChallenge() {
      console.log('Forțăm afișarea challenge-ului');
      if ((window as any).grecaptcha && (window as any).grecaptcha.execute) {
        try {
          // Încearcă să execute challenge-ul cu proprietăți specifice pentru forțarea obiectelor
          (window as any).grecaptcha.execute(this.captchaWidgetId || 0, { action: 'login' });
          
          // Adăugăm un hack pentru a força afișarea object challenge-ului
          // Simulăm că este un device mobil pentru a crește șansele de a primi un challenge cu obiecte
          const originalUserAgent = navigator.userAgent;
          Object.defineProperty(navigator, 'userAgent', {
            get: function() { 
              return 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'; 
            },
            configurable: true
          });
          
          // Apelăm metoda de verificare pentru a declanșa challenge-ul
          if ((window as any).___grecaptcha_cfg && (window as any).___grecaptcha_cfg.clients) {
            const clientsKeys = Object.keys((window as any).___grecaptcha_cfg.clients);
            if (clientsKeys.length > 0) {
              try {
                const client = (window as any).___grecaptcha_cfg.clients[clientsKeys[0]];
                // Forțăm afișarea dialog-ului de challenge
                if (client && client.bw && client.bw.send) {
                  client.bw.send('g', { c: true, bv: true, cs: true }); // Trimite semnalul pentru a afișa challenge-ul
                }
              } catch (err) {
                console.error('Eroare la forțarea challenge-ului:', err);
              }
            }
          }
          
          // Restaurăm user agent-ul original
          Object.defineProperty(navigator, 'userAgent', {
            get: function() { return originalUserAgent; },
            configurable: true
          });
        } catch (e) {
          console.error('Eroare la executarea challenge-ului:', e);
        }
      }
    }

    reloadCaptcha() {
      console.log('Reîncărcăm reCAPTCHA');
      
      // Eliminăm widget-ul vechi
      const container = document.querySelector('.captcha-container');
      const oldWidget = document.querySelector('.g-recaptcha-response');
      
      if (oldWidget) {
        try {
          this.resetCaptcha();
        } catch (e) {
          console.error('Eroare la resetarea CAPTCHA:', e);
          
          // Dacă resetarea nu funcționează, forțăm reîncărcarea scriptului
          const existingScript = document.querySelector('script[src*="recaptcha/api.js"]');
          if (existingScript) {
            existingScript.remove();
          }
          
          // Adăugăm parametrii suplimentari pentru a forța challenge-ul cu imagini
          // Recreăm div-ul g-recaptcha
          const captchaDiv = document.querySelector('.g-recaptcha');
          if (captchaDiv) {
            const parentNode = captchaDiv.parentNode;
            const newCaptchaDiv = document.createElement('div');
            newCaptchaDiv.className = 'g-recaptcha';
            newCaptchaDiv.setAttribute('data-sitekey', this.recaptchaSiteKey);
            newCaptchaDiv.setAttribute('data-callback', 'onCaptchaResolved');
            newCaptchaDiv.setAttribute('data-expired-callback', 'onCaptchaExpired');
            newCaptchaDiv.setAttribute('data-theme', 'light');
            newCaptchaDiv.setAttribute('data-type', 'image');  // Forțează tipul image
            newCaptchaDiv.setAttribute('data-size', 'normal');
            newCaptchaDiv.setAttribute('data-tabindex', '0');
            
            if (parentNode) {
              parentNode.replaceChild(newCaptchaDiv, captchaDiv);
            }
          }
          
          // Reîncărcăm scriptul cu parametri pentru a forța recaptcha v2 cu challenge explicit
          const script = document.createElement('script');
          script.src = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=onCaptchaLoad';
          script.async = true;
          script.defer = true;
          document.head.appendChild(script);
        }
      } else {
        // Dacă widget-ul nu există deloc, reîncărcăm scriptul
        const script = document.createElement('script');
        script.src = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=onCaptchaLoad';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
      }
      
      // Resetăm starea
      this.captchaResponse = null;
      this.isCaptchaVerified = false;
      this.cdr.detectChanges();
    }
    
    // Callback pentru rezolvarea CAPTCHA
    onCaptchaResolved(response: string) {
      console.log('CAPTCHA rezolvat:', response ? 'Valid' : 'Invalid');
      this.captchaResponse = response;
      this.isCaptchaVerified = !!response;
      this.cdr.detectChanges();
    }
    
    // Callback pentru expirarea CAPTCHA
    onCaptchaExpired() {
      console.log('CAPTCHA expirat');
      this.captchaResponse = null;
      this.isCaptchaVerified = false;
      this.cdr.detectChanges();
    }
  
  // Încarcă modelele necesare pentru face-api.js
  async loadFaceApiModels(): Promise<void> {
    try {
      console.log("Încărcăm modelele Face API...");
      await faceapi.nets.tinyFaceDetector.loadFromUri('./assets/models/tiny_face_detector');
      await faceapi.nets.ssdMobilenetv1.loadFromUri('./assets/models/ssd_mobilenetv1');
      console.log("Modelele Face API au fost încărcate cu succes!");
    } catch (error) {
      console.error("Eroare la încărcarea modelelor Face API:", error);
      throw error;
    }
  }

  private checkSocialLoginRedirect(): void {
    this.route.queryParams.subscribe(params => {
      const code = params['code'];
      const state = params['state'];
  
      // Deduce provider-ul din URL sau parametri
      let provider: string | null = null;
      if (window.location.href.includes('google')) {
        provider = 'google';
      } else if (window.location.href.includes('facebook')) {
        provider = 'facebook';
      }
  
      if (code && provider) {
        this.authService.socialLoginCallback(code, provider).subscribe(
          (response) => {
            localStorage.setItem('access_token', response.access);
            localStorage.setItem('refresh_token', response.refresh);
            this.snackBar.open('Autentificare socială reușită!', 'Închide', { duration: 3000 });
            this.router.navigate(['/menu']);
          },
          (error) => {
            console.error('Eroare la autentificarea socială:', error);
            this.showErrorMessage('Autentificarea socială a eșuat. Încercați din nou.');
            this.router.navigate(['/auth']); // in caz de esec, redirectionam la autentificare
          }
        );
      }
    });
  }
  
  toggleDarkMode() {
    this.darkMode = !this.darkMode;
    localStorage.setItem('darkMode', JSON.stringify(this.darkMode));
    this.applyDarkMode();
  }

  private applyDarkMode() {
    if (this.darkMode) {
      this.renderer.addClass(document.body, 'dark-mode');
    } else {
      this.renderer.removeClass(document.body, 'dark-mode');
    }
  }

  onIdCardAuthChange() {
    if (this.useIdCardAuth) {
      console.log('Autentificare prin buletin activată');
    } else {
      console.log('Autentificare standard activată');
      this.stopCamera();
      this.isFaceRecognitionActive = false;
    }
  }


onSubmit(): void {
  console.log('onSubmit apelat, tip autentificare:', this.useIdCardAuth ? 'Buletin' : 'Email');
  
  if (!this.isCaptchaVerified) {
    this.showErrorMessage('Te rugăm să confirmi că nu ești un robot înainte de a continua.');
    this.showCaptchaChallenge();
    return;
  }
  this.isLoading = true;

  if (this.useIdCardAuth) {
    if (!this.cnp || !this.series || !this.firstName || !this.lastName) {
      this.showErrorMessage('Toate câmpurile pentru autentificare prin buletin sunt obligatorii.');
      this.isLoading = false;
      return;
    }

    const idCardAuthData = {
      cnp: this.cnp,
      id_series: this.series,
      first_name: this.firstName,
      last_name: this.lastName
    };

    console.log('Trimit date pentru autentificare cu buletin:', idCardAuthData);

    this.authService.loginWithIDCard(idCardAuthData).subscribe({
      next: (response: any) => {
        console.log('Răspuns autentificare cu buletin:', response);
        
        // Verifică dacă este necesară autentificarea cu doi factori
        if (response.requires_2fa === true) {
          console.log('Autentificare 2FA necesară pentru buletin');
          this.isLoading = false;
          this.showTwoFactorForm = true;
          this.twoFactorCNP = response.cnp;
          this.twoFactorEmail = null;
          this.showInfoMessage('Este necesară verificarea cu doi factori. Introduceți codul din aplicația de autentificare.');
          return;
        }
        
        console.log('response.access:', response.access ? 'Prezent' : 'Absent');
        console.log('response.refresh:', response.refresh ? 'Prezent' : 'Absent');
        console.log('response.cnp:', response.cnp);
        console.log('response.first_name:', response.first_name);
        console.log('response.last_name:', response.last_name);
        console.log('response.is_active:', response.is_active);
        console.log('response.is_verified_by_id:', response.is_verified_by_id);
        
        if (response.access && response.refresh) {
          localStorage.setItem('access_token', response.access);
          localStorage.setItem('refresh_token', response.refresh);
          
          console.log('Tokenuri salvate în localStorage');
          
          if (response.cnp) {
            localStorage.setItem('user_cnp', response.cnp);
            localStorage.setItem('auth_method', 'id_card'); 
            
            const userData = {
              cnp: response.cnp,
              first_name: response.first_name || '',
              last_name: response.last_name || '',
              is_verified_by_id: response.is_verified_by_id || true,
              is_active: response.is_active || true
            };
            
            localStorage.setItem('user_data', JSON.stringify(userData));
            console.log('Date utilizator salvate:', userData);
          }
          
          setTimeout(() => {
            this.isLoading = false;
            this.showSuccessMessage('Autentificare reușită!');
            
            console.log('Navighez către /menu folosind window.location.href');
            window.location.href = '/menu'; 
          }, 300);
        } else {
          console.error('Lipsesc tokenurile din răspuns', response);
          this.showErrorMessage('Autentificare eșuată: răspuns invalid de la server');
          this.isLoading = false;
        }
      },
      error: (error) => {
        console.error('Autentificare eșuată', error);
        
        if (error.error) {
          console.error('Detalii eroare:', error.error);
        }
        
        if (error.error?.detail) {
          this.showErrorMessage(error.error.detail);
        } else {
          this.showErrorMessage('Autentificarea a eșuat. Verificați datele introduse sau încercați verificarea facială.');
        }
        
        this.isLoading = false;
        this.resetCaptcha();
      }
    });
  } else {
    if (!this.email || !this.password) {
      this.showErrorMessage('Te rugăm să introduci email-ul și parola.');
      this.isLoading = false;
      return;
    }

    console.log('Autentificare cu email și parolă:', this.email);
    
    this.authService.login(this.email, this.password).subscribe({
      next: (response: any) => {
        console.log('Răspuns complet autentificare cu email:', JSON.stringify(response));
        
        // Verifică explicit proprietatea requires_2fa
        console.log('requires_2fa există:', 'requires_2fa' in response);
        console.log('response.requires_2fa:', response.requires_2fa);
        console.log('typeof response.requires_2fa:', typeof response.requires_2fa);
        
        // Verifică explicit existența proprietății requires_2fa și if aceasta este true
        if (response.requires_2fa === true) {
          console.log('Autentificare 2FA necesară pentru email - activez formularul');
          this.isLoading = false;
          this.showTwoFactorForm = true;
          this.twoFactorEmail = response.email;
          this.twoFactorCNP = null;
          this.showInfoMessage('Este necesară verificarea cu doi factori. Introduceți codul din aplicația de autentificare.');
          return;
        }
        
        console.log('response.access:', response.access ? 'Prezent' : 'Absent');
        console.log('response.refresh:', response.refresh ? 'Prezent' : 'Absent');
        console.log('response.email:', response.email);
        
        if (response.access && response.refresh) {
          localStorage.setItem('access_token', response.access);
          localStorage.setItem('refresh_token', response.refresh);
          localStorage.setItem('auth_method', 'email');
          
          console.log('Tokenuri salvate în localStorage');
          
          // Construim obiectul cu datele utilizatorului
          const userData = {
            email: response.email,
            first_name: response.first_name || '',
            last_name: response.last_name || '',
            is_verified_by_id: response.is_verified_by_id || false,
            is_active: response.is_active || true
          };
          
          localStorage.setItem('user_data', JSON.stringify(userData));
          console.log('Date utilizator salvate:', userData);
          
          setTimeout(() => {
            this.isLoading = false;
            this.showSuccessMessage('Autentificare reușită!');
            
            console.log('Navighez către /menu folosind window.location.href');
            window.location.href = '/menu';
          }, 300);
        } else {
          console.error('Lipsesc tokenurile din răspuns', response);
          this.showErrorMessage('Autentificare eșuată: răspuns invalid de la server');
          this.isLoading = false;
        }
      },
      error: (error) => {
        console.error('Autentificare eșuată', error);
        
        if (error.error) {
          console.error('Detalii eroare:', error.error);
        }
        
        if (error.error?.detail) {
          this.showErrorMessage(error.error.detail);
        } else {
          this.showErrorMessage('Autentificarea a eșuat. Verifică email-ul și parola.');
        }
        
        this.isLoading = false;
        this.resetCaptcha();
      }
    });
  }
}

// Metoda pentru verificarea codului 2FA
verifyTwoFactorCode(): void {
  if (!this.twoFactorCode || this.twoFactorCode.length !== 6) {
    this.showErrorMessage('Te rugăm să introduci un cod valid de 6 cifre.');
    return;
  }
  
  this.isTwoFactorProcessing = true;
  console.log('Verificare cod 2FA:', this.twoFactorCode);
  console.log('Email pentru verificare:', this.twoFactorEmail);
  console.log('CNP pentru verificare:', this.twoFactorCNP);
  
  if (this.twoFactorEmail) {
    // Verificare cu email
    this.authService.verifyTwoFactorWithEmail(this.twoFactorEmail, this.twoFactorCode).subscribe({
      next: (response) => {
        this.handleTwoFactorSuccess(response);
      },
      error: (error) => {
        this.handleTwoFactorError(error);
      }
    });
  } else if (this.twoFactorCNP) {
    // Verificare cu CNP
    this.authService.verifyTwoFactorWithCNP(this.twoFactorCNP, this.twoFactorCode).subscribe({
      next: (response) => {
        this.handleTwoFactorSuccess(response);
      },
      error: (error) => {
        this.handleTwoFactorError(error);
      }
    });
  } else {
    this.isTwoFactorProcessing = false;
    this.showErrorMessage('Eroare: Informații lipsă pentru verificarea codului.');
  }
}


// Metoda pentru gestionarea succes verificare 2FA
private handleTwoFactorSuccess(response: any): void {
  console.log('Verificare 2FA reușită:', response);
  this.isTwoFactorProcessing = false;
  
  if (response.access && response.refresh) {
    localStorage.setItem('access_token', response.access);
    localStorage.setItem('refresh_token', response.refresh);
    
    // Salvăm datele utilizatorului
    const userData: any = {};
    
    if (response.email) {
      userData.email = response.email;
      localStorage.setItem('auth_method', 'email');
    }
    
    if (response.cnp) {
      userData.cnp = response.cnp;
      localStorage.setItem('auth_method', 'id_card');
    }
    
    if (response.first_name) userData.first_name = response.first_name;
    if (response.last_name) userData.last_name = response.last_name;
    if (response.is_verified_by_id !== undefined) userData.is_verified_by_id = response.is_verified_by_id;
    if (response.is_active !== undefined) userData.is_active = response.is_active;
    
    localStorage.setItem('user_data', JSON.stringify(userData));
    
    this.showSuccessMessage('Autentificare cu doi factori reușită!');
    
    // Redirecționare către meniu
    setTimeout(() => {
      window.location.href = '/menu';
    }, 1000);
  } else {
    this.showErrorMessage('Eroare: Răspuns invalid de la server.');
  }
}

// Metoda pentru gestionarea erorilor verificare 2FA
private handleTwoFactorError(error: any): void {
  console.error('Eroare verificare 2FA:', error);
  this.isTwoFactorProcessing = false;
  
  // Verifică dacă există un mesaj de eroare specific în răspuns
  if (error.error && typeof error.error === 'object') {
    // Pentru răspunsuri JSON
    if (error.error.error) {
      this.showErrorMessage(error.error.error);
      return;
    } else if (error.error.detail) {
      this.showErrorMessage(error.error.detail);
      return;
    } else if (error.error.message) {
      this.showErrorMessage(error.error.message);
      return;
    }
  } else if (error.error && typeof error.error === 'string') {
    // Pentru răspunsuri text
    this.showErrorMessage(error.error);
    return;
  } else if (error.status === 400) {
    // Dacă nu am găsit un mesaj specific, dar status-ul este 400
    this.showErrorMessage("Cod de verificare invalid. Verificați codul și încercați din nou.");
    return;
  }
  
  // Mesaj generic de eroare dacă nu am găsit nimic specific
  this.showErrorMessage('Verificarea codului a eșuat. Vă rugăm încercați din nou.');
}
cancelTwoFactor(): void {
  this.showTwoFactorForm = false;
  this.twoFactorCode = '';
  this.twoFactorEmail = null;
  this.twoFactorCNP = null;
}
  
  // Metodă pentru afișarea mesajelor de eroare
private showErrorMessage(message: string): void {
  console.error('Afișez eroare:', message);
  
  const snackConfig = {
    duration: 5000,
    panelClass: ['error-snackbar'],
    horizontalPosition: 'center' as MatSnackBarHorizontalPosition,
    verticalPosition: 'top' as MatSnackBarVerticalPosition,
  };
  
  this.snackBar.open(`❌ ${message}`, 'Închide', snackConfig);
}
  
  // Metodă pentru afișarea mesajelor de succes
  private showSuccessMessage(
    message: string, 
    duration: number = 3000,
    horizontalPosition: MatSnackBarHorizontalPosition = 'center',
    verticalPosition: MatSnackBarVerticalPosition = 'top'
  ) {
    this.showMessage(message, 'success', duration, horizontalPosition, verticalPosition);
  }
  private showWarningMessage(
    message: string, 
    duration: number = 4000,
    horizontalPosition: MatSnackBarHorizontalPosition = 'center',
    verticalPosition: MatSnackBarVerticalPosition = 'top'
  ) {
    this.showMessage(message, 'warning', duration, horizontalPosition, verticalPosition);
  }

  private showInfoMessage(
    message: string, 
    duration: number = 3000,
    horizontalPosition: MatSnackBarHorizontalPosition = 'center',
    verticalPosition: MatSnackBarVerticalPosition = 'top'
  ) {
    this.showMessage(message, 'info', duration, horizontalPosition, verticalPosition);
  }

  navigateToRegister() {
    if(!this.isCaptchaVerified){
      this.showErrorMessage('Te rugăm să confirmi că nu ești un robot înainte de a continua!')
      this.showCaptchaChallenge(); // Force the challenge to show
      return;
    }
    this.router.navigate(['/voteapp-front']);
  }

  onFileUpload(event: any): void {
    const file = event.target.files[0];
    if (file) {
        const allowedExtensions = ['jpg', 'jpeg', 'png']; // Extensii permise
        const fileExtension = file.name.split('.').pop().toLowerCase();

        if (!allowedExtensions.includes(fileExtension)) {
            this.showErrorMessage('Tipul fișierului nu este acceptat. Te rugăm să încarci o imagine (jpg, jpeg, png).');
            return;
        }

        this.uploadedImageName = file.name;
        this.capturedImage = null;
        const formData = new FormData();
        formData.append('id_card_image', file);

        console.log('Începem încărcarea imaginii:', file.name);

        this.authService.uploadIDCard(formData).subscribe(
            response => {
                console.log('Răspunsul serverului la încărcare:', response);
                this.snackBar.open('Imaginea a fost încărcată cu succes', 'OK', {
                    duration: 3000,
                    panelClass: ['success-snackbar']
                });
            },
            error => {
                console.error('Eroare la încărcarea imaginii:', error);
                this.showErrorMessage('Eroare la încărcarea imaginii. Te rugăm să încerci din nou.');
            }
        );
    }
  }

  // Deschide camera pentru captura normală (fără recunoaștere facială)
  openCamera() {
    this.closeCamera(); // Închide orice cameră/recunoaștere existentă
    this.isCameraOpen = true;
    this.isFaceRecognitionActive = false;
    
    navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user'
      }
    })
    .then(stream => {
      this.videoStream = stream;
      this.videoElement.nativeElement.srcObject = stream;
      this.videoElement.nativeElement.play();
    })
    .catch(error => {
      this.showErrorMessage('Nu s-a putut accesa camera. Te rugăm să verifici permisiunile.');
    });
  }

  // Metoda pentru pornirea recunoașterii faciale
  startFaceRecognition(): void {
    if (!this.cnp) {
      this.showErrorMessage("Introduceți CNP-ul înainte de verificarea facială.");
      return;
    }

    this.closeCamera(); // închide camera pentru scanare ID
    
    // Oprește camera dacă este deja deschisă
    this.stopCameraIfActive();  
    this.isFaceRecognitionActive = true;
    this.isCameraOpen = false; // Se asigură că UI-ul camerei de scanare e închis
    this.cdr.detectChanges();
  
    setTimeout(() => {
      this.startCamera().then(() => {
        // Nu mai avem nevoie să apelăm startSendingFramesToBackend 
        // deoarece trimiterea se face direct din detectFaces
      });
    }, 0);
  }

  // Oprește camera activă dacă există
  stopCameraIfActive(): void {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }
  }

  // Închide camera simplă
  closeCamera() {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }
    this.isCameraOpen = false;
    this.isFaceRecognitionActive = false;
  }

  // Captură foto simplă
  capturePhoto() {
    const canvas = document.createElement('canvas');
    canvas.width = this.videoElement.nativeElement.videoWidth;
    canvas.height = this.videoElement.nativeElement.videoHeight;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(this.videoElement.nativeElement, 0, 0, canvas.width, canvas.height);
      this.capturedImage = canvas.toDataURL('image/png');
      this.uploadedImageName = null;
      this.closeCamera();
      this.snackBar.open('Imaginea a fost capturată cu succes', 'OK', {
        duration: 3000,
        panelClass: ['success-snackbar']
      });
    }
  }

  deleteImage() {
    this.uploadedImageName = null;
    this.capturedImage = null;
    this.snackBar.open('Imaginea a fost ștearsă', 'OK', {
      duration: 3000
    });
  }
  
  loginWithGoogle() {
    this.isLoading = true;
    setTimeout(() => {
      window.location.href = 'http://localhost:8000/accounts/google/login';
    }, 1000); 
  }

  loginWithFacebook() {
    this.isLoading = true;
    setTimeout(() => {
      window.location.href = 'http://localhost:8000/accounts/facebook/login';
    }, 1000);
  }

  // Metodă pentru a porni camera pentru recunoaștere facială
  async startCamera(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      console.error("Camera nu este suportată pe acest dispozitiv.");
      return;
    }
  
    if (!this.videoElement?.nativeElement) {
      console.error("Eroare: Elementul video nu este disponibil.");
      return;
    }
  
    try {
      console.log("Pornim camera pentru recunoaștere facială...");
      this.faceMatched = false;
      this.faceMatchMessage = '🔍 Se analizează imaginea...';
      this.faceBoxClass = 'face-box-default';
      this.isProcessingFrame = false;
      this.recognitionComplete = false;
  
      this.videoStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        } 
      });
  
      if (this.videoStream) {
        const video = this.videoElement.nativeElement;
        video.srcObject = this.videoStream;
        video.onloadedmetadata = () => {
          video.play();
          this.detectFaces();
        };
        console.log("Camera a fost pornită cu succes!");
      }
    } catch (error) {
      console.error("Eroare la pornirea camerei:", error);
    }
  }

  // Metoda pentru detectarea fețelor și trimiterea lor pentru autentificare
  async detectFaces(): Promise<void> {
    if (!this.videoElement?.nativeElement) {
      console.error("Eroare: videoElement nu este disponibil pentru detecție!");
      return;
    }
  
    const video = this.videoElement.nativeElement;
    // Utilizăm modelul SSD Mobilenet pe care l-am încărcat
    const detectionOptions = {
      minConfidence: 0.5
    };
  
    this.faceDetectionInterval = window.setInterval(async () => {
      try {
        if (this.recognitionComplete) {
          console.log("Recunoaștere completă. Oprim detectarea feței.");
          this.stopFaceDetection();
          return;
        }
  
        const detections = await faceapi.detectAllFaces(video, new faceapi.SsdMobilenetv1Options(detectionOptions));
  
        if (detections && detections.length > 0) {
          if (detections.length > 1) {
            this.faceDetected = false;
            this.faceMatchMessage = '⚠️ S-au detectat multiple fețe! Procesul se va opri.';
            this.faceBoxClass = 'face-match-error';
            
            // Aplicăm blur-ul și păstrăm mesajul vizibil
            this.isBlurring = true;
            this.showResultIcon = true;
            this.resultIcon = '⚠️';
          
            this.cdr.detectChanges();
          
            // După 2 secunde, închidem camera și resetăm totul
            setTimeout(() => {
              this.stopCamera();
              this.isFaceRecognitionActive = false;
              this.isBlurring = false;
              this.showResultIcon = false;
              this.hideFaceBox = false;
              this.stopFaceDetection();
              this.cdr.detectChanges();
            }, 2000);
          
            return;
          }
          
          // O singură față detectată - continuă procesul normal
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
  
          if (!this.faceMatched && !this.isProcessingFrame) {
            this.faceMatchMessage = '✅ Față detectată';
          }
  
          if (!this.faceMatched && !this.isProcessingFrame) {
            this.captureAndSendFrame();
          }
        } else {
          this.faceDetected = false;
          this.faceMatchMessage = '🔍 Se caută fața în cadru...';
        }
  
        this.cdr.detectChanges();
      } catch (error) {
        console.error("Eroare la detecția feței:", error);
      }
    }, 100);
  }

  // Oprește detecția facială
  stopFaceDetection(): void {
    if (this.faceDetectionInterval !== null) {
      clearInterval(this.faceDetectionInterval);
      this.faceDetectionInterval = null;
    }
  }

  // Capturează un cadru și îl trimite pentru recunoaștere
  async captureAndSendFrame(): Promise<void> {
    const canvas = document.createElement('canvas');
    const video = this.videoElement.nativeElement;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (ctx && video) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          this.sendFrameForRecognition(blob);
        }
      }, 'image/jpeg', 0.9);
    }
  }

  // Trimite cadrul pentru recunoaștere facială
// Fixed sendFrameForRecognition method for your component

// Replace the sendFrameForRecognition method in your auth.component.ts file

async sendFrameForRecognition(liveImageBlob: Blob): Promise<void> {
  if (!this.cnp) {
    console.error("Nu există CNP pentru autentificare.");
    this.faceMatchMessage = "Introduceți CNP-ul pentru autentificare!";
    return;
  }

  if (this.isProcessingFrame) {
    return;
  }

  this.isProcessingFrame = true;

  try {
    const formData = new FormData();
    formData.append('cnp', this.cnp);
    formData.append('live_image', liveImageBlob, 'live_capture.jpg');

    this.faceMatchMessage = "🔄 Se verifică identitatea...";
    this.cdr.detectChanges();

    console.log("Trimitere imagine pentru recunoaștere facială...");
    
    this.authService.loginWithFaceRecognition(formData).subscribe({
      next: (response) => {
        console.log("✅ Răspuns primit de la backend:", response);

        this.recognitionComplete = true;
        this.isProcessingFrame = false;

        // Verifică dacă este necesară autentificarea cu doi factori
        if (this.authService.checkTwoFactorRequired(response)) {
          this.faceMatchMessage = "✅ Identificare reușită! Este necesară verificarea cu doi factori.";
          this.faceBoxClass = 'face-match-success';
          this.resultIcon = '✅';
          
          // Arătăm efectul de succes, apoi oprim camera și afișăm formularul 2FA
          setTimeout(() => {
            this.isBlurring = true;
            this.showResultIcon = true;
            this.hideFaceBox = true;
            this.cdr.detectChanges();
          }, 1000);

          setTimeout(() => {
            this.stopCamera();
            this.isFaceRecognitionActive = false;
            this.isBlurring = false;
            this.showResultIcon = false;
            this.hideFaceBox = false;
            this.cdr.detectChanges();
            
            // Afișăm formularul pentru 2FA
            this.showTwoFactorForm = true;
            this.twoFactorCNP = response.cnp;
            this.twoFactorEmail = null;
            this.showInfoMessage('Este necesară verificarea cu doi factori. Introduceți codul din aplicația de autentificare.');
          }, 2000);
          
          return;
        }

        this.faceMatched = true;
        this.faceMatchMessage = "✅ Identificare reușită!";
        this.faceBoxClass = 'face-match-success';
        this.resultIcon = '✅';
        
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        localStorage.setItem('auth_method', 'id_card');
        
        if (response.cnp) {
          localStorage.setItem('user_cnp', response.cnp);
          
          const userData = {
            cnp: response.cnp,
            first_name: response.first_name || '',
            last_name: response.last_name || '',
            is_verified_by_id: response.is_verified_by_id || true,
            is_active: response.is_active || true
          };
          
          localStorage.setItem('user_data', JSON.stringify(userData));
          console.log('Date utilizator salvate:', userData);
        }
        
        this.cdr.detectChanges();

        setTimeout(() => {
          this.isBlurring = true;
          this.showResultIcon = true;
          this.hideFaceBox = true;
          this.cdr.detectChanges();
        }, 1000);

        setTimeout(() => {
          this.stopCamera();
          this.isFaceRecognitionActive = false;
          this.isBlurring = false;
          this.showResultIcon = false;
          this.hideFaceBox = false;
          this.cdr.detectChanges();
          
          console.log("🚀 Navigare către /menu cu tokenuri:", {
            access: localStorage.getItem('access_token')?.substring(0, 20) + '...',
            refresh: localStorage.getItem('refresh_token')?.substring(0, 20) + '...',
            userData: localStorage.getItem('user_data')
          });
          
          window.location.href = '/menu';
        }, 3000);
      },
      error: (error) => {
        console.error("❌ Eroare la recunoaștere:", error);
        this.faceMatched = false;
        
        let errorMessage = "Eroare la recunoaștere!";
        if (error.error && error.error.detail) {
          errorMessage = error.error.detail;
        } else if (typeof error === 'string') {
          errorMessage = error;
        }
        
        this.faceMatchMessage = "❌ " + errorMessage;
        this.faceBoxClass = 'face-match-error';
        this.resultIcon = '❌';

        setTimeout(() => {
          this.isBlurring = true;
          this.showResultIcon = true;
          this.hideFaceBox = true;
          this.cdr.detectChanges();
        }, 1000);

        setTimeout(() => {
          this.stopCamera();
          this.isFaceRecognitionActive = false;
          this.isBlurring = false;
          this.showResultIcon = false;
          this.hideFaceBox = false;
          this.cdr.detectChanges();
        }, 3000);

        this.isProcessingFrame = false;
        this.cdr.detectChanges();
      }
    });
  } catch (error) {
    console.error("Eroare la procesarea imaginii:", error);
    this.faceMatchMessage = "❌ Eroare la procesarea imaginii!";
    this.isProcessingFrame = false;
    this.cdr.detectChanges();
  }
}
togglePasswordVisibility() {
  this.showPassword = !this.showPassword;
}

forgotPassword() {
  // Se verifica intai daca a fost captcha completat
  if (!this.isCaptchaVerified) {
    this.showErrorMessage('Te rugăm să confirmi că nu ești un robot înainte de a continua.');
    // Force show captcha challenge again
    this.showCaptchaChallenge();
    return;
  }
  if (!this.email) {
    this.showErrorMessage('Te rugăm să introduci adresa de email pentru resetarea parolei.');
    return;
  }

  this.isLoading = true;
  this.authService.requestPasswordReset(this.email).subscribe(
    response => {
      this.isLoading = false;
      this.showSuccessMessage(response.message || 'Un cod de resetare a fost trimis pe adresa de email.');
      // Navigăm către verificare cu parametri pentru resetare
      this.router.navigate(['/verify-email'], { 
        queryParams: { 
          reset: 'true', 
          email: this.email 
        } 
      });
    },
    error => {
      this.isLoading = false;
      this.showErrorMessage(error.error?.error || 'A apărut o eroare. Te rugăm să încerci din nou.');
    // Resetam CAPTCHA in caz de eroare
      this.resetCaptcha();
    }
  );
}

  // Oprește camera și toate procesele asociate
  stopCamera(): void {
    console.log("Oprim camera...");
    
    // Oprim intervalele și eliberăm resursele camerei
    if (this.faceDetectionInterval !== null) {
      clearInterval(this.faceDetectionInterval);
      this.faceDetectionInterval = null;
    }
  
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }
  
    if (this.videoElement?.nativeElement) {
      this.videoElement.nativeElement.srcObject = null;
    }
  
    // Resetăm starea afișării
    this.isFaceRecognitionActive = false;
    this.faceDetected = false;
    
    // Păstrăm mesajul final dacă recunoașterea s-a finalizat
    if (!this.recognitionComplete) {
      this.faceMatchMessage = '';
    }
    
    console.log("Camera oprită!");
  }
  ngOnDestroy(): void {
    this.stopCamera();
  }
}