import { Component, OnInit, Inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AppointmentService } from '../services/appointment.service';

@Component({
  selector: 'app-schedule-dialog',
  templateUrl: './schedule-dialog.component.html',
  styleUrls: ['./schedule-dialog.component.scss']
})
export class ScheduleDialogComponent implements OnInit {
  scheduleForm: FormGroup;
  availableDates: Date[] = [];
  availableHours: string[] = [];
  isLoading = false;
  selectedDate: Date | null = null;
  currentStep = 1; // 1: Select date, 2: Select time, 3: Confirm
  
  businessHours = {
    start: 9, // 9:00 AM
    end: 17 // 5:00 PM
  };

  constructor(
    private fb: FormBuilder,
    private appointmentService: AppointmentService,
    private snackBar: MatSnackBar,
    public dialogRef: MatDialogRef<ScheduleDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {
    this.scheduleForm = this.fb.group({
      date: ['', Validators.required],
      time: ['', Validators.required],
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', Validators.required],
      notes: ['']
    });
  }

  ngOnInit(): void {
    this.generateAvailableDates();
  }

  // Generează următoarele 14 zile lucrătoare (Luni-Vineri)
  generateAvailableDates(): void {
    const today = new Date();
    let nextDay = new Date(today);
    nextDay.setDate(today.getDate() + 1); // Start from tomorrow
    
    let count = 0;
    while (count < 14) {
      const dayOfWeek = nextDay.getDay();
      // 0 is Sunday, 6 is Saturday
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
        // Clone the date to avoid reference issues
        this.availableDates.push(new Date(nextDay));
        count++;
      }
      nextDay.setDate(nextDay.getDate() + 1);
    }
  }

  // Când utilizatorul selectează o dată
  onSelectDate(date: Date): void {
    this.selectedDate = date;
    this.scheduleForm.get('date')?.setValue(date);
    this.isLoading = true;
    
    // Formatăm data pentru API (YYYY-MM-DD) asigurându-ne că folosim data locală
    const formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    
    console.log(`Verifică disponibilitatea pentru data: ${formattedDate}`);
    
    // Verificăm disponibilitatea
    this.appointmentService.getAvailableHours(formattedDate).subscribe({
      next: (response) => {
        console.log('Ore disponibile primite:', response);
        this.availableHours = response.available_hours;
        this.isLoading = false;
        this.currentStep = 2;
      },
      error: (error) => {
        console.error('Eroare la verificarea disponibilității:', error);
        this.snackBar.open('Eroare la verificarea disponibilității. Încearcă din nou.', 'Închide', {
          duration: 3000,
          panelClass: ['error-snackbar']
        });
        // Folosim ore implicite în caz de eroare
        this.generateDefaultHours();
        this.isLoading = false;
        this.currentStep = 2;
      }
    });
  }
  
// Metodă pentru a genera ore implicite (în caz de eroare)
generateDefaultHours(): void {
  this.availableHours = [];
  for (let hour = 9; hour <= 17; hour++) {
    // Sari peste ora 12 (pauză de prânz)
    if (hour !== 12) {
      this.availableHours.push(`${hour}:00`);
    }
  }
}

  // Când utilizatorul selectează o oră
  onSelectTime(time: string): void {
    console.log(`Oră selectată: ${time}`);
    this.scheduleForm.get('time')?.setValue(time);
    this.currentStep = 3;
  }

  // Formatează data pentru afișare
  formatDate(date: Date): string {
    const options: Intl.DateTimeFormatOptions = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    };
    return date.toLocaleDateString('ro-RO', options);
  }

  // Verifică dacă data este selectată
  isDateSelected(date: Date): boolean {
    return this.selectedDate ? 
      this.selectedDate.getDate() === date.getDate() && 
      this.selectedDate.getMonth() === date.getMonth() &&
      this.selectedDate.getFullYear() === date.getFullYear() : false;
  }

  // Trimite programarea
// Modifică metoda submitAppointment pentru a include ora originală
// Trimite programarea
submitAppointment(): void {
  if (this.scheduleForm.invalid) {
    return;
  }

  this.isLoading = true;
  const formData = this.scheduleForm.value;
  
  // Combinăm data și ora într-un singur obiect Date
  const selectedDate = new Date(formData.date);
  const [hours, minutes] = formData.time.split(':').map(Number);
  
  // Setăm ora și minutul exact
  selectedDate.setHours(hours);
  selectedDate.setMinutes(0); // Asigură-te că minutele sunt 0
  selectedDate.setSeconds(0);
  selectedDate.setMilliseconds(0);
  
  console.log(`Data programării: ${selectedDate.toISOString()}`);
  console.log(`Ora selectată: ${hours}:00`);
  
  // Creează obiectul de date pentru trimitere, păstrând toate câmpurile originale
  const appointmentData = {
    name: formData.name,
    email: formData.email,
    phone: formData.phone,
    dateTime: selectedDate.toISOString(),
    originalHour: hours, // Adăugăm ora originală selectată pentru a o păstra
    notes: formData.notes || ''
  };

  console.log('Trimit datele programării:', appointmentData);

  this.appointmentService.scheduleAppointment(appointmentData).subscribe({
    next: (response) => {
      this.isLoading = false;
      this.snackBar.open('Programarea a fost trimisă cu succes! Veți primi un email de confirmare.', 'Închide', {
        duration: 5000,
        panelClass: ['success-snackbar']
      });
      this.dialogRef.close(true);
    },
    error: (error) => {
      this.isLoading = false;
      console.error('Eroare la trimiterea programării:', error);
      
      // Afișează mesajul de eroare specific de la backend
      let errorMessage = 'A apărut o eroare. Încercați din nou.';
      if (error.error && error.error.message) {
        errorMessage = error.error.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      this.snackBar.open(errorMessage, 'Închide', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
    }
  });
}

  // Navighează înapoi
  goBack(): void {
    this.currentStep--;
  }

  // Închide dialogul
  closeDialog(): void {
    this.dialogRef.close();
  }
}