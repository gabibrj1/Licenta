import { Component, OnInit } from '@angular/core';
import { UserService } from '../user.service';
import { Router, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-verify-email',
  templateUrl: './verify-email.component.html',
  styleUrls: ['./verify-email.component.scss']
})
export class VerifyEmailComponent implements OnInit {
  email: string = '';
  verificationCode: string = '';
  message: string = '';
  isSuccess: boolean = false;
  isResetPassword: boolean = false;
  
  // Pentru resetarea parolei
  resetForm: FormGroup;
  passwordErrors: string[] = [];
  isPasswordValid: boolean = false;
  showPassword: boolean = false;
  showConfirmPassword: boolean = false;
  
  constructor(
    private userService: UserService, 
    private router: Router,
    private route: ActivatedRoute,
    private fb: FormBuilder
  ) {
    this.resetForm = this.fb.group({
      new_password: ['', [
        Validators.required,
        Validators.minLength(6),
        this.requireUppercase,
        this.requireSpecialChar,
        this.requireDigit
      ]],
      confirm_password: ['', Validators.required]
    }, { validator: this.passwordMatchValidator });
  }

  
  ngOnInit() {
    // Verifică parametrii de query
    this.route.queryParams.subscribe(params => {
      this.isResetPassword = params['reset'] === 'true';
      this.email = params['email'] || '';
      
      // Dacă email-ul nu este în parametrii de query, verifică localStorage
      if (!this.email) {
        const storedEmail = localStorage.getItem('verification_email');
        if (storedEmail) {
          this.email = storedEmail;
        }
      }
      
      console.log('Email detectat:', this.email);
      console.log('Reset password mode:', this.isResetPassword);
    });
    this.resetForm.get('new_password')?.valueChanges.subscribe(() => {
      this.validatePassword();
    });
    this.resetForm.get('confirm_password')?.valueChanges.subscribe(() => {
      this.validateConfirmPassword();
    });
  
  }
  validatePassword() {
    const password = this.resetForm.get('new_password')?.value;
    this.passwordErrors = [];
  
    // Verificări de bază pentru complexitatea parolei
    if (!password || password.length < 6) {
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
  
    // Verificări extinse pentru a evita utilizarea părților din email
    if (this.email) {
      const emailLower = this.email.toLowerCase();
      const passwordLower = password.toLowerCase();
      
      // Împărțim email-ul în părți pentru verificări separate
      const emailParts = emailLower.split(/[.@_-]/);
      
      // Verificăm fiecare parte a emailului care are cel puțin 3 caractere
      for (const part of emailParts) {
        if (part.length >= 3 && passwordLower.includes(part)) {
          this.passwordErrors.push(`Parola nu trebuie să conțină părți din adresa de email (${part}).`);
          break;
        }
      }
      
      // Verificăm și alte combinații probabile din email
      // Numele de utilizator întreg (înainte de @)
      const username = emailLower.split('@')[0];
      if (username.length >= 3 && passwordLower.includes(username)) {
        this.passwordErrors.push('Parola nu trebuie să conțină numele de utilizator din email.');
      }
      
      // Verificăm pentru subșiruri mai lungi de 3 caractere din email
      for (let i = 0; i < emailLower.length - 3; i++) {
        const substr = emailLower.substring(i, i + 4); // Verifcăm subșiruri de 4 caractere
        if (passwordLower.includes(substr)) {
          this.passwordErrors.push(`Parola nu trebuie să conțină secvențe din adresa de email (${substr}).`);
          break;
        }
      }
    }
  
    // Verificare pentru repetări de caractere (ex: 'aaa', '111')
    if (/(.)\1{2,}/.test(password)) {
      this.passwordErrors.push('Parola nu trebuie să conțină caractere repetate excesiv.');
    }
  
    // Verificare pentru secvențe alfanumerice (ex: abc123, 123456)
    const sequences = ['abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij', 'ijk', 'jkl', 
                       'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr', 'qrs', 'rst', 'stu', 'tuv', 
                       'uvw', 'vwx', 'wxy', 'xyz', '012', '123', '234', '345', '456', '567', 
                       '678', '789'];
    
    for (const seq of sequences) {
      if (password.toLowerCase().includes(seq)) {
        this.passwordErrors.push('Parola conține secvențe predictibile de caractere.');
        break;
      }
    }
  
    // Verificare pentru parole comune
    const commonPasswords = ['password', '123456', 'qwerty', 'admin', 'welcome', 'parola'];
    if (commonPasswords.includes(password.toLowerCase())) {
      this.passwordErrors.push('Această parolă este prea comună și ușor de ghicit.');
    }
    
    this.isPasswordValid = this.passwordErrors.length === 0;
    this.validateConfirmPassword();
  }
  
  validateConfirmPassword() {
    const password = this.resetForm.get('new_password')?.value;
    const confirmPassword = this.resetForm.get('confirm_password')?.value;
    
    if (password && confirmPassword && password !== confirmPassword) {
      this.resetForm.get('confirm_password')?.setErrors({ mismatch: true });
    } else {
      // Eliminăm eroarea de nepotrivire dacă parolele coincid
      const confirmControl = this.resetForm.get('confirm_password');
      if (confirmControl?.hasError('mismatch')) {
        // Copiem celelalte erori, dacă există
        const errors = {...confirmControl.errors};
        delete errors['mismatch'];
        
        // Dacă nu mai există alte erori, setăm errors la null
        confirmControl.setErrors(Object.keys(errors).length ? errors : null);
      }
    }
  }
  
  requireUppercase(control: any) {
    const password = control.value;
    if (!password || !/[A-Z]/.test(password)) {
      return { 'uppercase': true };
    }
    return null;
  }

  requireSpecialChar(control: any) {
    const password = control.value;
    if (!password || !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return { 'specialChar': true };
    }
    return null;
  }

  requireDigit(control: any) {
    const password = control.value;
    if (!password || !/\d/.test(password)) {
      return { 'digit': true };
    }
    return null;
  }

  passwordMatchValidator(g: FormGroup) {
    return g.get('new_password')?.value === g.get('confirm_password')?.value
      ? null : {'mismatch': true};
  }
  
  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }

