import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { VoteSystemService } from '../../services/vote-system.service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-create-vote-system',
  templateUrl: './create-vote-system.component.html',
  styleUrls: ['./create-vote-system.component.scss']
})
export class CreateVoteSystemComponent implements OnInit {
  // Stări pentru UI
  currentStep = 1;
  totalSteps = 5;
  isSubmitting = false;
  submitted = false;
  errorMessage = '';
  successMessage = '';
  createdSystemId: string = '';

  // Sistemul activ
  hasActiveSystem = false;
  activeSystem: any = null;
  isLoadingActiveSystem = true;
  
  // Timer pentru expirarea sistemului activ
  timerSubscription: Subscription | null = null;
  remainingTime: any = {
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0
  };


  
  // Formular principal
  voteSystemForm: FormGroup;
  
  // Opțiuni pentru selecturi
  voteTypes = [
    { id: 'single', name: 'Vot unic (un singur vot per utilizator)' },
    { id: 'multiple', name: 'Vot multiplu (mai multe voturi per utilizator)' },
    { id: 'ranked', name: 'Vot preferențial (ordonare preferințe)' },
    { id: 'weighted', name: 'Vot ponderat (voturi cu greutăți diferite)' }
  ];
  
  visibilityOptions = [
    { id: 'public', name: 'Public (oricine poate vedea și vota)' },
    { id: 'registered', name: 'Doar utilizatori înregistrați' },
    { id: 'invited', name: 'Doar utilizatori invitați' }
  ];
  
