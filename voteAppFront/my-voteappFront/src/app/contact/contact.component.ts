import { Component, OnInit } from '@angular/core';
import { ContactService, ContactInfo, ContactMessage } from '../services/contact.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ScheduleDialogComponent } from '../schedule-dialog/schedule-dialog.component';

@Component({
  selector: 'app-contact',
  templateUrl: './contact.component.html',
  styleUrls: ['./contact.component.scss']
})
export class ContactComponent implements OnInit {
  contactInfo: ContactInfo | null = null;
  isLoading: boolean = true;
  isSending: boolean = false;
  contactForm: FormGroup;
  
  constructor(
    private contactService: ContactService,
    private snackBar: MatSnackBar,
    private fb: FormBuilder, 
    private dialog: MatDialog
  ) {
    this.contactForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      message: ['', [Validators.required, Validators.minLength(10)]]
    });
  }

  ngOnInit(): void {
    console.log('ContactComponent: ngOnInit a fost apelat');
    this.loadContactInfo();
  }

  loadContactInfo(): void {
    console.log('ContactComponent: Începe încărcarea informațiilor de contact');
    this.isLoading = true;
    
    this.contactService.getContactInfo().subscribe({
      next: (data) => {
        console.log('ContactComponent: Date primite cu succes:', data);
        this.contactInfo = data;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('ContactComponent: Eroare la încărcarea datelor:', error);
        this.snackBar.open('Nu s-au putut încărca informațiile de contact', 'Închide', {
          duration: 3000,
          panelClass: ['error-snackbar']
        });
        this.isLoading = false;
      },
      complete: () => {
        console.log('ContactComponent: Încărcare completă');
        this.isLoading = false;
      }
    });
  }

  sendMessage(): void {
    if (this.contactForm.invalid) {
      this.markFormGroupTouched(this.contactForm);
      this.snackBar.open('Te rugăm să completezi corect toate câmpurile', 'Închide', {
        duration: 3000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    this.isSending = true;
    const messageData: ContactMessage = this.contactForm.value;

    this.contactService.sendContactMessage(messageData).subscribe({
      next: (response) => {
        this.snackBar.open('Mesajul tău a fost trimis cu succes!', 'Închide', {
          duration: 3000,
          panelClass: ['success-snackbar']
        });
        this.contactForm.reset();
        this.isSending = false;
      },
      error: (error) => {
        console.error('Eroare la trimiterea mesajului:', error);
        this.snackBar.open(error.error?.error || 'Eroare la trimiterea mesajului. Încearcă din nou.', 'Închide', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
        this.isSending = false;
      }
    });
  }
  openScheduleDialog(): void {
    const dialogRef = this.dialog.open(ScheduleDialogComponent, {
      width: '550px',
      maxWidth: '95vw',
      disableClose: true,
      panelClass: 'dark-dialog'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        // Programare trimisă cu succes
        console.log('Programare trimisă cu succes');
      }
    });
  }

  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
      if ((control as any).controls) {
        this.markFormGroupTouched(control as FormGroup);
      }
    });
  }

  get nameInvalid(): boolean {
    const control = this.contactForm.get('name');
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  get emailInvalid(): boolean {
    const control = this.contactForm.get('email');
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  get messageInvalid(): boolean {
    const control = this.contactForm.get('message');
    return !!control && control.invalid && (control.dirty || control.touched);
  }
}