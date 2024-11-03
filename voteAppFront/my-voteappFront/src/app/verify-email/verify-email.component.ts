import { Component } from '@angular/core';
import { UserService } from '../user.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-verify-email',
  templateUrl: './verify-email.component.html',
  styleUrls: ['./verify-email.component.scss']
})
export class VerifyEmailComponent {
  email: string = '';
  verificationCode: string = '';
  message: string = '';
  isSuccess: boolean = false;

  constructor(private userService: UserService, private router: Router) {}

  verifyCode() {
    this.userService.verifyEmail(this.email, this.verificationCode).subscribe(
      response => {
        this.message = 'Email verificat cu succes!';
        this.isSuccess = true;
        setTimeout(() => {
          this.router.navigate(['/']);
        }, 2000); // Redirecționează după 2 secunde
      },
      error => {
        this.message = 'Cod de verificare incorect!';
        this.isSuccess = false;
      }
    );
  }
}
