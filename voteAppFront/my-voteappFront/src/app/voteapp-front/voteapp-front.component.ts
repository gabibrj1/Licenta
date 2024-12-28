import { Component, ElementRef, ViewChild, OnInit, Renderer2 } from '@angular/core';
import { UserService } from '../user.service';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AbstractControl, ValidationErrors } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { GdprDialogComponent } from '../gdpr-dialog/gdpr-dialog.component';



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






  @ViewChild('video') videoElement!: ElementRef;
  videoStream!: MediaStream;
  @ViewChild('passwordInput') passwordInput!: ElementRef;


  constructor(
    private userService: UserService, 
    private router: Router,
    private fb: FormBuilder,
    private renderer: Renderer2,
    private dialog: MatDialog,
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

    this.isUploadMethod = true;
    this.isScanMethod = false;
  
    this.uploadedImageName = file.name;
    this.showAutoFillButton = true;
  
    const formData = new FormData();
    formData.append('id_card_image', file);
  
    // Trimite imaginea către backend
    this.userService.uploadIDCardForAutofill(formData).subscribe(
      (response: any) => {
        if (response.file_path) {
          this.autoFillMessage = 'Imaginea a fost procesată. Apasă pe Autofill pentru completare!';
          this.uploadedImagePath = response.file_path; // Salvează calea în backend
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

  
  
  autoFillData(): void {
    if (!this.uploadedImagePath) {
      this.autoFillMessage = 'Încarcă sau capturează o imagine, te rog!';
      return;
    }

    this.isLoading = true;
    this.userService.autoFillFromImage(this.uploadedImagePath).subscribe(
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
  
  


  capturePhoto() {
    const canvas = document.createElement('canvas');
    const targetWidth = 640; // Dimensiunea imaginii pentru YOLO
    const targetHeight = 480;
  
    canvas.width = targetWidth;
    canvas.height = targetHeight;
  
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(this.videoElement.nativeElement, 0, 0, targetWidth, targetHeight);
      this.capturedImage = canvas.toDataURL('image/png');
      this.uploadedImageName = null;
      this.closeCamera();
  
      // Pregătește imaginea pentru backend
      const blob = this.dataURItoBlob(this.capturedImage);
      const formData = new FormData();
      formData.append('camera_image', blob, 'capture.png');
  
      // Trimite imaginea către backend pentru salvare
      this.userService.scanIDCardForAutofill(formData).subscribe(
        (response: any) => {
          if (response.file_path) {
            this.autoFillMessage = 'Imaginea a fost capturată cu succes!';
            this.uploadedImagePath = response.file_path; // Salvează calea pentru Autofill
            this.showAutoFillButton = true; // Activează butonul Autofill
          } else {
            this.autoFillMessage = 'Nu s-a putut salva imaginea.';
            this.showAutoFillButton = false;
          }
        },
        (error) => {
          console.error('Eroare la salvarea imaginii:', error);
          this.autoFillMessage = 'A apărut o eroare la salvarea imaginii.';
          this.showAutoFillButton = false;
        }
      );
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
      this.autoFillMessage = 'Nu există o imagine validă pentru completare.';
      return;
    }
  
    this.isLoading = true;
    this.userService.autoFillFromScan(this.uploadedImagePath).subscribe(
      (data: any) => {
        const extracted = data.extracted_info;
        if (extracted) {
          const valabilitate = extracted.Valabilitate || '';
          const dates = valabilitate.split(' ');
          const dateOfIssue = this.parseRomanianDate(dates[0]);
          const dateOfExpiry = this.parseRomanianDate(dates[1]);
  
          this.idCardForm.patchValue({
            cnp: extracted.CNP || '',
            series: extracted.SERIA || '',
            number: extracted.NR || '',
            last_name: extracted.Nume || '',
            first_name: extracted.Prenume || '',
            place_of_birth: extracted.LocNastere || '',
            address: extracted.Domiciliu || '',
            issuing_authority: extracted.EmisaDe || '',
            sex: extracted.Sex || '',
            date_of_issue: dateOfIssue,
            date_of_expiry: dateOfExpiry,
          });
          this.autoFillMessage = 'Date completate automat din imaginea capturată! Verifică dacă sunt valide!';
        } else {
          this.autoFillMessage = 'Datele nu au putut fi extrase din imagine.';
        }
        this.isLoading = false;
      },
      (error) => {
        console.error('Eroare la completarea automată din scanare:', error);
        this.autoFillMessage = 'A apărut o eroare la completarea automată din scanare.';
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
    this.uploadedImageName = null;       
    this.capturedImage = null;           
    this.showAutoFillButton = false;     
    this.autoFillMessage = '';  
    this.uploadedImagePath = null;  
    this.showAutoFillButton = false;
    this.autoFillMessage = '';
    this.idCardForm.reset();  
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
