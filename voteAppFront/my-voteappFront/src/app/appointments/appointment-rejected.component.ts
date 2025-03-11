// src/app/appointments/appointment-rejected.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-appointment-rejected',
  template: `
    <div class="rejected-container">
      <h2>Programare respinsă</h2>
      <p>Programarea a fost respinsă.</p>
      <p>Un email a fost trimis solicitantului pentru a-l informa.</p>
      <p class="note">Poți închide această pagină și reveni la email-ul tău.</p>
    </div>
  `,
  styles: [`
    .rejected-container {
      padding: 40px;
      background-color: #1e1e1e;
      border-radius: 8px;
      text-align: center;
      max-width: 600px;
      margin: 40px auto;
      color: white;
    }
    h2 {
      color: #f44336;
      margin-bottom: 20px;
    }
    .note {
      margin-top: 30px;
      font-style: italic;
      color: #aaa;
    }
  `]
})
export class AppointmentRejectedComponent {}