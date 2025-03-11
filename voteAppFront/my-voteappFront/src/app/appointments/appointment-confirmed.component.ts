// src/app/appointments/appointment-confirmed.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-appointment-confirmed',
  template: `
    <div class="success-container">
      <h2>Programare confirmată</h2>
      <p>Programarea a fost confirmată cu succes.</p>
      <p>Un email de confirmare a fost trimis solicitantului.</p>
      <p class="note">Poți închide această pagină și reveni la email-ul tău.</p>
    </div>
  `,
  styles: [`
    .success-container {
      padding: 40px;
      background-color: #1e1e1e;
      border-radius: 8px;
      text-align: center;
      max-width: 600px;
      margin: 40px auto;
      color: white;
    }
    h2 {
      color: #4CAF50;
      margin-bottom: 20px;
    }
    .note {
      margin-top: 30px;
      font-style: italic;
      color: #aaa;
    }
  `]
})
export class AppointmentConfirmedComponent {}