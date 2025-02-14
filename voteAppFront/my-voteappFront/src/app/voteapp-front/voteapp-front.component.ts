import { Component, ElementRef, ViewChild, OnInit, Renderer2, AfterViewInit, OnDestroy, ChangeDetectorRef} from '@angular/core';
import { UserService } from '../user.service';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AbstractControl, ValidationErrors } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { GdprDialogComponent } from '../gdpr-dialog/gdpr-dialog.component';
import { DeleteConfirmDialogComponent } from "../delete-confirm.dialog/delete-confirm.dialog.component";
import { MatSnackBar } from '@angular/material/snack-bar';
import { WarningDialogComponent } from '../warning-dialog/warning-dialog.component';
import { animate, style, transition, trigger } from '@angular/animations';
import * as faceapi from 'face-api.js';



@Component({
  selector: 'app-voteapp-front',
  templateUrl: './voteapp-front.component.html',
  styleUrls: ['./voteapp-front.component.scss'],
  animations: [
    trigger('slideInOut', [
      transition(':enter', [
        style({ transform: 'translateX(-100%)' }),
        animate('300ms ease-out', style({ transform: 'translateX(0)' }))
      ]),
      transition(':leave', [
        animate('300ms ease-in', style({ transform: 'translateX(-100%)' }))
      ])
    ])
  ]


})
export class VoteappFrontComponent implements OnInit, AfterViewInit {
  idCardForm: FormGroup;
  registrationForm: FormGroup;
  email: string = '';
  password: string = '';
  confirmPassword: string = '';
  passwordErrors: string[] = [];
  isPasswordValid: boolean = false;
  useIDCard: boolean = false;
  isCameraOpen: boolean = false;
  capturedImage: string | null = null;
  uploadedImageName: string | null = null;
  isSubmittingVote: boolean = false;
  showPassword: boolean = false;
  showConfirmPassword: boolean = false;
  minExpiryDate: Date | null = null;
  darkMode: boolean = false;
  errorMessage: string = '';
  isLoading: boolean = false;
  maxIssueDate = new Date();
  showAutoFillButton = false;
  autoFillMessage = '';
  uploadedImagePath: string | null = null;
  isUploadMethod: boolean = false;
  isScanMethod: boolean = false;
  showRedLine: boolean = false;
  guidanceTimerId: any; // ID-ul pentru setTimeout
  isCameraExpanded: boolean = false;
  currentRotation: number = 0;
  isFlipped: boolean = false;
  suggestions: string[] = [];
  showValidateLocalityButton: boolean = false;
  showSuggestions: boolean = false; 
  isFaceRecognitionActive: boolean = false;
  capturedFaceImage: string | null = null;
  private currentStream: MediaStream | null = null;
  videoStream: MediaStream | null = null;
  private faceDetectionInterval: number | null = null;
  faceMatched: boolean = false;
  faceMatchMessage: string = 'Analizăm imaginea...';
  videoCaptureInterval: any;
  faceDetected = false;
  faceBox = { top: 0, left: 0, width: 0, height: 0 };
  @ViewChild('locationFieldContainer') locationFieldContainer!: ElementRef;
  selectedSuggestion: string | null = null;

  
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('passwordInput') passwordInput!: ElementRef;


