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
    this.uploadedImageName = file.name; 
    this.showAutoFillButton = true; 
  
    const formData = new FormData();
    formData.append('id_card_image', file);
  
    this.userService.uploadIDCardForAutofill(formData).subscribe(
      (response: any) => {
        if (response.data) {
          this.autoFillMessage = 'Datele au fost extrase. Apasă pe Autofill pentru completare!';
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
    this.userService.autoFillFromImage().subscribe(
      (data: any) => {
        this.idCardForm.patchValue({
          cnp: data.cnp,
          series: data.series,
          number: data.number,
          last_name: data.last_name,
          first_name: data.first_name,
          place_of_birth: data.place_of_birth,
          address: data.address,
          issuing_authority: data.issuing_authority,
          sex: data.sex,
          date_of_issue: data.date_of_issue,
          date_of_expiry: data.date_of_expiry
        });
        this.autoFillMessage = 'Date completate automat!';
      },
      (error: any) => {
        console.error('Eroare la completarea automată:', error);
        this.autoFillMessage = 'Nu s-au putut completa automat datele.';
      }
    );
  }


 
  openCamera() {
    this.isCameraOpen = true;
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
      this.videoStream = stream;
      this.videoElement.nativeElement.srcObject = stream;
      this.videoElement.nativeElement.play();
    });
  }

  closeCamera() {
    this.isCameraOpen = false;
    this.videoStream.getTracks().forEach(track => track.stop());
  }


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
    }
  }

 
  deleteImage(): void {
    this.uploadedImageName = null;       
    this.capturedImage = null;           
    this.showAutoFillButton = false;     
    this.autoFillMessage = '';           
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