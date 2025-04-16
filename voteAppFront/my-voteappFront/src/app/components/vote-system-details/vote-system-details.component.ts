import { Component, OnInit, OnDestroy, ViewChild, ElementRef, ChangeDetectorRef, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { VoteSystemService } from '../../services/vote-system.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
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
}