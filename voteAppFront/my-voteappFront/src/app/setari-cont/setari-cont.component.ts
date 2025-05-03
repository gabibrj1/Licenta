import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import { SetariContService } from '../services/setari-cont.service';
import { AuthService } from '../services/auth.service';
import { ConfirmDialogComponent } from '../shared/confirm-dialog/confirm-dialog.component';
import { Router } from '@angular/router';

@Component({
  selector: 'app-setari-cont',
  templateUrl: './setari-cont.component.html',
  styleUrl: './setari-cont.component.scss'
})
export class SetariContComponent implements OnInit {
  profileForm!: FormGroup;  // Adăugăm ! pentru a indica inițializarea în constructor
  settingsForm!: FormGroup;
  passwordForm!: FormGroup;
  
  userProfile: any = null;
  userEmail: string | null = null;
  userCNP: string | null = null;
  firstName: string | null = null;
  lastName: string | null = null;
  profileImageUrl: string | null = null;
  authMethod: 'email' | 'id_card' = 'email';
  
  isLoading = false;
  isPasswordVisible = false;
  isCurrentPasswordVisible = false;
  isSubmitting = false;
  activeTab = 'profile';
  
  passwordErrors: string[] = [];
  avatarColor: string = this.getRandomColor();
  
  @ViewChild('fileInput') fileInput!: ElementRef;  // Adăugăm ! pentru a indica că va fi inițializat după ViewInit
  
  constructor(
    private fb: FormBuilder,
    private settingsService: SetariContService,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private router: Router
  ) {
    // Initialize forms
    this.initForms();
  }
  
  // Extragem inițializarea formularelor într-o metodă separată
  private initForms(): void {
    this.profileForm = this.fb.group({
      email: ['', [Validators.email]],
      first_name: [''],
      last_name: [''],
      address: ['']
    });
    
    this.settingsForm = this.fb.group({
      email_notifications: [true],
      vote_reminders: [true],
      security_alerts: [true],
      show_name_in_forums: [false],
      show_activity_history: [false],
      high_contrast: [false],
      large_font: [false],
      language: [{value: 'ro', disabled: true}],
      two_factor_enabled: [false]
    });
    
    this.passwordForm = this.fb.group({
      old_password: ['', [Validators.required]],
      new_password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', [Validators.required]]
    }, { validator: this.passwordMatchValidator });
  }
  
  ngOnInit(): void {
    this.loadUserProfile();
  }
  
  loadUserProfile(): void {
    this.isLoading = true;
    this.settingsService.getUserProfile().subscribe(
      data => {
        this.userProfile = data;
        
        // Determine auth method
        this.authMethod = data.auth_method || (data.cnp && data.is_verified_by_id ? 'id_card' : 'email');
        
        // Set user details based on auth method
        if (this.authMethod === 'email') {
          this.userEmail = data.email;
          this.userCNP = null;
        } else {
          this.userCNP = data.cnp;
          this.userEmail = data.email; // Email might still be available for ID card users
        }
        
        this.firstName = data.first_name;
        this.lastName = data.last_name;
        
        // Set profile image if exists
        if (data.profile_image && data.profile_image.image_url) {
          this.profileImageUrl = data.profile_image.image_url;
        }
        
        // Update forms with user data
        this.updateProfileForm(data);
        this.updateSettingsForm(data.account_settings);
        
        this.isLoading = false;
      },
      error => {
        this.showError('Eroare la încărcarea profilului. Vă rugăm încercați din nou.');
        this.isLoading = false;
      }
    );
  }
  
  updateProfileForm(data: any): void {
    this.profileForm.patchValue({
      email: data.email || '',
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      address: data.address || ''
    });
    
    // Disable email field for ID card users
    if (this.authMethod === 'id_card') {
      this.profileForm.get('email')?.disable();
    }
  }
  
  updateSettingsForm(settings: any): void {
    if (!settings) return;
    
    this.settingsForm.patchValue({
      email_notifications: settings.email_notifications,
      vote_reminders: settings.vote_reminders,
      security_alerts: settings.security_alerts,
      show_name_in_forums: settings.show_name_in_forums,
      show_activity_history: settings.show_activity_history,
      high_contrast: settings.high_contrast,
      large_font: settings.large_font,
      // Don't update language from settings - always keep Romanian
      two_factor_enabled: settings.two_factor_enabled
    });
    
    // Make sure language stays disabled even after form update
    this.settingsForm.get('language')?.disable();
  }
  
  saveProfile(): void {
    if (this.profileForm.invalid) {
      return;
    }
    
    this.isSubmitting = true;
    const profileData = this.profileForm.value;
    
    this.settingsService.updateUserProfile(profileData).subscribe(
      response => {
        this.showSuccess('Profilul a fost actualizat cu succes');
        this.isSubmitting = false;
        
        // Update local state
        this.firstName = response.first_name;
        this.lastName = response.last_name;
        if (this.authMethod === 'email') {
          this.userEmail = response.email;
        }
      },
      error => {
        this.showError('Eroare la actualizarea profilului');
        this.isSubmitting = false;
      }
    );
  }
  
  saveSettings(): void {
    if (this.settingsForm.invalid) {
      return;
    }
    
    this.isSubmitting = true;
    const settingsData = this.settingsForm.value;
    
    this.settingsService.updateAccountSettings(settingsData).subscribe(
      response => {
        this.showSuccess('Setările au fost actualizate cu succes');
        this.isSubmitting = false;
      },
      error => {
        this.showError('Eroare la actualizarea setărilor');
        this.isSubmitting = false;
      }
    );
  }
  
