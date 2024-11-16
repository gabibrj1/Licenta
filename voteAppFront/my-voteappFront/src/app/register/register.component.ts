import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserService } from '../user.service';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  registerForm: FormGroup;

  constructor(private fb: FormBuilder, private userService: UserService) {
    this.registerForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]],
      confirmPassword: ['', [Validators.required]],
      this:userService.initCsrf().subscribe({
        next: () => console.log('CSRF Cookie set'),
        error: (error) => console.error('Eroare la inițializarea CSRF:', error)
      }),
    

    });
  }
  

  onSubmit() {
    if (this.registerForm.valid) {
      const formData = this.registerForm.value;
      this.userService.register({
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirmPassword
      }).subscribe({
        next: (response) => alert('Înregistrare reușită. Verificați emailul pentru codul de verificare.'),
        error: (error) => alert('A apărut o eroare: ' + JSON.stringify(error.error.errors))
      });
    }
  }
}