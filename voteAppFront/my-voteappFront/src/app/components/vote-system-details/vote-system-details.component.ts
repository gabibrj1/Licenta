import { Component, OnInit, OnDestroy, ViewChild, ElementRef, ChangeDetectorRef, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { VoteSystemService } from '../../services/vote-system.service';
import { FormBuilder, FormGroup, Validators, FormArray, FormControl  } from '@angular/forms';
import { environment } from '../../../src/environments/environment';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-vote-system-details',
  templateUrl: './vote-system-details.component.html',
  styleUrls: ['./vote-system-details.component.scss']
})
export class VoteSystemDetailsComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('pieChartCanvas') pieChartCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('barChartCanvas') barChartCanvas!: ElementRef<HTMLCanvasElement>;
  
  systemId: string = '';
  voteSystem: any = null;
  isLoading = true;
  errorMessage = '';
  
  // State pentru interfață
  activeTab = 'overview'; // overview, results, share, settings
  
  // Formular pentru vot
  voteForm: FormGroup;
  isSubmittingVote = false;
  voteSubmitted = false;
  voteError = '';
  isLocalhost = false;
  
  // Linkuri pentru distribuire
  shareLinks = {
    directLink: '',
    embedCode: '',
    qrCodeUrl: ''
  };

  // Date pentru rezultate
  resultsData: any[] = [];
  totalVotes: number = 0;
  resultsUpdateSubscription: Subscription | null = null;

  // Flag pentru a urmări dacă componenta este încă vie
  private alive = true;

  // State pentru editare si stergere
  editForm: FormGroup;
  isEditing = false;
  isEditSubmitting = false;
  editError = '';
  editSuccess = '';

  isDeleting = false;
  deleteError = '';
  deleteConfirmationOpen = false;

  
  // Instanțe pentru grafice
  pieChart: Chart | null = null;
  barChart: Chart | null = null;
  

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private voteSystemService: VoteSystemService,
    private fb: FormBuilder,
    private cdr: ChangeDetectorRef
  ) {
    
    this.voteForm = this.fb.group({
      selectedOption: ['', Validators.required]
    });
    this.editForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(100)]],
      description: ['', [Validators.required, Validators.minLength(20), Validators.maxLength(1000)]],
      category: ['', Validators.required],
      start_date: ['', Validators.required],
      start_time: ['', Validators.required],
      end_date: ['', Validators.required],
      end_time: ['', Validators.required],
      voter_emails: ['', [this.validateEmails]],
      rules: this.fb.group({
        vote_type: ['single', Validators.required],
        max_votes_per_user: [1, [Validators.required, Validators.min(1)]],
        visibility: ['public', Validators.required],
        result_visibility: ['after_end', Validators.required],
        require_verification: [false],
        allow_comments: [false],
        allow_anonymous_voting: [false],
        require_email_verification: [false]
      }),
      options: this.fb.array([])
    });

  }

  ngOnInit(): void {
    this.systemId = this.route.snapshot.paramMap.get('id') || '';
    
    if (!this.systemId) {
      this.errorMessage = 'ID-ul sistemului de vot lipsește.';
      this.isLoading = false;
      return;
    }
    
    this.loadVoteSystem();
  }

  ngAfterViewInit(): void {
    // Dacă suntem în tabul de rezultate și avem date, inițializăm graficele
    if (this.activeTab === 'results' && this.resultsData.length > 0) {
      this.initCharts();
    }
  }
  
  ngOnDestroy(): void {
    // Marcăm componenta ca fiind distrusă
    this.alive = false;
    
    // Anulăm abonamentul la actualizări
    if (this.resultsUpdateSubscription) {
      this.resultsUpdateSubscription.unsubscribe();
    }
    
    // Distrugem graficele pentru a evita memory leaks
    if (this.pieChart) {
      this.pieChart.destroy();
    }
    
    if (this.barChart) {
      this.barChart.destroy();
    }
  }

  validateEmails(control: FormControl): { [key: string]: any } | null {
    if (!control.value) {
      return null;
    }
    
    const emails = control.value.split('\n').map((email: string) => email.trim()).filter((email: string) => email !== '');
    
    if (emails.length === 0) {
      return { 'required': true };
    }
    
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const invalidEmails = emails.filter((email: string) => !emailPattern.test(email));
    
    if (invalidEmails.length > 0) {
      return { 'invalidEmails': invalidEmails };
    }
    
    return null;
  }
  loadVoterEmails(): void {
    if (!this.voteSystem || !this.systemId) return;
    
    this.voteSystemService.getVoterEmails(this.systemId).subscribe({
      next: (response: {success: boolean, emails: string[]}) => {
        if (response.success && response.emails) {
          // Populează câmpul voter_emails cu email-urile existente
          this.editForm.patchValue({
            voter_emails: response.emails.join('\n')
          });
        }
      },
      error: (error: any) => {
        console.error('Eroare la încărcarea email-urilor votanților:', error);
        // Pentru a nu bloca utilizatorul, doar afișăm eroarea în consolă
      }
    });
  }
  
  // Adaugă această metodă în clasa componentei
