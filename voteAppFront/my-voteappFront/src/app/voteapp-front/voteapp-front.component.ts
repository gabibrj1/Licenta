import { Component, ElementRef, ViewChild, OnInit, Renderer2 } from '@angular/core';
import { UserService } from '../user.service';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AbstractControl, ValidationErrors } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { GdprDialogComponent } from '../gdpr-dialog/gdpr-dialog.component';
import { DeleteConfirmDialogComponent } from "../delete-confirm.dialog/delete-confirm.dialog.component";
import { MatSnackBar } from '@angular/material/snack-bar';


@Component({
  selector: 'app-voteapp-front',
  templateUrl: './voteapp-front.component.html',
  styleUrls: ['./voteapp-front.component.scss']
})
export class VoteappFrontComponent implements OnInit {
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







  @ViewChild('video') videoElement!: ElementRef;
  videoStream!: MediaStream;
  @ViewChild('passwordInput') passwordInput!: ElementRef;


  constructor(
    private userService: UserService, 
    private router: Router,
    private fb: FormBuilder,
    private renderer: Renderer2,
    private dialog: MatDialog,
    private snackBar:MatSnackBar
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

  
  ngOnInit() {
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
  


  
  onFileUpload(event: any): void {
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
        console.error('Eroare la încărcarea imaginii:', error);
        this.autoFillMessage = 'A apărut o eroare la procesarea imaginii.';
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
      return;
    }
  
    // Transformăm calea completă în calea relativă necesară pentru backend
        const croppedPath = this.uploadedImagePath
        .replace('http://127.0.0.1:8000/media/', '')
        .replace(/^\//, '');
  
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
        } else {
          this.autoFillMessage = 'Datele nu au putut fi extrase!';
        }
        this.isLoading = false;
      },
      (error: any) => {
        console.error('Eroare la completarea datelor:', error);
        this.autoFillMessage = 'A apărut o eroare!';
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
  
  
 
  openCamera() {

    if (this.uploadedImagePath) {
      this.deleteImageSilently();
    }
    this.isScanMethod = true;
    this.isUploadMethod = false;

    this.isCameraOpen = true;
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
      this.videoStream = stream;
      this.videoElement.nativeElement.srcObject = stream;
      this.videoElement.nativeElement.play();

      setTimeout(() => {
        this.showRedLine = true; // Variabilă pentru controlul afișării liniei
      }, 500);

      this.updateGuidance();
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
      } else {
        this.autoFillMessage = 'Datele nu au putut fi extrase!';
      }
      this.isLoading = false;
    },
    (error: any) => {
      console.error('Eroare la completarea datelor:', error);
      this.autoFillMessage = 'A apărut o eroare!';
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
    const idRegex = /ROMANIA|CNP|ROU|SERIA|NR/; // Text specific cărților de identitate
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
        this.autoFillMessage = '';
        this.uploadedImagePath = null;
        this.isLoading = false;
        this.idCardForm.reset();
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
} 