  constructor(
    private userService: UserService, 
    private router: Router,
    private fb: FormBuilder,
    private renderer: Renderer2,
    private dialog: MatDialog,
    private snackBar:MatSnackBar,
    private cdr: ChangeDetectorRef
  ) {

    this.registrationForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [
        Validators.required,
        Validators.minLength(6),
        this.requireUppercase,
        this.requireSpecialChar,
        this.requireDigit
      ]],
      confirmPassword: ['', Validators.required]
    }, { validator: this.passwordMatchValidator });
    
    this.idCardForm = this.fb.group({
      cnp: ['', Validators.required],
      series: ['', Validators.required],
      number: ['', Validators.required],
      last_name: ['', Validators.required],
      first_name: ['', Validators.required],
      place_of_birth: ['', Validators.required],
      address: ['', Validators.required],
      issuing_authority: ['', Validators.required],
      sex: ['', Validators.required],
      date_of_issue: ['', Validators.required],
      date_of_expiry: ['', Validators.required]
    });
    
  }
  

  
 async ngOnInit() {
    console.log('Initializare componenta:...');

    //Incarcam modelele Face API inainte de a initia orice proces
    try {
      await this.loadFaceDetectionModels();
    } catch (error) {
      console.error("Eroare la încărcarea modelelor Face API:", error);
    }

    this.registrationForm.get('password')?.valueChanges.subscribe(() => {
      this.validatePassword();
      this.validateConfirmPassword();
      this.isPasswordValid = this.passwordErrors.length === 0;
    });

    this.registrationForm.get('confirmPassword')?.valueChanges.subscribe(() => {
      this.validateConfirmPassword();
    });
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode) {
      this.darkMode = JSON.parse(savedDarkMode);
      this.applyDarkMode();
    }
    this.passwordInput.nativeElement.addEventListener('keyup', () => {
      this.validatePassword();
    });
  }
  async loadFaceDetectionModels(): Promise<void> {
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

  async onIdCardChange() {
    if (this.useIDCard) {
      const dialogRef = this.dialog.open(GdprDialogComponent, { width: '400px' });
      const userAgreed = await dialogRef.afterClosed().toPromise();

      if (!userAgreed) {
        this.useIDCard = false; 
      }
    }
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

  onConfirmPasswordInput() {
    this.validateConfirmPassword();
  }

   
  
  validatePassword() {
    const password = this.registrationForm.get('password')?.value;
    this.passwordErrors = [];

    if (password.length < 6) {
      this.passwordErrors.push('Parola trebuie să aibă cel puțin 6 caractere.');
    }
    if (!/[A-Z]/.test(password)) {
      this.passwordErrors.push('Parola trebuie să conțină cel puțin o literă mare.');
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      this.passwordErrors.push('Parola trebuie să conțină cel puțin un caracter special.');
    }
    if (!/\d/.test(password)) {
      this.passwordErrors.push('Parola trebuie să conțină cel puțin o cifră.');
    }
  }

  validateConfirmPassword() {
    const password = this.registrationForm.get('password')?.value;
    const confirmPassword = this.registrationForm.get('confirmPassword')?.value;

    
    if (password && confirmPassword && password !== confirmPassword) {
      this.registrationForm.get('confirmPassword')?.setErrors({ mismatch: true });
    } else {
      this.registrationForm.get('confirmPassword')?.setErrors(null); 
    }
  }
  


  requireUppercase(control: AbstractControl): { [key: string]: boolean } | null {
    const password = control.value;
    if (!/[A-Z]/.test(password)) {
      return { 'uppercase': true };
    }
    return null;
  }

  requireSpecialChar(control: AbstractControl): { [key: string]: boolean } | null {
    const password = control.value;
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return { 'specialChar': true };
    }
    return null;
  }

  requireDigit(control: AbstractControl): { [key: string]: boolean } | null {
    const password = control.value;
    if (!/\d/.test(password)) {
      return { 'digit': true };
    }
    return null;
  }

  passwordMatchValidator(g: FormGroup) {
    return g.get('password')?.value === g.get('confirmPassword')?.value
      ? null : {'mismatch': true};
  }

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }

  toggleConfirmPasswordVisibility() {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  register() {
    
    if (this.useIDCard) {
      if (this.idCardForm.valid) {
        this.registerWithIDCard();
      }
    } else {
      if (this.registrationForm.valid) {

        const { email, password } = this.registrationForm.value;
        this.userService.register({ email, password }).subscribe(
          (response: any) => {
            alert('Verifică-ți emailul pentru codul de verificare');
            this.router.navigate(['/verify-email']);
          },
          (error: any) => {
            this.errorMessage = error;
            console.error('Eroare la înregistrare', error);
          }
        );
      }
    }
  

  
    this.userService.register({ email: this.email, password: this.password }).subscribe(
      (response: any) => {
        alert('Verifică-ți emailul pentru codul de verificare. Nu răspunde la acel email.');
        this.router.navigate(['/verify-email']);
      },
      (error: any) => {
        console.error('Eroare la înregistrare', error);
      }
    );
  }



  
  onDateOfIssueChange(event: any) {
    const issueDate = new Date(event.value);
    this.minExpiryDate = new Date(issueDate);
    this.minExpiryDate.setDate(this.minExpiryDate.getDate() + 1);
    
    
    const currentExpiryDate = this.idCardForm.get('date_of_expiry')?.value;
    if (currentExpiryDate && new Date(currentExpiryDate) <= issueDate) {
      this.idCardForm.patchValue({
        date_of_expiry: null
      });
    }
  }
  
  registerWithIDCard() {
    if (this.idCardForm.valid) {
      const userData = this.idCardForm.value;
      this.userService.registerWithIDCard(userData).subscribe(
        (response: any) => {
          alert('Te-ai înregistrat cu succes cu buletinul');
          this.router.navigate(['/login']);
        },
        (error: any) => {
          console.error('Eroare la înregistrarea cu buletin', error);
        }
      );
    }
  }

  
  openWarningDialog(): void {
    this.dialog.open(WarningDialogComponent, {
      width: '400px',
      disableClose: false, // Permite utilizatorului să închidă dialogul
    });
  }
  


  
  onFileUpload(event: any): void {
    const dialogRef = this.dialog.open(WarningDialogComponent, { width: '400px' });
    dialogRef.afterClosed().subscribe(() => {
      // Actioneaza dupa inchiderea dialogului
      this.proceedWithFileUpload(event);
    });
  }
  private proceedWithFileUpload(event: any): void {
    this.autoFillMessage = ''; //reseteaza mesajele de eroare
    const file = event.target.files[0];
    if (!file) return;
   

    if (this.isCameraOpen) {
      this.closeCamera();
    }
    if (this.uploadedImagePath) {
      this.deleteImageSilently();
    }
  
    this.isUploadMethod = true;
    this.isScanMethod = false;
    this.stopCamera();
  
    this.uploadedImageName = file.name;
    this.showAutoFillButton = true;
  
    const formData = new FormData();
    formData.append('id_card_image', file);

    this.isLoading = true;
  
    this.userService.uploadIDCardForAutofill(formData).subscribe(
      (response: any) => {
        this.isLoading = false;
        if (response.cropped_image_path) {
          this.autoFillMessage = 'Imaginea a fost procesată. Apasă pe Autofill pentru completare!';
          this.uploadedImagePath = `http://127.0.0.1:8000${response.cropped_image_path}`;
        } else {
          this.autoFillMessage = 'Nu s-au putut extrage datele din imagine.';
        }
      },
      (error: any) => {
        this.isLoading = false;
        console.error('Eroare la încărcarea imaginii:', error);
        if(error.error && error.error.error){
          //afisam mesajul de eroare primit de la backend
          this.autoFillMessage = error.error.error;
        }else{
          this.autoFillMessage = 'Imaginea încărcată nu corespunde unui act de identitate sau calitatea imaginii este prea slabă!';
        }
        this.showAutoFillButton = false;
        this.uploadedImagePath = null;
        event.target.value = '';
      }
    );
  }
  rotateImage(angle: number): void {
    if (this.uploadedImagePath) {
      this.isLoading = true;
      this.userService.rotateImage(this.uploadedImagePath, angle).subscribe({
        next: (response) => {
          // Update the image path for preview, similar to upload logic
          if (response.manipulated_image_path) {
            this.uploadedImagePath = `http://127.0.0.1:8000${response.manipulated_image_path}?t=${new Date().getTime()}`;
            this.autoFillMessage = 'Imaginea a fost rotită cu succes!';
          } else {
            this.autoFillMessage = 'Eroare la actualizarea imaginii rotite.';
          }
          this.isLoading = false;
        },
        error: (error) => {
          this.autoFillMessage = 'Eroare la rotirea imaginii.';
          this.isLoading = false;
        },
      });
    }
  }
  
  flipImage(): void {
    if (this.uploadedImagePath) {
      this.isLoading = true;
      this.userService.flipImage(this.uploadedImagePath).subscribe({
        next: (response) => {
          // Update the image path for preview, similar to upload logic
          if (response.manipulated_image_path) {
            this.uploadedImagePath = `http://127.0.0.1:8000${response.manipulated_image_path}?t=${new Date().getTime()}`;
            this.autoFillMessage = 'Imaginea a fost oglindită cu succes!';
          } else {
            this.autoFillMessage = 'Eroare la actualizarea imaginii oglindite.';
          }
          this.isLoading = false;
        },
        error: (error) => {
          this.autoFillMessage = 'Eroare la oglindirea imaginii.';
          this.isLoading = false;
        },
      });
    }
  }
  

  showSuccessMessage(message: string): void {
    this.snackBar.open(message, 'Închide', {
      duration: 3000,
      horizontalPosition: 'center',
      verticalPosition: 'top',
      panelClass: ['success-snackbar'],
    });
  }

  showErrorMessage(message: string): void {
    this.snackBar.open(message, 'Închide', {
      duration: 3000,
      horizontalPosition: 'center',
      verticalPosition: 'top',
      panelClass: ['error-snackbar'],
    });
  }
  
  autoFillData(): void {
    if (!this.uploadedImagePath) {
      this.autoFillMessage = 'Încarcă sau capturează o imagine, te rog!';
      this.showValidateLocalityButton = false;
      return;
    }
  
    // Transformam calea completa in calea relativa necesara pentru backend
        const croppedPath = this.uploadedImagePath
        .replace('http://127.0.0.1:8000/media/', '')
        .split('?')[0];
  
    this.isLoading = true;
    this.userService.autoFillFromImage(croppedPath).subscribe(
      (data: any) => {
        const extracted = data.extracted_info;
        if (extracted) {
          const cnpDetails = extracted.CNP || {};
          const cnpValue = cnpDetails.value || '';
          const cnpErrors = cnpDetails.errors || [];
          const cnpStatus = cnpDetails.status || '';
  
          if (cnpErrors.length > 0) {
            this.autoFillMessage = `CNP extras: ${cnpValue}. Erori: ${cnpErrors.join(', ')}`;
          } else {
            this.autoFillMessage = `CNP extras: ${cnpValue}. Status: ${cnpStatus}`;
          }
  
          this.idCardForm.patchValue({
            cnp: cnpValue,
            series: extracted.SERIA || '',
            number: extracted.NR || '',
            last_name: extracted.Nume || '',
            first_name: extracted.Prenume || '',
            place_of_birth: extracted.LocNastere || '',
            address: extracted.Domiciliu || '',
            issuing_authority: extracted.EmisaDe || '',
            sex: extracted.Sex || '',
            date_of_issue: this.parseRomanianDate(extracted.Valabilitate?.split(' ')[0]) || '',
            date_of_expiry: this.parseRomanianDate(extracted.Valabilitate?.split(' ')[1]) || ''
          });
          this.autoFillMessage = 'Datele au fost completate cu succes!';
          this.showValidateLocalityButton = true;
        } else {
          this.autoFillMessage = 'Datele nu au putut fi extrase!';
          this.showValidateLocalityButton = false; 

        }
        this.isLoading = false;
      },
      (error: any) => {
        console.error('Eroare la completarea datelor:', error);
        this.autoFillMessage = 'A apărut o eroare!';
        this.showValidateLocalityButton = false; 
        this.isLoading = false;
      }
    );
  }
  
  
  // Utility function to parse Romanian date format (dd.mm.yy or dd.mm.yyyy) into a Date object
  parseRomanianDate(dateString: string): Date | null {
    if (!dateString) return null;
    const parts = dateString.split('.'); // Split by "."
    if (parts.length !== 3) return null;
  
    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1; // Month is zero-indexed in JS Date
    let year = parseInt(parts[2], 10);
  
    // If year is two digits (e.g., 21), assume it's 2000+21 = 2021
    if (year < 100) {
      year += 2000;
    }
  
    return new Date(year, month, day);
  }
  
  
  private stopCameraIfActive(): void {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }
    if (this.videoElement?.nativeElement?.srcObject) {
      this.videoElement.nativeElement.srcObject = null;
    }
  }
  openCamera() {
    const dialogRef = this.dialog.open(WarningDialogComponent, { width: '400px' });
    dialogRef.afterClosed().subscribe(() => {
      this.proceedWithCamera();
    });
  }
  
  private proceedWithCamera(): void {
    if (this.uploadedImagePath) {
      this.deleteImageSilently();
    }
    //Inchide orice camera este deschisa inainte
    this.stopCamera();

    this.isScanMethod = true;
    this.isUploadMethod = false;
    this.isFaceRecognitionActive = false; // Se asigura cu ui-ul camerei pentru face recognition este inchis
  
    // Oprește camera dacă este deja deschisă
    this.stopCameraIfActive();
  
    this.isCameraOpen = true;
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
      this.videoStream = stream;
      this.videoElement.nativeElement.srcObject = stream;
      this.videoElement.nativeElement.play();
  
      setTimeout(() => {
        this.showRedLine = true; // Afișează linia roșie
      }, 500);
  
      this.updateGuidance();
    }).catch((error) => {
      console.error('Eroare la accesarea camerei:', error);
      this.showErrorMessage('Nu s-a putut accesa camera.');
    });
  }

  closeCamera() {
    this.isCameraOpen = false;
    this.isCameraExpanded = false;
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
    }
  
    // Oprește actualizarea mesajelor de guidance
    if (this.guidanceTimerId) {
      clearTimeout(this.guidanceTimerId); // Oprește timer-ul
      this.guidanceTimerId = null; // Resetează ID-ul timerului
    }
  
    // Resetează mesajele de guidance și alte variabile asociate
    this.autoFillMessage = '';
  }
  toggleExpandCamera() {
    this.isCameraExpanded = !this.isCameraExpanded;
  }
  
  capturePhoto(): void { 
    this.autoFillMessage=''
    const canvas = document.createElement('canvas');
    const targetWidth = 640;
    const targetHeight = 480;
  
    canvas.width = targetWidth;
    canvas.height = targetHeight;
  
    const ctx = canvas.getContext('2d');
    if (ctx && this.videoElement?.nativeElement) {
      ctx.drawImage(this.videoElement.nativeElement, 0, 0, targetWidth, targetHeight);
      this.capturedImage = canvas.toDataURL('image/jpg', 0.9);
      this.uploadedImageName = null;
      this.closeCamera();
  
      const blob = this.dataURItoBlob(this.capturedImage);
      const formData = new FormData();
      formData.append('camera_image', blob, 'capture.jpg');
  
      this.isLoading = true;
      this.userService.scanIDCardForAutofill(formData).subscribe({
        next: (response: any) => {
          if (response.cropped_image_path) {
            this.autoFillMessage = 'Imaginea a fost capturată și procesată cu succes!';
            // Store both the relative and full paths
            this.uploadedImagePath = `http://127.0.0.1:8000${response.cropped_image_path}`;
            this.showAutoFillButton = true;
          } else {
            this.autoFillMessage = 'Nu s-a putut detecta cartea de identitate.';
            this.showAutoFillButton = false;
          }
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la procesarea imaginii capturate:', error);
          this.autoFillMessage = 'Imaginea încărcată nu corespunde unui act de identitate!';
          this.showAutoFillButton = false;
          this.isLoading = false;
        }
      });
    }
}
  