getEmailCount(): number {
  const emailsValue = this.editForm.get('voter_emails')?.value;
  if (!emailsValue) return 0;
  
  return emailsValue.split('\n')
    .map((email: string) => email.trim())
    .filter((email: string) => email !== '')
    .length;
}
  

  

  loadVoteSystem(): void {
    this.isLoading = true;
    this.voteSystemService.getVoteSystemDetails(this.systemId).subscribe({
      next: (data) => {
        this.voteSystem = data;
        this.isLoading = false;

        // Extragem numarul total de voturi
        this.totalVotes = data.total_votes || 0;
        
        // Generăm linkurile pentru share
        this.generateShareLinks();

        // Inițializăm actualizarea periodică a rezultatelor și informațiilor de sistem
        this.startLiveUpdates();
        
        // Dacă suntem în tabul de rezultate, încărcăm datele
        if (this.activeTab === 'results') {
          this.loadResultsData();
        }
      },
      error: (error) => {
        this.errorMessage = 'Nu s-au putut încărca detaliile sistemului de vot.';
        this.isLoading = false;
        console.error('Eroare la încărcarea detaliilor sistemului de vot:', error);
      }
    });
  }
    // Metodă pentru a deschide formularul de editare
    openEditForm(): void {
      if (!this.voteSystem) return;
      
      // Verificăm dacă sistemul poate fi editat (doar dacă este în starea "pending")
      if (this.voteSystem.status !== 'pending') {
        this.editError = 'Acest sistem nu mai poate fi modificat deoarece a început sau s-a încheiat.';
        return;
      }
      
      this.isEditing = true;
      this.editError = '';
      this.editSuccess = '';
      
      // Extragem data și ora din datetime
      const startDate = new Date(this.voteSystem.start_date);
      const endDate = new Date(this.voteSystem.end_date);
      
      const formatDate = (date: Date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };
      
      const formatTime = (date: Date) => {
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
      };
      
      // Populăm formularul cu datele existente
      this.editForm.patchValue({
        name: this.voteSystem.name,
        description: this.voteSystem.description,
        category: this.voteSystem.category,
        start_date: formatDate(startDate),
        start_time: formatTime(startDate),
        end_date: formatDate(endDate),
        end_time: formatTime(endDate),
        rules: this.voteSystem.rules
      });
      
      // Resetăm array-ul de opțiuni
      this.optionsArray.clear();
      
      // Adăugăm opțiunile existente
      if (this.voteSystem.options && this.voteSystem.options.length > 0) {
        this.voteSystem.options.forEach((option: any) => {
          this.optionsArray.push(this.fb.group({
            id: [option.id],
            title: [option.title, [Validators.required, Validators.minLength(1)]],
            description: [option.description || ''],
            image_url: [option.image_url || '']
          }));
        });
      }
      this.loadVoterEmails();
    }
      // Getter pentru accesarea opțiunilor ca FormArray
  get optionsArray(): FormArray {
    return this.editForm.get('options') as FormArray;
    
  }
  
  
  // Adaugă o nouă opțiune
  addOption(): void {
    this.optionsArray.push(this.fb.group({
      title: ['', [Validators.required, Validators.minLength(1)]],
      description: [''],
      image_url: ['']
    }));
  }
  
  // Șterge o opțiune
  removeOption(index: number): void {
    if (this.optionsArray.length > 2) {
      this.optionsArray.removeAt(index);
    } else {
      this.editError = 'Sistemul de vot trebuie să aibă cel puțin 2 opțiuni.';
    }
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
  
  // Verifică dacă un control are erori
  hasError(controlName: string): boolean {
    const control = this.editForm.get(controlName);
    return !!control && control.invalid && (control.dirty || control.touched);
  }
  
  // Obține mesajul de eroare pentru un control
  getErrorMessage(controlName: string): string {
    const control = this.editForm.get(controlName);
    
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
    if (controlName === 'voter_emails') {
      if (control.errors?.['invalidEmails']) {
        const invalidEmails = control.errors['invalidEmails'];
        if (invalidEmails.length > 3) {
          return `${invalidEmails.length} adrese de email sunt invalide. Verificați formatul.`;
        } else {
          return `Adresele de email invalide: ${invalidEmails.join(', ')}. Verificați formatul.`;
        }
      }
    }

    
    return 'Valoare invalidă.';
  }
  
  // Trimite formularul de editare
  submitEditForm(): void {
    if (this.editForm.invalid) {
      // Marchează toate câmpurile ca touched pentru a afișa erorile
      this.markFormGroupTouched(this.editForm);
      this.editError = 'Vă rugăm să completați toate câmpurile obligatorii corect.';
      return;
    }
    
    this.isEditSubmitting = true;
    this.editError = '';
    this.editSuccess = '';
    
    // Pregătim datele pentru backend
    const formData = this.prepareFormData();
    
    // Extragem email-urile
    const emailsText = this.editForm.value.voter_emails || '';
    const emails = emailsText.split('\n')
      .map((email: string) => email.trim())
      .filter((email: string) => email !== '');
    
    console.log('Email-uri care vor fi procesate:', emails);
    
    // Trimitem datele către backend
    this.voteSystemService.updateVoteSystem(this.systemId, formData).subscribe({
      next: (response) => {
        console.log('Sistemul de vot a fost actualizat cu succes:', response);
        
        // După ce s-a salvat sistemul, actualizăm și email-urile
        this.voteSystemService.manageVoterEmails(this.systemId, emails).subscribe({
          next: (emailResponse) => {
            console.log('Email-urile au fost actualizate cu succes:', emailResponse);
            
            // După ce s-au salvat email-urile, trimitem token-uri pentru email-urile noi
            console.log('Se începe trimiterea token-urilor pentru sistemul', this.systemId);
            this.voteSystemService.sendVoteTokens(this.systemId).subscribe({
              next: (tokenResponse) => {
                console.log('Token-urile au fost trimise cu succes:', tokenResponse);
                this.isEditSubmitting = false;
                this.isEditing = false;
                this.editSuccess = 'Sistemul de vot a fost actualizat cu succes! Token-urile de vot au fost trimise.';
                
                // Reîncărcăm detaliile sistemului pentru a reflecta modificările
                this.loadVoteSystem();
              },
              error: (tokenError) => {
                console.error('Eroare la trimiterea token-urilor:', tokenError);
                this.isEditSubmitting = false;
                this.isEditing = false;
                this.editSuccess = 'Sistemul de vot a fost actualizat cu succes, dar a apărut o eroare la trimiterea token-urilor.';
                
                // Reîncărcăm detaliile sistemului pentru a reflecta modificările
                this.loadVoteSystem();
              }
            });
          },
          error: (emailError) => {
            console.error('Eroare la actualizarea email-urilor:', emailError);
            this.isEditSubmitting = false;
            this.isEditing = false;
            this.editSuccess = 'Sistemul de vot a fost actualizat cu succes, dar a apărut o eroare la actualizarea email-urilor.';
            
            // Reîncărcăm detaliile sistemului pentru a reflecta modificările
            this.loadVoteSystem();
          }
        });
      },
      error: (error) => {
        console.error('Eroare la actualizarea sistemului de vot:', error);
        this.isEditSubmitting = false;
        
        if (error.error && error.error.errors) {
          // Afișăm erorile de validare
          const errorMessages = [];
          for (const field in error.error.errors) {
            errorMessages.push(`${field}: ${error.error.errors[field]}`);
          }
          this.editError = errorMessages.join('\n');
        } else {
          this.editError = error.error?.error || 'A apărut o eroare la actualizarea sistemului de vot.';
        }
      }
    });
  }
  
  // Pregătește datele pentru backend
  private prepareFormData(): any {
    const formValue = this.editForm.value;
    
    // Combinăm date/time pentru start și end
    const startDate = new Date(`${formValue.start_date}T${formValue.start_time}`);
    const endDate = new Date(`${formValue.end_date}T${formValue.end_time}`);
    
    // Construim obiectul de date pentru backend
    return {
      name: formValue.name,
      description: formValue.description,
      category: formValue.category,
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
      rules: formValue.rules,
      options: formValue.options
    };
  }
  
  // Helper pentru a marca toate controalele ca touched
  markFormGroupTouched(formGroup: FormGroup) {
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
  
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      } else if (control instanceof FormArray) {
        control.controls.forEach(ctrl => {
          if (ctrl instanceof FormGroup) {
            this.markFormGroupTouched(ctrl);
          } else {
            ctrl.markAsTouched();
          }
        });
      }
    });
  }
  
  // Închide formularul de editare
  cancelEdit(): void {
    this.isEditing = false;
    this.editError = '';
    this.editSuccess = '';
  }
  
  // Deschide dialogul de confirmare pentru ștergere
  openDeleteConfirmation(): void {
    this.deleteConfirmationOpen = true;
    this.deleteError = '';
  }
  
  // Închide dialogul de confirmare pentru ștergere
  cancelDelete(): void {
    this.deleteConfirmationOpen = false;
    this.deleteError = '';
  }
  
  // Șterge sistemul de vot
  deleteVoteSystem(): void {
    this.isDeleting = true;
    this.deleteError = '';
    
    this.voteSystemService.deleteVoteSystem(this.systemId).subscribe({
      next: (response) => {
        this.isDeleting = false;
        this.deleteConfirmationOpen = false;
        
        // Afișăm un mesaj de succes și redirecționăm către lista de sisteme
        alert('Sistemul de vot a fost șters cu succes!');
        this.router.navigate(['/menu/despre/sisteme-vot']);
      },
      error: (error) => {
        this.isDeleting = false;
        this.deleteError = error.error?.error || 'A apărut o eroare la ștergerea sistemului de vot.';
      }
    });
  }

    // Metodă nouă pentru a actualiza toate informațiile relevante în timp real
    startLiveUpdates(): void {
      // Anulăm orice abonament existent
      if (this.resultsUpdateSubscription) {
        this.resultsUpdateSubscription.unsubscribe();
      }
      
      // Creăm un nou abonament care actualizează datele la fiecare 10 secunde
      this.resultsUpdateSubscription = interval(10000)
        .pipe(
          takeWhile(() => this.alive),
          switchMap(() => this.voteSystemService.getVoteSystemDetails(this.systemId))
        )
        .subscribe({
          next: (data) => {
            // Actualizăm numărul total de voturi
            this.totalVotes = data.total_votes || 0;
            
            // Actualizăm datele de sistem (pentru a reflecta orice alte modificări)
            this.voteSystem = data;
            
            // Dacă suntem în tabul de rezultate, încărcăm și datele detaliate de rezultate
            if (this.activeTab === 'results') {
              this.loadResultsData();
            }
            
            // Forțăm detectarea schimbărilor pentru a actualiza UI-ul
            this.cdr.detectChanges();
          },
          error: (error) => {
            console.error('Eroare la actualizarea datelor de sistem:', error);
          }
        });
    }

  
  startResultsUpdates(): void {
    // Anulăm orice abonament existent
    if (this.resultsUpdateSubscription) {
      this.resultsUpdateSubscription.unsubscribe();
    }
    
    // Creăm un nou abonament care actualizează rezultatele la fiecare 10 secunde
    this.resultsUpdateSubscription = interval(10000)
      .pipe(
        takeWhile(() => this.alive),
        switchMap(() => this.voteSystemService.getVoteSystemResultsUpdate(this.systemId))
      )
      .subscribe({
        next: (results) => {
          if (results.success) {
            this.totalVotes = results.total_votes;
            this.resultsData = results.results;
            this.updateCharts();
          }
        },
        error: (error) => {
          console.error('Eroare la actualizarea rezultatelor:', error);
        }
      });
  }
  
  loadResultsData(): void {
    this.voteSystemService.getVoteSystemResultsUpdate(this.systemId).subscribe({
      next: (results) => {
        if (results.success) {
          this.totalVotes = results.total_votes;
          this.resultsData = results.results;
          
          // Inițializăm graficele cu un mic delay pentru a ne asigura că DOM-ul este pregătit
          setTimeout(() => {
            this.initCharts();
          }, 100);
          
          // Inițializăm actualizarea periodică a rezultatelor
          this.startResultsUpdates();
        }
      },
      error: (error) => {
        console.error('Eroare la încărcarea rezultatelor:', error);
      }
    });
  }
  
  initCharts(): void {
    if (!this.pieChartCanvas?.nativeElement || !this.barChartCanvas?.nativeElement) {
      console.warn('Canvas-urile pentru grafice nu sunt disponibile încă.');
      return;
    }
    
    if (this.resultsData.length === 0) {
      console.warn('Nu există date pentru afișarea graficelor.');
      return;
    }

    // Pregătim datele pentru grafice
    const labels = this.resultsData.map(item => item.title);
    const values = this.resultsData.map(item => item.votes_count);
    const backgroundColors = [
      'rgba(52, 152, 219, 0.8)',
      'rgba(46, 204, 113, 0.8)',
      'rgba(155, 89, 182, 0.8)',
      'rgba(230, 126, 34, 0.8)',
      'rgba(241, 196, 15, 0.8)',
      'rgba(231, 76, 60, 0.8)',
      'rgba(52, 73, 94, 0.8)'
    ];
    
    // Asigurăm că sunt suficiente culori pentru toate opțiunile
    const colors = this.resultsData.map((_, i) => backgroundColors[i % backgroundColors.length]);
    
    try {
      // Curățăm orice grafic existent
      if (this.pieChart) {
        this.pieChart.destroy();
      }
      
      // Inițializăm graficul pie
      this.pieChart = new Chart(this.pieChartCanvas.nativeElement, {
        type: 'pie',
        data: {
          labels: labels,
          datasets: [{
            data: values,
            backgroundColor: colors,
            borderColor: 'rgba(255, 255, 255, 0.5)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: {
                color: '#fff',
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              callbacks: {
                label: (tooltipItem: any): string => {
                  const value = tooltipItem.raw;
                  const total = tooltipItem.dataset.data.reduce((a: number, b: number) => a + b, 0);
                  const percentage = Math.round((value / total) * 100);
                  return `${tooltipItem.label}: ${value} voturi (${percentage}%)`;
                }
              }
            }
          }
        }
      });
      
      // Curățăm orice grafic existent
      if (this.barChart) {
        this.barChart.destroy();
      }
      
      // Inversăm datele pentru ca opțiunile cu cele mai multe voturi să fie în partea de sus
      const reversedLabels = [...labels].reverse();
      const reversedValues = [...values].reverse();
      const reversedColors = [...colors].reverse();
      
      // Inițializăm graficul bar
      this.barChart = new Chart(this.barChartCanvas.nativeElement, {
        type: 'bar',
        data: {
          labels: reversedLabels,
          datasets: [{
            label: 'Voturi',
            data: reversedValues,
            backgroundColor: reversedColors,
            borderColor: 'rgba(255, 255, 255, 0.5)',
            borderWidth: 1
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            x: {
              ticks: {
                color: '#fff',
                font: {
                  size: 12
                }
              },
              grid: {
                color: 'rgba(255, 255, 255, 0.1)'
              }
            },
            y: {
              ticks: {
                color: '#fff',
                font: {
                  size: 12
                },
                callback: (value: any, index: number): string => {
                  // Obținem etichetele direct din array
                  const label = reversedLabels[index];
                  if (typeof label === 'string' && label.length > 20) {
                    return label.substring(0, 20) + '...';
                  }
                  return label?.toString() || '';
                }
              },
              grid: {
                color: 'rgba(255, 255, 255, 0.1)'
              }
            }
          }
        }
      });
      
      console.log('Grafice inițializate cu succes');
    } catch (error) {
      console.error('Eroare la inițializarea graficelor:', error);
    }
  }
  
  updateCharts(): void {
    if (!this.pieChart || !this.barChart || this.resultsData.length === 0) {
      return;
    }
    
    // Pregătim datele pentru grafice
    const labels = this.resultsData.map(item => item.title);
    const values = this.resultsData.map(item => item.votes_count);
    
    // Actualizăm graficul pie
    this.pieChart.data.labels = labels;
    if (this.pieChart.data.datasets && this.pieChart.data.datasets[0]) {
      this.pieChart.data.datasets[0].data = values;
    }
    this.pieChart.update();
    
    // Inversăm datele pentru graficul bar
    const reversedLabels = [...labels].reverse();
    const reversedValues = [...values].reverse();
    
    // Actualizăm graficul bar
    this.barChart.data.labels = reversedLabels;
    if (this.barChart.data.datasets && this.barChart.data.datasets[0]) {
      this.barChart.data.datasets[0].data = reversedValues;
    }
    this.barChart.update();
  }
  
  setActiveTab(tab: string): void {
    this.activeTab = tab;
    
    // Dacă utilizatorul a trecut la tab-ul de rezultate, inițializăm datele
    if (tab === 'results') {
      this.loadResultsData();
    }
  }
  
  generateShareLinks(): void {
    // Pentru link-urile distribuite folosim întotdeauna adresa IP a rețelei
    const networkUrl = `http://${environment.networkIp}:4200`;
    
    // Detectăm localhost
    this.isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    // Generăm un token simplu
    const simpleToken = btoa(`${this.systemId}-${Date.now()}`);
    
    // Link-urile distribuite folosesc adresa IP a rețelei
    this.shareLinks.directLink = `${networkUrl}/vote/${this.systemId}?token=${simpleToken}`;
    this.shareLinks.embedCode = `<iframe src="${networkUrl}/vote/${this.systemId}?token=${simpleToken}" width="100%" height="500px" frameborder="0"></iframe>`;
    this.shareLinks.qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(this.shareLinks.directLink)}`;
  }
  
  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(
      () => {
        alert('Copiat în clipboard!');
      },
      (err) => {
        console.error('Nu s-a putut copia textul:', err);
      }
    );
  }
  
  submitVote(): void {
    if (this.voteForm.invalid) return;
    
    const selectedOptionId = this.voteForm.value.selectedOption;
    console.log('ID-ul opțiunii selectate:', selectedOptionId);
    
    this.isSubmittingVote = true;
    this.voteError = '';
    
    const voteData = { option_id: selectedOptionId };
    
    this.voteSystemService.submitVote(this.systemId, voteData).subscribe({
      next: (response) => {
        this.isSubmittingVote = false;
        this.voteSubmitted = true;
        
        // Actualizăm imediat datele de rezultate după vot
        if (this.activeTab === 'results') {
          this.loadResultsData();
        }
      },
      error: (error) => {
        this.isSubmittingVote = false;
        console.error('Eroare la trimiterea votului:', error);
        this.voteError = error.error?.error || 'A apărut o eroare la trimiterea votului.';
      }
    });
  }
  
  formatDate(date: Date | string): string {
    if (!date) return '';
    
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    return dateObj.toLocaleDateString('ro-RO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  isVoteActive(): boolean {
    if (!this.voteSystem) return false;
    
    const now = new Date();
    const startDate = new Date(this.voteSystem.start_date);
    const endDate = new Date(this.voteSystem.end_date);
    
    return now >= startDate && now <= endDate;
  }
  
  getVoteProgress(): number {
    if (!this.voteSystem) return 0;
    
    const now = new Date();
    const startDate = new Date(this.voteSystem.start_date);
    const endDate = new Date(this.voteSystem.end_date);
    
    if (now < startDate) return 0;
    if (now > endDate) return 100;
    
    const totalDuration = endDate.getTime() - startDate.getTime();
    const elapsed = now.getTime() - startDate.getTime();
    
    return Math.round((elapsed / totalDuration) * 100);
  }
  
  getVoteStatusText(): string {
    if (!this.voteSystem) return '';
    
    const now = new Date();
    const startDate = new Date(this.voteSystem.start_date);
    const endDate = new Date(this.voteSystem.end_date);
    
    if (now < startDate) {
      return `Votul va începe pe ${this.formatDate(startDate)}`;
    } else if (now > endDate) {
      return `Votul s-a încheiat pe ${this.formatDate(endDate)}`;
    } else {
      return `Votul este activ până pe ${this.formatDate(endDate)}`;
    }
  }
  
  encodeURL(url: string): string {
    return encodeURIComponent(url);
  }

  getShareFacebookLink(): string {
    return 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(this.shareLinks.directLink);
  }

  getShareTwitterLink(): string {
    return 'https://twitter.com/intent/tweet?url=' + encodeURIComponent(this.shareLinks.directLink) + 
           '&text=' + encodeURIComponent('Participă la votul: ' + this.voteSystem.name);
  }

  getShareWhatsAppLink(): string {
    return 'https://wa.me/?text=' + encodeURIComponent('Participă la votul: ' + 
           this.voteSystem.name + ' ' + this.shareLinks.directLink);
  }

  getShareEmailLink(): string {
    return 'mailto:?subject=' + encodeURIComponent('Participă la votul: ' + this.voteSystem.name) + 
           '&body=' + encodeURIComponent('Te invit să participi la următorul vot: ' + 
           this.voteSystem.name + '\n\n' + this.shareLinks.directLink);
  }
  
  goBack(): void {
    this.router.navigate(['/menu/despre/sisteme-vot']);
  }
    // Verifică dacă sistemul poate fi editat
    canEdit(): boolean {
      if (!this.voteSystem) return false;
      
      // Doar sistemele în starea "pending" pot fi editate
      return this.voteSystem.status === 'pending';
    }
    
    // Obține clasa CSS pentru butonul de editare
    getEditButtonClass(): string {
      return this.canEdit() ? 'btn-primary' : 'btn-disabled';
    }
    
    // Obține textul tooltip pentru butonul de editare
    getEditButtonTooltip(): string {
      if (this.canEdit()) {
        return 'Editează detaliile sistemului de vot';
      } else {
        return 'Sistemul nu poate fi editat deoarece a început sau s-a încheiat';
      }
    }
    getStatusClass(): string {
      if (!this.voteSystem) return '';
      
      // Verificăm statusul real din backend
      switch (this.voteSystem.status) {
        case 'active': return 'status-active';
        case 'pending': return 'status-pending';
        case 'completed': return 'status-completed';
        default: return '';
      }
    }
    
    // Metodă pentru a obține textul corect al statusului
    getStatusText(): string {
      if (!this.voteSystem) return 'Necunoscut';
      
      // Verificăm statusul real din backend
      switch (this.voteSystem.status) {
        case 'active': return 'Activ';
        case 'pending': return 'În așteptare';
        case 'completed': return 'Încheiat';
        default: return this.voteSystem.status || 'Necunoscut';
      }
    }
    // Metodă pentru a obține iconița corespunzătoare statusului
getStatusIcon(): string {
  if (!this.voteSystem) return 'fa-question-circle';
  
  switch (this.voteSystem.status) {
    case 'active': return 'fa-check-circle';
    case 'pending': return 'fa-clock';
    case 'completed': return 'fa-calendar-check';
    default: return 'fa-question-circle';
  }
}



}