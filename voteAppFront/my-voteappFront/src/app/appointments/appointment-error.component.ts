// src/app/appointments/appointment-error.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-appointment-error',
  template: `
    <div class="error-container">
      <h2>Eroare la procesarea programării</h2>
      <p>A apărut o eroare la procesarea solicitării.</p>
      <p>Programarea nu a putut fi găsită sau a fost deja procesată.</p>
      <p class="note">Poți închide această pagină și reveni la email-ul tău.</p>
    </div>
  `,
  styles: [`
    .error-container {
      padding: 40px;
      background-color: #1e1e1e;
      border-radius: 8px;
      text-align: center;
      max-width: 600px;
      margin: 40px auto;
      color: white;
    }
    h2 {
      color: #ff9800;
      margin-bottom: 20px;
    }
    .note {
      margin-top: 30px;
      font-style: italic;
      color: #aaa;
    }
  `]
})
export class AppointmentErrorComponent {}