dataURItoBlob(dataURI: string): Blob {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}
  

autoFillDataFromScan(): void {
  if (!this.uploadedImagePath) {
    this.autoFillMessage = 'Încarcă sau capturează o imagine, te rog!';
    this.showValidateLocalityButton = false;
    return;
  }

  // Transformăm calea completă în calea relativă necesară pentru backend
      const croppedPath = this.uploadedImagePath
      .replace('http://127.0.0.1:8000/media/', '')
      .replace(/^\//, '');

  this.isLoading = true;
  this.userService.autoFillFromScan(croppedPath).subscribe(
    (data: any) => {
      const extracted = data.extracted_info;
      if (extracted) {
        const cnpDetails = extracted.CNP || {};
        const cnpValue = cnpDetails.value || '';
        const cnpErrors = cnpDetails.errors || [];
        const cnpStatus = cnpDetails.status || '';

        if (cnpErrors.length > 0) {
          this.autoFillMessage = `CNP extras: ${cnpValue}. Erori: ${cnpErrors.join(', ')}`;
        } else {
          this.autoFillMessage = `CNP extras: ${cnpValue}. Status: ${cnpStatus}`;
        }

        this.idCardForm.patchValue({
          cnp: cnpValue,
          series: extracted.SERIA || '',
          number: extracted.NR || '',
          last_name: extracted.Nume || '',
          first_name: extracted.Prenume || '',
          place_of_birth: extracted.LocNastere || '',
          address: extracted.Domiciliu || '',
          issuing_authority: extracted.EmisaDe || '',
          sex: extracted.Sex || '',
          date_of_issue: this.parseRomanianDate(extracted.Valabilitate?.split(' ')[0]) || '',
          date_of_expiry: this.parseRomanianDate(extracted.Valabilitate?.split(' ')[1]) || ''
        });
        this.autoFillMessage = 'Datele au fost completate cu succes!';
        this.showValidateLocalityButton = true;
      } else {
        this.autoFillMessage = 'Datele nu au putut fi extrase!';
        this.showValidateLocalityButton = false;
      }
      this.isLoading = false;
    },
    (error: any) => {
      console.error('Eroare la completarea datelor:', error);
      this.autoFillMessage = 'A apărut o eroare!';
      this.showValidateLocalityButton = false;
      this.isLoading = false;
    }
  );
}


  
  updateGuidance(): void {
    if (!this.isCameraOpen) return;
   
    const guidanceMessages = [
      'Îndepărtează documentul!',
      'Apropie documentul!',
      'Asigură-te că documentul este vizibil complet!',
      'Evită umbrele sau strălucirea!'
    ];
   
    const randomIndex = Math.floor(Math.random() * guidanceMessages.length);
    this.autoFillMessage = guidanceMessages[randomIndex];
   
    // Salvăm ID-ul pentru a putea opri acest setTimeout
    this.guidanceTimerId = setTimeout(() => this.updateGuidance(), 2000);
  }
  
  validateRomanianID(imageData: string): boolean {
    const idRegex = /ROMANIA|CNP|ROU|SERIA|NR/; // Text specific cartilor de identitate
    return idRegex.test(imageData);
  }
 
  deleteImage(): void {
    const dialogRef = this.dialog.open(DeleteConfirmDialogComponent,{
      width:'300px',
      
    })
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        // Utilizatorul a confirmat ștergerea
        this.uploadedImageName = null;
        this.capturedImage = null;
        this.showAutoFillButton = false;
        this.showValidateLocalityButton = false;
        this.autoFillMessage = '';
        this.uploadedImagePath = null;
        this.isLoading = false;
        this.idCardForm.reset();
        this.stopCamera();
      } else {
        // Utilizatorul a anulat ștergerea
        console.log('Ștergerea imaginii a fost anulată.');
      }
    });
  }

  deleteImageSilently(): void {
    this.uploadedImageName = null;
    this.capturedImage = null;
    this.showAutoFillButton = false;
    this.autoFillMessage = '';
    this.uploadedImagePath = null;
    this.isLoading = false; // Opreste spinner-ul daca era activ
    this.idCardForm.reset(); // Reseteaza campurile din formular
    this.stopCamera(); // Inchide camera daca era deschisa
  }
  toggleLocalityValidation(): void {
    if (this.showSuggestions) {
      // If suggestions are currently visible, hide them
      this.showSuggestions = false;
      //this.suggestions = [];
    } else {
      // Otherwise, fetch suggestions and display them
      this.validateLocality();
    }
  }
  
  ngAfterViewInit(): void {
    if (this.isFaceRecognitionActive) {
      setTimeout(() => {
        if (!this.videoElement?.nativeElement) {
          console.error("Eroare: videoElement nu a fost inițializat!");
          return;
        }
        console.log("✅ Elementul video este disponibil:", this.videoElement.nativeElement);
        this.startCamera();
      }, 1000);
    }
  }
  
  handleScroll(): void {
    if (!this.showSuggestions) return; // Exit early if suggestions are not shown

    const locationFieldPosition = this.locationFieldContainer.nativeElement.getBoundingClientRect();
    const viewportHeight = window.innerHeight;

    // Check if the location field is scrolled out of view
    if (locationFieldPosition.bottom < 0 || locationFieldPosition.top > viewportHeight) {
      this.showSuggestions = false; // Hide the suggestions list
    }
  }
  
  validateLocality(): void {
    const locality = this.idCardForm.get('place_of_birth')?.value || '';
    if (!locality) {
      this.showSuggestions = false;
      return;
    }

    this.userService.validateLocality(locality).subscribe(
      (response: any) => {
        if (response.matches && response.matches.length > 0) {
          this.suggestions = response.matches.map(
            (match: any) =>
              `${match.localitate.nume} (${match.localitate.judet}) (încredere: ${(match.similarity * 100).toFixed(2)}%)`
          );
          this.showSuggestions = true;
        } else {
          this.suggestions = [];
          this.showSuggestions = false;
        }
      },
      () => {
        this.suggestions = [];
        this.showSuggestions = false;
      }
    );
  }

  selectSuggestion(suggestion: string): void {
    this.selectedSuggestion = suggestion;
    const localityName = suggestion.split('(')[0].trim();
    this.idCardForm.patchValue({ place_of_birth: localityName });
    this.closeSuggestions();
  }

  isSuggestionSelected(suggestion: string): boolean {
    return this.selectedSuggestion === suggestion;
  }

  closeSuggestions(): void {
    this.showSuggestions = false;
  }

  submitVote() {
    this.isSubmittingVote = true;
    setTimeout(() => {
      this.isSubmittingVote = false;
    }, 2000); 
  }


 
  loginWithGoogle() {
    this.isLoading = true;
    setTimeout(() => {
      window.location.href = 'http://localhost:8000/accounts/google/login/?process=signup';
    }, 1000); 
  }

 
  loginWithFacebook() {
    this.isLoading = true;
    setTimeout(() => {
      window.location.href = 'http://localhost:8000/accounts/facebook/login/?process=signup';
    }, 1000);
  }

  
  async sendForFaceRecognition(liveImageBlob: Blob): Promise<void> {
    if (!this.uploadedImagePath) {
      this.showErrorMessage('Nu există o imagine a buletinului încărcată.');
      return;
    }
  
    this.isLoading = true;
    const formData = new FormData();
  
    try {
      // Așteptăm conversia URL-ului într-un fișier valid
      const idCardFile = await this.fileFromUploadedPath(this.uploadedImagePath);
  
      formData.append('id_card_image', idCardFile);
      formData.append('live_image', liveImageBlob, 'live_capture.jpg');
  
      this.userService.recognizeFace(formData).subscribe({
        next: (response) => {
          this.isLoading = false;
          if (response.match) {
            this.showSuccessMessage('Recunoaștere facială reușită!');
            this.isFaceRecognitionActive = false;
            this.registerWithIDCard();
          } else {
            this.showErrorMessage('Fața nu corespunde cu buletinul.');
          }
        },
        error: (error) => {
          this.isLoading = false;
          this.showErrorMessage(error.error?.message || 'Eroare la recunoașterea feței.');
        }
      });
    } catch (error) {
      console.error("Eroare la conversia imaginii pentru FormData:", error);
      this.showErrorMessage('Eroare la procesarea imaginii.');
      this.isLoading = false;
    }
  }
  
  
  
  
  fileFromUploadedPath(imagePath: string): Promise<File> {
    const cleanPath = imagePath.split('?')[0];  // Elimină orice parametri extra
  
    return fetch(cleanPath)
      .then(res => {
        if (!res.ok) throw new Error("Eroare la descărcarea imaginii");
        return res.blob();
      })
      .then(blob => {
        const fileName = cleanPath.split('/').pop() || 'id_card.jpg';
        return new File([blob], fileName, { type: blob.type });
      })
      .catch(error => {
        console.error("Eroare la conversia imaginii:", error);
        throw error;
      });
  }
    
  dataURItoBlobId(dataURI: string): Blob {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
  }
  
  startFaceRecognition(): void {
    if (!this.uploadedImagePath) {
      this.showErrorMessage("Încarcă mai întâi imaginea buletinului.");
      return;
    }

    this.closeCamera(); // inchide camera pentru scanaer ID
  
    // Oprește camera dacă este deja deschisă
    this.stopCameraIfActive();  
    this.isFaceRecognitionActive = true;
    this.isCameraOpen = false; //Se asigura cu Ui-ul camerei de scanare e inchis
    this.cdr.detectChanges();
  
    setTimeout(() => {
      this.startCamera().then(() => {
        this.startSendingFramesToBackend();  // Trimite cadre video către backend
      });
    }, 0);
  }
  startSendingFramesToBackend(): void {
    if (this.videoCaptureInterval) {
      clearInterval(this.videoCaptureInterval);
    }
  
    this.videoCaptureInterval = setInterval(() => {
      if (this.faceMatched) {
        clearInterval(this.videoCaptureInterval);
        return;
      }
  
      const canvas = document.createElement('canvas');
      const video = this.videoElement.nativeElement;
  
      if (!video || !video.videoWidth || !video.videoHeight) {
        console.error("Eroare la obținerea cadrului video");
        return;
      }
  
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
  
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (blob) {
            this.sendFrameForRecognition(blob);
          }
        }, 'image/jpeg', 0.9);
      }
    }, 2000); // Trimitere cadru la fiecare 2 secunde
  }
  

  async sendFrameForRecognition(liveImageBlob: Blob): Promise<void> {
    if (!this.uploadedImagePath) {
      console.error("Nu există o imagine încărcată pentru buletin.");
      this.faceMatchMessage = "Încărcați mai întâi buletinul!";
      return;
    }
  
    try {
      const formData = new FormData();
  
      // Așteptăm conversia imaginii pentru a obține un `File`
      const idCardFile = await this.fileFromUploadedPath(this.uploadedImagePath);
      
      // Adăugăm fișierele în FormData
      formData.append('id_card_image', idCardFile);
      formData.append('live_image', liveImageBlob, 'live_capture.jpg');
  
      // Trimiterea către backend
      this.userService.recognizeFace(formData).subscribe({
        next: (response) => {
          if (response.match) {
            this.faceMatched = true;
            this.faceMatchMessage = "Identificare reușită!";
          } else {
            this.faceMatched = false;
            this.faceMatchMessage = "Fețele nu corespund!";
          }
        },
        error: () => {
          this.faceMatched = false;
          this.faceMatchMessage = "Eroare la recunoaștere!";
        }
      });
    } catch (error) {
      console.error("Eroare la conversia imaginii:", error);
    }
  }
  
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
      console.log("Pornim camera...");
      this.isFaceRecognitionActive = true;
      this.faceDetected = false;
      this.faceMatched = false;
      this.faceMatchMessage = '🔍 Se analizează imaginea...';

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

  async detectFaces(): Promise<void> {
    if (!this.videoElement?.nativeElement) {
      console.error("Eroare: videoElement nu este disponibil pentru detecție!");
      return;
    }

    const video = this.videoElement.nativeElement;
    const detectionOptions = new faceapi.TinyFaceDetectorOptions({
      inputSize: 512,
      scoreThreshold: 0.5
    });

    this.faceDetectionInterval = window.setInterval(async () => {
      try {
        const detection = await faceapi.detectSingleFace(video, detectionOptions);

        if (detection) {
          this.faceDetected = true;
          const videoRect = video.getBoundingClientRect();
          
          // Calculate scaling factors
          const scaleX = videoRect.width / video.videoWidth;
          const scaleY = videoRect.height / video.videoHeight;

          this.faceBox = {
            top: detection.box.y * scaleY,
            left: detection.box.x * scaleX,
            width: detection.box.width * scaleX,
            height: detection.box.height * scaleY
          };

          this.faceMatchMessage = '✅ Față detectată';
          console.log("Față detectată:", this.faceBox);
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

  stopCamera(): void {
    console.log("Oprim camera...");
    
    if (this.faceDetectionInterval) {
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

    this.isFaceRecognitionActive = false;
    this.faceDetected = false;
    this.faceMatchMessage = '';
    console.log("Camera oprită!");
  }


  
  toggleExpandCameraId(): void {
    this.isCameraExpanded = !this.isCameraExpanded;
  }
  
  captureLiveFace(): void {
    if (!this.videoElement?.nativeElement?.srcObject) {
      this.showErrorMessage('Camera nu este pornită.');
      return;
    }

    const canvas = document.createElement('canvas');
    const video = this.videoElement.nativeElement;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (ctx && video) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      this.capturedFaceImage = canvas.toDataURL('image/jpeg', 0.9);

      fetch(this.capturedFaceImage)
        .then(res => res.blob())
        .then(blob => this.sendForFaceRecognition(blob))
        .catch(error => {
          console.error('Eroare la procesarea imaginii:', error);
          this.showErrorMessage('Eroare la procesarea imaginii capturate.');
        });
    }
  }
  
  ngOnDestroy(): void {
    this.stopCamera();
  }
  
} 
