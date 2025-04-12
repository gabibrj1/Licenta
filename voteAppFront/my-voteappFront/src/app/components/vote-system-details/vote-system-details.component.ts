import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { VoteSystemService } from '../../services/vote-system.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { environment } from '../../../src/environments/environment';

@Component({
  selector: 'app-vote-system-details',
  templateUrl: './vote-system-details.component.html',
  styleUrls: ['./vote-system-details.component.scss']
})
export class VoteSystemDetailsComponent implements OnInit {
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
    
    this.loadVoteSystem();
  }

  loadVoteSystem(): void {
    this.isLoading = true;
    this.voteSystemService.getVoteSystemDetails(this.systemId).subscribe({
      next: (data) => {
        this.voteSystem = data;
        this.isLoading = false;
        
        // Generăm linkurile pentru share
        this.generateShareLinks();
        
        // Pregătește datele pentru grafic
        this.updateChartData();
      },
      error: (error) => {
        this.errorMessage = 'Nu s-au putut încărca detaliile sistemului de vot.';
        this.isLoading = false;
        console.error('Eroare la încărcarea detaliilor sistemului de vot:', error);
      }
    });
  }
  
  // Schimbă tab-ul activ
  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }
  
  // Generează linkuri pentru distribuire
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
  // Copiază un text în clipboard
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
  
  // Actualizează datele pentru graficul de rezultate
  updateChartData(): void {
    if (!this.voteSystem || !this.voteSystem.options) return;
    
    const chartData = this.voteSystem.options.map((option: any) => ({
      value: option.votes,
      name: option.title
    }));
    
    this.chartOptions.series[0].data = chartData;
    
    // Forțăm re-render-ul graficului (în HTML vom folosi [options]="chartOptions")
    this.chartOptions = { ...this.chartOptions };
  }
  
  // Trimite un vot
  submitVote(): void {
    if (this.voteForm.invalid) return;
    
    const selectedOptionId = this.voteForm.value.selectedOption;
    console.log('ID-ul opțiunii selectate:', selectedOptionId); // Debug
    
    this.isSubmittingVote = true;
    this.voteError = '';
    
    // Asigură-te că ai structura corectă de date pentru backend
    const voteData = { option_id: selectedOptionId };
    console.log('Date trimise către backend:', voteData); // Debug
    
    this.voteSystemService.submitVote(this.systemId, voteData).subscribe({
      next: (response) => {
        this.isSubmittingVote = false;
        this.voteSubmitted = true;
        
        // Actualizăm numărul de voturi pentru opțiunea selectată
        if (this.voteSystem && this.voteSystem.options) {
          const option = this.voteSystem.options.find((o: any) => o.id === selectedOptionId);
          if (option) {
            option.votes_count++; // Asigură-te că acest nume de proprietate corespunde cu cel din backend
            this.voteSystem.total_votes++;
            this.updateChartData();
          }
        }
      },
      error: (error) => {
        this.isSubmittingVote = false;
        console.error('Eroare la trimiterea votului:', error);
        this.voteError = error.error?.error || 'A apărut o eroare la trimiterea votului.';
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
  // Adaugă aceste metode în clasa VoteSystemDetailsComponent
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
  
  // Navighează înapoi la lista de sisteme
  goBack(): void {
    this.router.navigate(['/menu/despre/sisteme-vot']);
  }
}