  changePassword(): void {
    if (this.passwordForm.invalid) {
      return;
    }
    
    this.isSubmitting = true;
    const passwordData = this.passwordForm.value;
    
    this.settingsService.changePassword(passwordData).subscribe(
      response => {
        this.showSuccess('Parola a fost schimbată cu succes');
        this.isSubmitting = false;
        this.passwordForm.reset();
      },
      error => {
        if (error.error && error.error.new_password) {
          this.passwordErrors = Array.isArray(error.error.new_password) 
            ? error.error.new_password 
            : [error.error.new_password];
        } else if (error.error && error.error.old_password) {
          this.showError(error.error.old_password);
        } else {
          this.showError('Eroare la schimbarea parolei');
        }
        this.isSubmitting = false;
      }
    );
  }
  
  openFileInput(): void {
    if (this.fileInput && this.fileInput.nativeElement) {
      this.fileInput.nativeElement.click();
    }
  }
  
  onFileSelected(event: Event): void {
    const fileInput = event.target as HTMLInputElement;
    if (fileInput.files && fileInput.files[0]) {
      const file = fileInput.files[0];
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        this.showError('Imaginea este prea mare. Dimensiunea maximă permisă este 5MB.');
        return;
      }
      
      // Validate file type
      const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
      if (!validTypes.includes(file.type)) {
        this.showError('Format de fișier neacceptat. Vă rugăm încărcați o imagine JPEG sau PNG.');
        return;
      }
      
      const formData = new FormData();
      formData.append('image', file);
      
      this.isSubmitting = true;
      this.settingsService.uploadProfileImage(formData).subscribe(
        response => {
          if (response.image_url) {
            this.profileImageUrl = response.image_url;
          }
          this.showSuccess('Imaginea de profil a fost actualizată cu succes');
          this.isSubmitting = false;
        },
        error => {
          this.showError('Eroare la încărcarea imaginii');
          this.isSubmitting = false;
        }
      );
    }
  }
  
  deleteProfileImage(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '350px',
      data: {
        title: 'Confirmă ștergerea',
        message: 'Sunteți sigur că doriți să ștergeți imaginea de profil?',
        confirmText: 'Șterge',
        cancelText: 'Anulează'
      }
    });
    
    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.isSubmitting = true;
        this.settingsService.deleteProfileImage().subscribe(
          response => {
            this.profileImageUrl = null;
            this.showSuccess('Imaginea de profil a fost ștearsă cu succes');
            this.isSubmitting = false;
          },
          error => {
            this.showError('Eroare la ștergerea imaginii');
            this.isSubmitting = false;
          }
        );
      }
    });
  }
  
  deleteAccount(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: 'Confirmare dezactivare cont',
        message: 'Sunteți sigur că doriți să vă dezactivați contul? Această acțiune va face contul inactiv, dar datele dvs. vor fi păstrate conform politicii noastre de confidențialitate.',
        confirmText: 'Dezactivează',
        cancelText: 'Anulează',
        dangerMode: true
      }
    });
    
    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.isSubmitting = true;
        this.settingsService.deleteAccount().subscribe(
          response => {
            this.showSuccess('Contul dvs. a fost dezactivat cu succes');
            this.isSubmitting = false;
            
            // Logout și redirecționare către pagina principală
            setTimeout(() => {
              this.authService.logout();
              this.router.navigate(['/']);
            }, 2000);
          },
          error => {
            this.showError('Eroare la dezactivarea contului');
            this.isSubmitting = false;
          }
        );
      }
    });
  }
  
  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }
  
  togglePasswordVisibility(): void {
    this.isPasswordVisible = !this.isPasswordVisible;
  }
  
  toggleCurrentPasswordVisibility(): void {
    this.isCurrentPasswordVisible = !this.isCurrentPasswordVisible;
  }
  
  // Password validation
  passwordMatchValidator(g: FormGroup) {
    const newPassword = g.get('new_password')?.value;
    const confirmPassword = g.get('confirm_password')?.value;
    
    return newPassword === confirmPassword ? null : {'mismatch': true};
  }
  
  validatePassword(): void {
    const password = this.passwordForm.get('new_password')?.value;
    this.passwordErrors = [];
    
    if (!password) return;
    
    // Basic password complexity checks
    if (password.length < 8) {
      this.passwordErrors.push('Parola trebuie să aibă cel puțin 8 caractere.');
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
  
  // Helper for displaying first letters in avatar
  getInitials(): string {
    if (this.firstName && this.lastName) {
      return (this.firstName[0] + this.lastName[0]).toUpperCase();
    } else if (this.firstName) {
      return this.firstName[0].toUpperCase();
    } else if (this.lastName) {
      return this.lastName[0].toUpperCase();
    } else if (this.userEmail) {
      return this.userEmail[0].toUpperCase();
    } else if (this.userCNP) {
      return 'ID';
    }
    return '?';
  }
  
  // Generate random color for avatar background
  getRandomColor(): string {
    const colors = [
      '#3F51B5', '#2196F3', '#03A9F4', '#00BCD4', '#009688', 
      '#4CAF50', '#8BC34A', '#CDDC39', '#FFC107', '#FF9800', 
      '#FF5722', '#795548', '#607D8B'
    ];
    const randomIndex = Math.floor(Math.random() * colors.length);
    return colors[randomIndex];
  }
  
  // Mask CNP for privacy
  maskCNP(cnp: string): string {
    if (!cnp) return '';
    return cnp.substring(0, 3) + '********' + cnp.substring(11);
  }
  
  // Show success message
  showSuccess(message: string): void {
    this.snackBar.open(message, 'Închide', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }
  
  // Show error message
  showError(message: string): void {
    this.snackBar.open(message, 'Închide', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }
}