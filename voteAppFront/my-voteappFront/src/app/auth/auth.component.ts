import { Component, ElementRef, ViewChild, Renderer2 } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';


@Component({
  selector: 'app-auth',
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.scss']
})
export class AuthComponent {
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
  @ViewChild('video') videoElement!: ElementRef;
  videoStream!: MediaStream;

  constructor(private authService: AuthService, private router: Router, private renderer: Renderer2, private snackBar: MatSnackBar) {}

  ngOnInit() {
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode) {
      this.darkMode = JSON.parse(savedDarkMode);
      this.applyDarkMode();
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

  onIdCardAuthChange() {
    if (this.useIdCardAuth) {
      console.log('Autentificare prin buletin activată');
    } else {
      console.log('Autentificare standard activată');
    }
  }

  onSubmit() {
    if (this.useIdCardAuth) {
      if (this.cnp && this.series && this.firstName && this.lastName) {
        this.authService.loginWithIDCard(this.cnp, this.series, this.firstName, this.lastName).subscribe(
          response => this.router.navigate(['/dashboard']),
          error => {
            this.showErrorMessage('Autentificarea prin buletin a eșuat. Te rugăm să încerci din nou.');
          }
        );
      } else {
        this.showErrorMessage('Te rugăm să completezi toate câmpurile necesare.');
      }
    } else {
      if (this.email && this.password) {
        this.authService.login(this.email, this.password).subscribe(
          response => this.router.navigate(['/dashboard']),
          error => {
            this.showErrorMessage('Autentificarea a eșuat. Verifică email-ul și parola.');
          }
        );
      } else {
        this.showErrorMessage('Te rugăm să introduci email-ul și parola.');
      }
    }
  }

  private showErrorMessage(message: string) {
    this.snackBar.open(message, 'Închide', {
      duration: 5000,
      horizontalPosition: 'center',
      verticalPosition: 'top',
      panelClass: ['error-snackbar']
    });
  }

  navigateToRegister() {
    this.router.navigate(['/voteapp-front']);
  }

  // File Upload
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


  // Camera Functions
  openCamera() {
    this.isCameraOpen = true;
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        this.videoStream = stream;
        this.videoElement.nativeElement.srcObject = stream;
        this.videoElement.nativeElement.play();
      })
      .catch(error => {
        this.showErrorMessage('Nu s-a putut accesa camera. Te rugăm să verifici permisiunile.');
      });
  }

  closeCamera() {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
    }
    this.isCameraOpen = false;
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
}
