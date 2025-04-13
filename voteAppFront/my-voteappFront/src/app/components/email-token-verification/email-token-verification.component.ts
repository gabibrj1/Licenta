import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { VoteSystemService } from '../../services/vote-system.service';

@Component({
  selector: 'app-email-token-verification',
  templateUrl: './email-token-verification.component.html',
  styleUrls: ['./email-token-verification.component.scss']
})
export class EmailTokenVerificationComponent implements OnInit {
  @Input() systemId: string = '';
  @Output() verificationComplete = new EventEmitter<boolean>();
  
  tokenForm: FormGroup;
  isSubmitting = false;
  errorMessage = '';
  verified = false;
  
  constructor(
    private fb: FormBuilder,
    private voteSystemService: VoteSystemService
  ) {
    this.tokenForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      token: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  ngOnInit(): void {
  }
  
  submitToken(): void {
    if (this.tokenForm.invalid) {
      return;
    }
    
    this.isSubmitting = true;
    this.errorMessage = '';
    
    const token = this.tokenForm.value.token.toUpperCase().trim();
    const email = this.tokenForm.value.email.trim();
    
    console.log(`Verificare token pentru sistemul ${this.systemId}: token=${token}, email=${email}`);
    
    this.voteSystemService.verifyVoteToken(this.systemId, token, email).subscribe({
      next: (response) => {
        console.log('Răspuns verificare token:', response);
        this.isSubmitting = false;
        
        if (response.valid) {
          this.verified = true;
          this.verificationComplete.emit(true);
          
          // Folosește response.session_token dacă există, altfel folosește token-ul original
          const sessionToken = response.session_token || token;
          console.log(`Token care va fi salvat: ${sessionToken}`);
          
          localStorage.setItem(`vote_session_${this.systemId}`, sessionToken);
          localStorage.setItem(`vote_email_${this.systemId}`, email);
          
          console.log(`Date salvate în localStorage: token=${sessionToken}, email=${email}`);
        } else {
          this.errorMessage = response.message || 'Cod invalid. Te rugăm să verifici și să încerci din nou.';
          this.verificationComplete.emit(false);
        }
      },
      error: (error) => {
        console.error('Eroare la verificarea token-ului:', error);
        this.isSubmitting = false;
        this.errorMessage = error.error?.message || 'A apărut o eroare la verificarea codului.';
        this.verificationComplete.emit(false);
      }
    });
  }
}