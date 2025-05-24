import { Component, OnInit, OnDestroy, Inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CsvDownloadService } from '../services/csv-download.service';
import { Subscription } from 'rxjs';

export interface DownloadStatus {
  available: boolean;
  data_count: number;
  vote_type: string;
  location: string;
  round_type: string;
  estimated_file_size: string;
}

@Component({
  selector: 'app-csv-download',
  templateUrl: './csv-download.component.html',
  styleUrls: ['./csv-download.component.scss']
})
export class CsvDownloadComponent implements OnInit, OnDestroy {
  
  // Parametri actuali
  currentLocation: string = 'romania';
  currentRound: string = 'tur1_2024';
  
  // Stare componenta
  isLoading: boolean = false;
  isDownloading: boolean = false;
  error: string = '';
  downloadStatus: DownloadStatus | null = null;
  
  // Informații despre runde
  availableRounds = [
    {
      id: 'tur1_2024',
      name: 'Tur 1 Alegeri Prezidențiale 2024',
      description: 'Date finale din primul tur al alegerilor prezidențiale'
    },
    {
      id: 'tur2_2024',
      name: 'Tur 2 Alegeri Prezidențiale 2024 (ANULAT)',
      description: 'Turul 2 a fost anulat - nu există date disponibile'
    },
    {
      id: 'tur_activ',
      name: 'Tur Activ',
      description: 'Date live din turul de alegeri activ în acest moment'
    }
  ];
  
  private routeSubscription?: Subscription;
  
  constructor(
    @Inject(CsvDownloadService) private csvDownloadService: CsvDownloadService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // Ascultă schimbările de parametri din rută
    this.routeSubscription = this.route.queryParams.subscribe(params => {
      this.currentLocation = params['location'] || 'romania';
      this.currentRound = params['round'] || 'tur1_2024';
      
      this.checkDownloadStatus();
    });
  }

  ngOnDestroy(): void {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  checkDownloadStatus(): void {
    this.isLoading = true;
    this.error = '';
    
    this.csvDownloadService.getDownloadStatus(this.currentLocation, this.currentRound)
      .subscribe({
        next: (status) => {
          this.downloadStatus = status;
          this.isLoading = false;
        },
        error: (error) => {
          this.error = 'Eroare la verificarea disponibilității datelor: ' + (error.error?.message || error.message);
          this.isLoading = false;
        }
      });
  }

  downloadCSV(): void {
    if (!this.downloadStatus?.available) {
      return;
    }
    
    this.isDownloading = true;
    this.error = '';
    
    console.log(`Început descărcare CSV pentru: ${this.currentLocation}, tur: ${this.currentRound}`);
    
    this.csvDownloadService.downloadCSV(this.currentLocation, this.currentRound).subscribe({
      next: (blob: Blob) => {
        // Creează URL pentru blob
        const url = window.URL.createObjectURL(blob);
        
        // Creează un link temporar pentru descărcare
        const link = document.createElement('a');
        link.href = url;
        link.download = this.generateFileName();
        
        // Adaugă link-ul la document, click și remove
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Eliberează memoria
        window.URL.revokeObjectURL(url);
        
        console.log(`CSV descărcat cu succes: ${link.download}`);
        this.isDownloading = false;
      },
      error: (error) => {
        console.error('Eroare la descărcarea CSV:', error);
        this.error = 'Eroare la descărcarea fișierului CSV: ' + (error.error?.message || 'Încearcă din nou.');
        this.isDownloading = false;
      }
    });
  }

  private generateFileName(): string {
    const locationName = this.currentLocation === 'romania' ? 'Romania' : 'Strainatate';
    
    let roundName: string;
    switch (this.currentRound) {
      case 'tur1_2024':
        roundName = 'Tur1_Prezidentiale_2024';
        break;
      case 'tur2_2024':
        roundName = 'Tur2_Prezidentiale_2024_ANULAT';
        break;
      case 'tur_activ':
        roundName = 'Vot_Live';
        break;
      default:
        roundName = 'Prezenta';
    }
    
    const timestamp = new Date().toISOString()
      .slice(0, 16)
      .replace(/[-:T]/g, '')
      .replace(/(\d{8})(\d{4})/, '$1_$2');
    
    return `prezenta_${locationName}_${roundName}_${timestamp}.csv`;
  }

  getRoundInfo() {
    return this.availableRounds.find(r => r.id === this.currentRound);
  }

  getLocationDisplayName(): string {
    return this.currentLocation === 'romania' ? 'România' : 'Străinătate';
  }

  formatNumber(num: number): string {
    if (!num && num !== 0) return '0';
    return num.toLocaleString('ro-RO');
  }

  refreshStatus(): void {
    this.checkDownloadStatus();
  }
}