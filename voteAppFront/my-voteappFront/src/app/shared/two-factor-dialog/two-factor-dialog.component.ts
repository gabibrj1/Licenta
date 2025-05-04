// În two-factor-dialog.component.ts
import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { SetariContService } from '../../services/setari-cont.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-two-factor-dialog',
  templateUrl: './two-factor-dialog.component.html',
  styleUrls: ['./two-factor-dialog.component.scss']
})
export class TwoFactorDialogComponent implements OnInit {
  isLoading = false;
  verificationForm!: FormGroup;
  qrCodeData: string = '';
  secret: string = '';
  isVerified: boolean = false;
  showVerificationForm: boolean = false;

  constructor(
    private dialogRef: MatDialogRef<TwoFactorDialogComponent>,
    private fb: FormBuilder,
    private settingsService: SetariContService,
    private snackBar: MatSnackBar,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {
    this.verificationForm = this.fb.group({
      code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6), Validators.pattern('^[0-9]*$')]]
    });
  }

  ngOnInit(): void {
    this.loadTwoFactorSetup();
  }

  loadTwoFactorSetup(): void {
    this.isLoading = true;
    this.settingsService.getTwoFactorSetup().subscribe(
      (data) => {
        this.qrCodeData = data.qr_code;
        this.secret = data.secret;
        this.isVerified = data.is_verified;
        this.showVerificationForm = !data.is_verified;
        this.isLoading = false;
      },
      (error) => {
        this.showError('Eroare la încărcarea configurației pentru autentificarea în doi pași.');
        this.isLoading = false;
        this.dialogRef.close(false);
      }
    );
  }

  verifyCode(): void {
    if (this.verificationForm.invalid) {
      return;
    }

    const code = this.verificationForm.get('code')?.value;
    this.isLoading = true;

    this.settingsService.verifyTwoFactorSetup(code).subscribe(
      (response) => {
        this.isVerified = response.is_verified;
        this.showSuccess('Autentificarea în doi pași a fost configurată cu succes!');
        this.isLoading = false;
        this.dialogRef.close(true);
      },
      (error) => {
        this.showError(error.error?.error || 'Eroare la verificarea codului.');
        this.isLoading = false;
      }
    );
  }

  cancel(): void {
    this.dialogRef.close(false);
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