import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { VoteSystemService } from '../../services/vote-system.service';
import { environment } from '../../../src/environments/environment';
import { EChartsOption } from 'echarts';


@Component({
  selector: 'app-public-vote',
  templateUrl: './public-vote.component.html',
  styleUrls: ['./public-vote.component.scss']
})
export class PublicVoteComponent implements OnInit {
  systemId: string = '';
  voteSystem: any = null;
  isLoading = true;
  errorMessage = '';
  
  // Formular pentru vot
  voteForm: FormGroup;
  isSubmittingVote = false;
  voteSubmitted = false;
  voteError = '';
  
  // Verificare token
  requiresEmailVerification = false;
  emailVerified = false;
  tokenForm: FormGroup;
  isVerifying = false;
  tokenError = '';
  
  // Vizualizare rezultate
  showResults = false;
  
  // Setări pentru grafice
  chartOptions = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: '70%',
        center: ['50%', '50%'],
        selectedMode: 'single',
        data: [],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private voteSystemService: VoteSystemService,
    private fb: FormBuilder
  ) {
    this.voteForm = this.fb.group({
      selectedOption: ['', Validators.required]
    });
    
    // Inițializăm formularul pentru verificarea token-ului
    this.tokenForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      token: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  ngOnInit(): void {
    this.systemId = this.route.snapshot.paramMap.get('id') || '';
    
    if (!this.systemId) {
      this.errorMessage = 'ID-ul sistemului de vot lipsește.';
      this.isLoading = false;
      return;
    }
    
    // Verifică dacă există parametri în query string
    const queryParams = this.route.snapshot.queryParams;
    
    // Dacă există token și email în URL, populează formularul automat
    if (queryParams['token'] && queryParams['email']) {
      console.log('Token și email găsite în URL:', {
        token: queryParams['token'],
        email: queryParams['email']
      });
      
      // Populează formularul cu valorile din URL
      this.tokenForm.patchValue({
        token: queryParams['token'],
        email: queryParams['email']
      });
      
      // Opțional: Verifică automat token-ul
      // this.verifyToken();
    }
    
    // Verifică dacă utilizatorul a votat deja
    this.checkIfAlreadyVoted();
    
    this.loadVoteSystem();
  }

  // Verifică dacă utilizatorul a votat deja
  checkIfAlreadyVoted(): void {
    // Verifică localStorage pentru token-ul de vot
    const voteKey = `vote_confirmation_${this.systemId}`;
    const hasVoted = localStorage.getItem(voteKey);
    
    if (hasVoted) {
      this.voteSubmitted = true;
    }
  }

  loadVoteSystem(): void {
    this.isLoading = true;
    this.voteSystemService.getPublicVoteSystemDetails(this.systemId).subscribe({
      next: (data) => {
        this.voteSystem = data;
        this.isLoading = false;
        
        // Verifică dacă sistemul necesită verificare prin email
        this.requiresEmailVerification = data.require_email_verification;
        console.log('Necesită verificare email:', this.requiresEmailVerification);
        
        // Verifică dacă emailul a fost deja verificat în această sesiune
        const sessionToken = localStorage.getItem(`vote_session_${this.systemId}`);
        if (sessionToken) {
          this.emailVerified = true;
        }
        
        // Verificăm dacă putem afișa rezultatele
        this.checkIfCanShowResults();
        
        // Dacă putem afișa rezultate, încărcăm datele pentru grafic
        if (this.showResults) {
          this.updateChartData();
        }
      },
      error: (error) => {
        this.errorMessage = 'Nu s-au putut încărca detaliile sistemului de vot.';
        this.isLoading = false;
        console.error('Eroare la încărcarea detaliilor sistemului de vot:', error);
      }
    });
  }
  
  // Verifică token-ul de email
  verifyToken(): void {
    if (this.tokenForm.invalid) return;
    
    this.isVerifying = true;
    this.tokenError = '';
    
    const token = this.tokenForm.value.token.toUpperCase();
    const email = this.tokenForm.value.email;
    
    this.voteSystemService.verifyVoteToken(this.systemId, token, email).subscribe({
      next: (response) => {
        this.isVerifying = false;
        if (response.valid) {
          this.emailVerified = true;
          
          // Stocăm token-ul și email-ul pentru a-l folosi la vot
          localStorage.setItem(`vote_session_${this.systemId}`, response.session_token || '');
          localStorage.setItem(`vote_email_${this.systemId}`, email);
        } else {
          this.tokenError = response.message || 'Cod invalid. Te rugăm să verifici și să încerci din nou.';
        }
      },
      error: (error) => {
        this.isVerifying = false;
        this.tokenError = error.error?.message || 'A apărut o eroare la verificarea codului.';
        console.error('Eroare la verificarea token-ului:', error);
      }
    });
  }
  
  // Verifică dacă se pot afișa rezultatele
  checkIfCanShowResults(): void {
    if (!this.voteSystem) return;
    
    const resultVisibility = this.voteSystem.rules?.result_visibility || 'after_end';
    const now = new Date();
    const endDate = new Date(this.voteSystem.end_date);
    
    if (resultVisibility === 'realtime') {
      this.showResults = true;
    } else if (resultVisibility === 'after_vote' && this.voteSubmitted) {
      this.showResults = true;
    } else if (resultVisibility === 'after_end' && now > endDate) {
      this.showResults = true;
    } else {
      this.showResults = false;
    }
  }
  
  // Actualizează datele pentru graficul de rezultate
  updateChartData(): void {
    if (!this.voteSystem || !this.voteSystem.options) return;
    
    const chartData = this.voteSystem.options.map((option: any) => ({
      value: option.votes_count,
      name: option.title
    }));
    
    this.chartOptions.series[0].data = chartData;
    
    // Forțăm re-render-ul graficului
    this.chartOptions = { ...this.chartOptions };
  }
  
  // Trimite un vot
  submitVote(): void {
    if (this.voteForm.invalid) {
      console.error('Formular invalid pentru vot');
      return;
    }
    
    const selectedOptionId = this.voteForm.value.selectedOption;
    console.log('Opțiune selectată pentru vot:', selectedOptionId);
    
    this.isSubmittingVote = true;
    this.voteError = '';
    
    // Verifică dacă utilizatorul a votat deja
    const voteKey = `vote_confirmation_${this.systemId}`;
    if (localStorage.getItem(voteKey)) {
      this.isSubmittingVote = false;
      this.voteError = 'Se pare că ați votat deja în acest sistem de vot.';
      console.log('Vot deja înregistrat în localStorage');
      return;
    }
    
    // Pregătim datele pentru vot
    const voteData: any = {
      option_id: selectedOptionId
    };
    
    // Dacă sistemul necesită verificare prin email, adăugăm token-ul și email-ul
    if (this.requiresEmailVerification) {
      const sessionToken = localStorage.getItem(`vote_session_${this.systemId}`);
      const email = localStorage.getItem(`vote_email_${this.systemId}`);
      
      console.log('Date sesiune pentru votare:', { 
        requiresEmailVerification: this.requiresEmailVerification,
        systemId: this.systemId, 
        sessionToken, 
        email 
      });
      
      if (!sessionToken || !email) {
        this.isSubmittingVote = false;
        this.voteError = 'Sesiunea de verificare a expirat. Te rugăm să introduci din nou codul de acces.';
        this.emailVerified = false;
        console.error('Lipsă token sau email pentru vot');
        return;
      }
      
      // Adăugăm token-ul și email-ul la datele de vot
      voteData.token = sessionToken;
      voteData.email = email;
    }
    
    console.log('Trimitere date vot către server:', voteData);
    
    this.voteSystemService.submitPublicVote(this.systemId, voteData).subscribe({
      next: (response) => {
        console.log('Răspuns după trimitere vot:', response);
        this.isSubmittingVote = false;
        this.voteSubmitted = true;
        
        // Salvăm confirmarea votului în localStorage
        if (response.vote_confirmation) {
          localStorage.setItem(voteKey, response.vote_confirmation);
          console.log('Confirmare vot salvată în localStorage');
        } else {
          localStorage.setItem(voteKey, 'voted');
          console.log('Confirmare simplă de vot salvată în localStorage');
        }
        
        // Verificăm dacă putem afișa rezultatele după vot
        this.checkIfCanShowResults();
        
        // Dacă putem afișa rezultate, reîncărcăm sistemul pentru a obține voturile actualizate
        if (this.showResults) {
          this.loadPublicResults();
        }
      },
      error: (error) => {
        console.error('Eroare la trimiterea votului:', error);
        this.isSubmittingVote = false;
        
        // Tratarea specifică a mesajelor de eroare
        if (error.error && error.error.error) {
          this.voteError = error.error.error;
        } else if (error.message) {
          this.voteError = error.message;
        } else {
          this.voteError = 'A apărut o eroare la trimiterea votului.';
        }
        
        // Dacă eroarea indică un token invalid, resetăm starea de verificare
        if (this.voteError.toLowerCase().includes('token') || 
            this.voteError.toLowerCase().includes('email')) {
          console.log('Resetare stare verificare email din cauza erorii cu token/email');
          this.emailVerified = false;
          localStorage.removeItem(`vote_session_${this.systemId}`);
          localStorage.removeItem(`vote_email_${this.systemId}`);
        }
      }
    });
  }
  
  // Încarcă rezultatele actualizate
  loadPublicResults(): void {
    this.voteSystemService.getPublicVoteSystemResults(this.systemId).subscribe({
      next: (data) => {
        this.voteSystem = data;
        this.updateChartData();
      },
      error: (error) => {
        console.error('Eroare la încărcarea rezultatelor:', error);
      }
    });
  }
  
  // Verifică dacă există parametri speciali în URL
  checkUrlParameters(): void {
    const params = this.route.snapshot.queryParams;
    
    // Exemplu: Poți implementa verificări de token-uri de unică folosință sau alte metode
    if (params['token']) {
      // Verifică token-ul (implementare specifică aplicației tale)
      console.log('Token găsit în URL:', params['token']);
    }
  }
  
  // Formatează data pentru afișare
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
  
  // Verifică dacă votul este activ
  isVoteActive(): boolean {
    if (!this.voteSystem) return false;
    
    const now = new Date();
    const startDate = new Date(this.voteSystem.start_date);
    const endDate = new Date(this.voteSystem.end_date);
    
    return now >= startDate && now <= endDate;
  }
  
  // Obține textul pentru starea votului
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
  
  // Calculează progresul votului
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
}