  toggleConfirmPasswordVisibility() {
    this.showConfirmPassword = !this.showConfirmPassword;
  }
  // Adaugă în verify-email.component.ts
getPasswordStrength(): { score: number, label: string, color: string } {
  const password = this.resetForm.get('new_password')?.value || '';
  
  if (!password) {
    return { score: 0, label: 'Foarte slabă', color: '#dc3545' };
  }
  
  let score = 0;
  
  // Acordă puncte pentru diferite criterii
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  
  // Penalizări
  if (/(.)\1{2,}/.test(password)) score -= 1;  // Caractere repetate
  
  // Secvențe predictibile
  const sequences = ['abc', 'bcd', 'cde', 'def', '123', '234', '345', '456'];
  for (const seq of sequences) {
    if (password.toLowerCase().includes(seq)) {
      score -= 1;
      break;
    }
  }
  
  // Nu lăsa scorul să fie negativ
  score = Math.max(0, score);
  
  // Mapează scorul la un nivel
  const strengthMap = [
    { score: 0, label: 'Foarte slabă', color: '#dc3545' },
    { score: 1, label: 'Slabă', color: '#dc3545' },
    { score: 2, label: 'Medie', color: '#ffc107' },
    { score: 3, label: 'Bună', color: '#28a745' },
    { score: 4, label: 'Puternică', color: '#28a745' },
    { score: 5, label: 'Foarte puternică', color: '#28a745' }
  ];
  
  return strengthMap[Math.min(score, 5)];
}
  
  verifyCode() {
    if (!this.email) {
      this.message = 'Te rugăm să introduci adresa de email!';
      return;
    }
    
    
    if (!this.verificationCode) {
      this.message = 'Te rugăm să introduci codul de verificare!';
      return;
    }
    
    console.log('Verificare pentru email:', this.email, 'cod:', this.verificationCode);
    
    if (this.isResetPassword) {
      // Verificare pentru resetare parolă
      this.userService.verifyResetCode(this.email, this.verificationCode).subscribe(
        response => {
          this.message = 'Cod verificat cu succes! Poți introduce noua parolă.';
          this.isSuccess = true;
        },
        error => {
          this.message = error.error?.error || 'Cod de verificare incorect!';
          this.isSuccess = false;
        }
      );
    } else {
      // Verificare standard pentru email
      this.userService.verifyEmail(this.email, this.verificationCode).subscribe(
        response => {
          this.message = 'Email verificat cu succes!';
          this.isSuccess = true;
          // Șterge email-ul din localStorage după verificare reușită
          localStorage.removeItem('verification_email');
          setTimeout(() => {
            this.router.navigate(['/auth']);
          }, 2000);
        },
        error => {
          this.message = error.error?.error || 'Cod de verificare incorect!';
          this.isSuccess = false;
        }
      );
    }
  }
  
  goBack(){
    if (this.isResetPassword){
      this.router.navigate(['/auth']);
    }else{
      this.router.navigate(['/voteapp-front']);
    }
  }
  resetPassword() {
    if (this.resetForm.invalid) {
      this.message = 'Te rugăm să completezi corect toate câmpurile.';
      return;
    }
    
    if (this.resetForm.get('new_password')?.value !== this.resetForm.get('confirm_password')?.value) {
      this.message = 'Parolele nu coincid.';
      return;
    }
    
    const newPassword = this.resetForm.get('new_password')?.value;
    
    console.log('Resetare parolă pentru email:', this.email);
    
    this.userService.resetPassword(this.email, this.verificationCode, newPassword).subscribe(
      response => {
        this.message = 'Parola a fost resetată cu succes!';
        this.isSuccess = true;
        setTimeout(() => {
          this.router.navigate(['/auth']);
        }, 2000);
      },
      error => {
        const errorMsg = error.error?.error || 'A apărut o eroare la resetarea parolei.';
        this.message = Array.isArray(errorMsg) ? errorMsg.join(' ') : errorMsg;
        this.isSuccess = false;
      }
    );
  }
  
}