  resultVisibilityOptions = [
    { id: 'realtime', name: 'În timp real (rezultatele sunt vizibile în timpul votului)' },
    { id: 'after_vote', name: 'După vot (rezultatele sunt vizibile doar după ce utilizatorul votează)' },
    { id: 'after_end', name: 'După încheierea perioadei de vot' },
    { id: 'hidden', name: 'Ascunse (doar administratorul poate vedea rezultatele)' }
  ];

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private authService: AuthService,
    private voteSystemService: VoteSystemService 
  ) {
    this.voteSystemForm = this.fb.group({
      // Pas 1: Informații de bază
      basicInfo: this.fb.group({
        name: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(100)]],
        description: ['', [Validators.required, Validators.minLength(20), Validators.maxLength(1000)]],
        category: ['', Validators.required]
      }),
      
      // Pas 2: Opțiuni de vot
      votingOptions: this.fb.group({
        options: this.fb.array([
          this.createOption(),
          this.createOption()
        ]),
        allowCustomOptions: [false]
      }),
      
      // Pas 3: Reguli și parametri
      rules: this.fb.group({
        voteType: ['single', Validators.required],
        maxVotesPerUser: [1, [Validators.required, Validators.min(1)]],
        visibility: ['public', Validators.required],
        resultVisibility: ['after_end', Validators.required],
        requireVerification: [false],
        allowComments: [false],
        allowAnonymousVoting: [false],
        requireEmailVerification: [false]
      }),

      // Pas 4: Lista de emailuiri pentru votanti
      voterEmails: this.fb.group({
        emails: ['', Validators.required],
        sendImmediately: [true]
      }),
      
      // Pas 5: Programare și durată
      schedule: this.fb.group({
        startDate: ['', Validators.required],
        endDate: ['', Validators.required],
        startTime: ['', Validators.required],
        endTime: ['', Validators.required],
        timeZone: ['Europe/Bucharest', Validators.required]
      })
    });
  }

  ngOnInit(): void {
    // Verificam daca utilizatorul are un sistem de vot activ
    this.checkActiveVoteSystem();

    // Setăm data minimă ca ziua curentă
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);
    
    // Formatare pentru input-uri de tip date
    const formattedToday = this.formatDate(today);
    const formattedTomorrow = this.formatDate(tomorrow);
    
    // Actualizăm valorile implicite pentru datele de început și sfârșit
    this.voteSystemForm.get('schedule.startDate')?.setValue(formattedToday);
    this.voteSystemForm.get('schedule.endDate')?.setValue(formattedTomorrow);
    
    // Setăm ore implicite
    this.voteSystemForm.get('schedule.startTime')?.setValue('09:00');
    this.voteSystemForm.get('schedule.endTime')?.setValue('18:00');

    //Adaugam listener pentru schimbarea optiunii de verificare prin email
    this.voteSystemForm.get('rules.requireEmailVerification')?.valueChanges.subscribe(value => {
      this.onEmailVerificationChange(value);
    });
  }
  ngOnDestroy(): void {
    // Anulăm subscription-ul la timer când componenta este distrusă
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
    }
  }
  checkActiveVoteSystem(): void {
    this.isLoadingActiveSystem = true;
    
    this.voteSystemService.checkActiveVoteSystem().subscribe({
      next: (response) => {
        this.isLoadingActiveSystem = false;
        this.hasActiveSystem = response.has_active_system;
        
        if (this.hasActiveSystem && response.system) {
          this.activeSystem = response.system;
          
          // Pornim timer-ul pentru sistemul activ
          this.startExpirationTimer();
        }
      },
      error: (error) => {
        this.isLoadingActiveSystem = false;
        console.error('Eroare la verificarea sistemului activ:', error);
      }
    });
  }
  
  // Pornim timer-ul pentru expirarea sistemului
  startExpirationTimer(): void {
    // Anulăm orice timer existent
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
    }
    
    // Pornim un nou timer care se actualizează la fiecare secundă
    this.timerSubscription = interval(1000).subscribe(() => {
      this.updateRemainingTime();
    });
    
    // Actualizăm timpul rămas inițial
    this.updateRemainingTime();
  }
  
  // Actualizează timpul rămas până la expirarea sistemului activ
  updateRemainingTime(): void {
    if (!this.activeSystem || !this.activeSystem.end_date) return;
    
    const now = new Date();
    const endDate = new Date(this.activeSystem.end_date);
    
    // Calculăm diferența în milisecunde
    let diff = endDate.getTime() - now.getTime();
    
    // Dacă timpul a expirat, reîncărcăm starea sistemului
    if (diff <= 0) {
      this.checkActiveVoteSystem();
      return;
    }
    
    // Calculăm zilele, orele, minutele și secundele
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    diff -= days * (1000 * 60 * 60 * 24);
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    diff -= hours * (1000 * 60 * 60);
    
    const minutes = Math.floor(diff / (1000 * 60));
    diff -= minutes * (1000 * 60);
    
    const seconds = Math.floor(diff / 1000);
    
    // Actualizăm obiectul cu timpul rămas
    this.remainingTime = {
      days,
      hours,
      minutes,
      seconds
    };
  }

  
  // Formatare dată pentru input de tip date
  private formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
    // Formatează data pentru afișare
    formatDateTime(date: string): string {
      if (!date) return '';
      
      const dateObj = new Date(date);
      
      return dateObj.toLocaleDateString('ro-RO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
    
    // Navighează către detaliile sistemului activ
    viewActiveSystem(): void {
      if (this.activeSystem && this.activeSystem.id) {
        this.router.navigate(['/menu/despre/sisteme-vot', this.activeSystem.id]);
      }
    }
  
  // Crează o nouă opțiune pentru FormArray
  createOption(): FormGroup {
    return this.fb.group({
      title: ['', [Validators.required, Validators.minLength(1)]],
      description: [''],
      imageUrl: ['']
    });
  }
  
  // Getter pentru accesarea opțiunilor de vot ca FormArray
  get optionsArray(): FormArray {
    return this.voteSystemForm.get('votingOptions.options') as FormArray;
  }
  
  // Adaugă o nouă opțiune de vot
  addOption(): void {
    this.optionsArray.push(this.createOption());
  }
  
  // Șterge o opțiune de vot
  removeOption(index: number): void {
    if (this.optionsArray.length > 2) {
      this.optionsArray.removeAt(index);
    }
  }

  // Arata sau ascunde pasul de emailuri in functie de varainta selectata
  onEmailVerificationChange(value: boolean): void {
    if (value){
      this.totalSteps = 5;
      if (this.currentStep > 4) {
        this.currentStep = 5;
      }
    } else {
      this.totalSteps = 4;
      if (this.currentStep === 4) {
        this.currentStep = 3;
      }
    }
  }
  
  // Navigare între pași
  nextStep(): void {
    const currentFormGroup = this.getCurrentFormGroup();
    
    if (currentFormGroup.valid) {
      // Verifică dacă pasul curent este 3 și verificarea prin email este dezactivată
      const requireEmailVerification = this.voteSystemForm.get('rules.requireEmailVerification')?.value;
      
      if (this.currentStep === 3 && !requireEmailVerification) {
        this.currentStep = 5; // Sărim peste pasul de emailuri
      } else {
        this.currentStep++;
      }
    } else {
      // Marchează toate câmpurile ca touched pentru a afișa erorile
      Object.keys(currentFormGroup.controls).forEach(key => {
        const control = currentFormGroup.get(key);
        control?.markAsTouched();
      });
      
      // Dacă avem un FormArray, marcăm și controalele din acesta
      if (this.currentStep === 2) {
        this.optionsArray.controls.forEach(control => {
          Object.keys(control.value).forEach(key => {
            control.get(key)?.markAsTouched();
          });
        });
      }
      
      this.errorMessage = 'Vă rugăm să completați toate câmpurile obligatorii corect.';
    }
  }
  
  prevStep(): void {
    if (this.currentStep > 1) {
      // Verifică dacă pasul curent este 5 și verificarea prin email este dezactivată
      const requireEmailVerification = this.voteSystemForm.get('rules.requireEmailVerification')?.value;
      
      if (this.currentStep === 5 && !requireEmailVerification) {
        this.currentStep = 3; // Sărim peste pasul de emailuri
      } else {
        this.currentStep--;
      }
      
      this.errorMessage = '';
    }
  }
  
  // Obține grupul de forme pentru pasul curent
  getCurrentFormGroup(): FormGroup {
    switch (this.currentStep) {
      case 1:
        return this.voteSystemForm.get('basicInfo') as FormGroup;
      case 2:
        return this.voteSystemForm.get('votingOptions') as FormGroup;
      case 3:
        return this.voteSystemForm.get('rules') as FormGroup;
      case 4:
        return this.voteSystemForm.get('voterEmails') as FormGroup;
      case 5:
        return this.voteSystemForm.get('schedule') as FormGroup;
      default:
        return this.voteSystemForm.get('basicInfo') as FormGroup;
    }
  }
  
  // Trimitere formular
  onSubmit(): void {
    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';
    
    if (this.voteSystemForm.valid) {
      // Pregătim datele pentru backend
      const basicInfo = this.voteSystemForm.get('basicInfo')?.value;
      const votingOptions = this.voteSystemForm.get('votingOptions')?.value;
      const rules = this.voteSystemForm.get('rules')?.value;
      const schedule = this.voteSystemForm.get('schedule')?.value;
      
      // Combinăm date/time pentru start și end
      const startDate = new Date(schedule.startDate + 'T' + schedule.startTime);
      const endDate = new Date(schedule.endDate + 'T' + schedule.endTime);
      
      // Construim obiectul de date pentru backend
      const formData = {
        name: basicInfo.name,
        description: basicInfo.description,
        category: basicInfo.category,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        rules: {
          vote_type: rules.voteType,
          max_votes_per_user: rules.maxVotesPerUser,
          visibility: rules.visibility,
          result_visibility: rules.resultVisibility,
          require_verification: rules.requireVerification,
          allow_comments: rules.allowComments,
          allow_anonymous_voting: rules.allowAnonymousVoting,
          require_email_verification: rules.requireEmailVerification
        },
        options: votingOptions.options
      };
      
      console.log('Trimite date sistem vot:', formData);
      
      // Trimitem datele către backend
      this.voteSystemService.createVoteSystem(formData).subscribe({
        next: (response) => {
          this.createdSystemId = response.system_id;
          console.log('Sistem creat cu ID:', this.createdSystemId);
          
          // Dacă este activată verificarea prin email, trimitem listele de email
          if (rules.requireEmailVerification) {
            const emailsData = this.voteSystemForm.get('voterEmails')?.value;
            if (!emailsData || !emailsData.emails || emailsData.emails.trim() === '') {
              this.isSubmitting = false;
              this.errorMessage = 'Lista de email-uri nu poate fi goală când este activată verificarea prin email.';
              return;
            }
            
            const emailsList = emailsData.emails
              .split(/[\n,;]+/)
              .map((email: string) => email.trim())
              .filter((email: string) => email !== '');
            
            console.log('Lista de email-uri pentru trimitere:', emailsList);
            
            if (emailsList.length === 0) {
              this.isSubmitting = false;
              this.errorMessage = 'Nu s-au găsit adrese de email valide în lista furnizată.';
              return;
            }
            
            this.voteSystemService.manageVoterEmails(this.createdSystemId, emailsList).subscribe({
              next: (emailResponse) => {
                console.log('Răspuns management email-uri:', emailResponse);
                
                // Dacă s-a cerut trimiterea imediată a tokenurilor
                if (emailsData.sendImmediately) {
                  console.log('Se trimit token-uri...');
                  
                  this.voteSystemService.sendVoteTokens(this.createdSystemId).subscribe({
                    next: (tokenResponse) => {
                      console.log('Răspuns trimitere token-uri:', tokenResponse);
                      this.isSubmitting = false;
                      this.submitted = true;
                      
                      if (tokenResponse.success) {
                        this.successMessage = `Sistemul de vot a fost creat cu succes și au fost trimise ${tokenResponse.emails_sent} email-uri cu coduri de acces!`;
                      } else {
                        this.successMessage = 'Sistemul de vot a fost creat, dar a apărut o eroare la trimiterea email-urilor.';
                      }
                      
                      // Redirecționăm către pagina de status
                      setTimeout(() => {
                        this.router.navigate(['/menu/despre/status-vot', this.createdSystemId]);
                      }, 2000);
                    },
                    error: (tokenError) => {
                      console.error('Eroare trimitere token-uri:', tokenError);
                      this.isSubmitting = false;
                      this.submitted = true;
                      this.successMessage = 'Sistemul de vot a fost creat, dar a apărut o eroare la trimiterea email-urilor.';
                      
                      setTimeout(() => {
                        this.router.navigate(['/menu/despre/status-vot', this.createdSystemId]);
                      }, 2000);
                    }
                  });
                } else {
                  this.isSubmitting = false;
                  this.submitted = true;
                  this.successMessage = 'Sistemul de vot a fost creat cu succes și a fost trimis spre verificare.';
                  
                  // Redirecționăm către pagina de status
                  setTimeout(() => {
                    this.router.navigate(['/menu/despre/status-vot', this.createdSystemId]);
                  }, 2000);
                }
              },
              error: (emailError) => {
                console.error('Eroare management email-uri:', emailError);
                this.isSubmitting = false;
                this.errorMessage = 'Sistemul de vot a fost creat, dar a apărut o eroare la salvarea listei de email-uri.';
              }
            });
          } else {
            this.isSubmitting = false;
            this.submitted = true;
            this.successMessage = 'Sistemul de vot a fost creat cu succes și a fost trimis spre verificare.';
            
            // Redirecționăm către pagina de status
            setTimeout(() => {
              this.router.navigate(['/menu/despre/status-vot', this.createdSystemId]);
            }, 2000);
          }
        },
        error: (error) => {
          console.error('Eroare creare sistem vot:', error);
          this.isSubmitting = false;
          
          if (error.error && error.error.errors) {
            // Afișăm erorile de validare
            const errorMessages = [];
            for (const field in error.error.errors) {
              errorMessages.push(`${field}: ${error.error.errors[field]}`);
            }
            this.errorMessage = errorMessages.join('\n');
          } else {
            this.errorMessage = error.error?.error || 'A apărut o eroare la crearea sistemului de vot.';
          }
        }
      });
    } else {
      this.isSubmitting = false;
      this.errorMessage = 'Vă rugăm să completați toate câmpurile obligatorii.';
      
      // Marchează toate câmpurile ca touched pentru a afișa erorile
      this.markFormGroupTouched(this.voteSystemForm);
    }
  }
  
  // Helper pentru a marca toate controalele ca touched
  markFormGroupTouched(formGroup: FormGroup) {
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
  
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }
  
  // Resetează formularul și revine la primul pas
  resetForm(): void {
    this.voteSystemForm.reset();
    this.currentStep = 1;
    this.submitted = false;
    this.successMessage = '';
    this.errorMessage = '';
    
    // Reinițializăm datele implicite
    this.ngOnInit();
  }
  
  // Verifică dacă un control are erori
  hasError(formGroupName: string, controlName: string): boolean {
    const control = this.voteSystemForm.get(formGroupName)?.get(controlName);
    return !!control && control.invalid && (control.dirty || control.touched);
  }
  
  // Obține mesajul de eroare pentru un control
  getErrorMessage(formGroupName: string, controlName: string): string {
    const control = this.voteSystemForm.get(formGroupName)?.get(controlName);
    
    if (!control) return '';
    
    if (control.errors?.['required']) {
      return 'Acest câmp este obligatoriu.';
    }
    
    if (control.errors?.['minlength']) {
      return `Acest câmp trebuie să conțină minim ${control.errors['minlength'].requiredLength} caractere.`;
    }
    
    if (control.errors?.['maxlength']) {
      return `Acest câmp poate conține maxim ${control.errors['maxlength'].requiredLength} caractere.`;
    }
    
    if (control.errors?.['min']) {
      return `Valoarea minimă admisă este ${control.errors['min'].min}.`;
    }
    
    if (control.errors?.['max']) {
      return `Valoarea maximă admisă este ${control.errors['max'].max}.`;
    }
    
    return 'Valoare invalidă.';
  }
  
  // Verifică dacă un control din FormArray are erori
  hasOptionError(index: number, controlName: string): boolean {
    const control = this.optionsArray.at(index).get(controlName);
    return !!control && control.invalid && (control.dirty || control.touched);
  }
  
  // Obține mesajul de eroare pentru un control din FormArray
  getOptionErrorMessage(index: number, controlName: string): string {
    const control = this.optionsArray.at(index).get(controlName);
    
    if (!control) return '';
    
    if (control.errors?.['required']) {
      return 'Acest câmp este obligatoriu.';
    }
    
    if (control.errors?.['minlength']) {
      return `Acest câmp trebuie să conțină minim ${control.errors['minlength'].requiredLength} caractere.`;
    }
    
    return 'Valoare invalidă.';
  }
  
  // Când se schimbă tipul de vot
  onVoteTypeChange(): void {
    const voteType = this.voteSystemForm.get('rules.voteType')?.value;
    
    if (voteType === 'single') {
      this.voteSystemForm.get('rules.maxVotesPerUser')?.setValue(1);
    } else if (voteType === 'multiple') {
      this.voteSystemForm.get('rules.maxVotesPerUser')?.setValue(3);
    }
  }
}