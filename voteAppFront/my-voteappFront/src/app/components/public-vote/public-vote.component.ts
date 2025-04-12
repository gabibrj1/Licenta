import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { VoteSystemService } from '../../services/vote-system.service';
import { environment } from '../../../src/environments/environment';

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
  }

  ngOnInit(): void {
    this.systemId = this.route.snapshot.paramMap.get('id') || '';
    
    if (!this.systemId) {
      this.errorMessage = 'ID-ul sistemului de vot lipsește.';
      this.isLoading = false;
      return;
    }
    
    // Verifică dacă există parametri speciali în URL
    this.checkUrlParameters();

    // Detectează accesul din rețea
    this.detectNetworkAccess();
    
    this.loadVoteSystem();
  }
  detectNetworkAccess(): void {
    const isNetworkAccess = window.location.hostname === environment.networkIp;
    
    if (isNetworkAccess) {
      console.log('Acces din rețeaua locală detectat, folosim adresa IP a rețelei pentru API');
    }
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

  loadVoteSystem(): void {
    this.isLoading = true;
    this.voteSystemService.getPublicVoteSystemDetails(this.systemId).subscribe({
      next: (data) => {
        this.voteSystem = data;
        this.isLoading = false;
        
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
    if (this.voteForm.invalid) return;
    
    const selectedOptionId = this.voteForm.value.selectedOption;
    
    this.isSubmittingVote = true;
    this.voteError = '';
    
    this.voteSystemService.submitPublicVote(this.systemId, { option_id: selectedOptionId }).subscribe({
      next: (response) => {
        this.isSubmittingVote = false;
        this.voteSubmitted = true;
        
        // Verificăm dacă putem afișa rezultatele după vot
        this.checkIfCanShowResults();
        
        // Dacă putem afișa rezultate, reîncărcăm sistemul pentru a obține voturile actualizate
        if (this.showResults) {
          this.loadPublicResults();
        }
      },
      error: (error) => {
        this.isSubmittingVote = false;
        console.error('Eroare la trimiterea votului:', error);
        this.voteError = error.error?.error || 'A apărut o eroare la trimiterea votului.';
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