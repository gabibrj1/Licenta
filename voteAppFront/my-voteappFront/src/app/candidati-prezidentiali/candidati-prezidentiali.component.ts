import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from './candidati-prezidentiali/services/presidential-candidates.service';
import { 
  PresidentialCandidate, 
  ElectionYear, 
  HistoricalEvent 
} from './models/candidate.model';

@Component({
  selector: 'app-candidati-prezidentiali',
  templateUrl: './candidati-prezidentiali.component.html',
  styleUrls: ['./candidati-prezidentiali.component.scss']
})
export class CandidatiPrezidentialiComponent implements OnInit, OnDestroy {
  // Date pentru afișare
  candidates: PresidentialCandidate[] = [];
  currentCandidates: PresidentialCandidate[] = [];
  electionYears: ElectionYear[] = [];
  historicalEvents: HistoricalEvent[] = [];
  
  // Filtre și opțiuni de afișare
  showCurrent: boolean = true;
  activeTab: 'current' | 'historical' | 'timeline' | 'controversies' | 'media-influence' = 'current';
  selectedYear: number | null = null; // Adăugat selectedYear
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = false;
  loadingError: string | null = null;
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(private candidatesService: PresidentialCandidatesService) { }

  ngOnInit(): void {
    this.loadCurrentCandidates();
    this.loadElectionYears();
    this.loadHistoricalEvents();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Încarcă candidații actuali (2025)
  loadCurrentCandidates(): void {
    this.isLoading = true;
    this.candidatesService.getCandidates(true)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.currentCandidates = data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea candidaților actuali:', error);
          this.loadingError = 'Nu s-au putut încărca candidații. Vă rugăm să încercați din nou mai târziu.';
          this.isLoading = false;
        }
      });
  }

  // Încarcă toți candidații
  loadAllCandidates(): void {
    this.isLoading = true;
    this.candidatesService.getCandidates()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.candidates = data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea tuturor candidaților:', error);
          this.loadingError = 'Nu s-au putut încărca candidații. Vă rugăm să încercați din nou mai târziu.';
          this.isLoading = false;
        }
      });
  }

  // Încarcă anii electorali
  loadElectionYears(): void {
    this.candidatesService.getElectionYears()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.electionYears = data;
        },
        error: (error) => {
          console.error('Eroare la încărcarea anilor electorali:', error);
        }
      });
  }

  // Încarcă evenimentele istorice
  loadHistoricalEvents(): void {
    this.candidatesService.getHistoricalEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.historicalEvents = data.sort((a, b) => b.year - a.year); // Sortare descrescătoare după an
        },
        error: (error) => {
          console.error('Eroare la încărcarea evenimentelor istorice:', error);
        }
      });
  }

  // Metode pentru schimbarea filelor
  changeTab(tab: 'current' | 'historical' | 'timeline' | 'controversies' | 'media-influence'): void {
    this.activeTab = tab;
    
    // Încarcă datele necesare pentru tab-ul selectat
    if (tab === 'historical' && this.candidates.length === 0) {
      this.loadAllCandidates();
    }
  }

  // Filtrare candidați după an electoral
  filterCandidatesByElectionYear(year: number): PresidentialCandidate[] {
    if (!this.candidates || this.candidates.length === 0) {
      return [];
    }
    // Folosim filtrul cu verificare pentru participations
    return this.candidates.filter(candidate => 
      candidate.participations && candidate.participations.some(p => p.year === year)
    );
  }
  
  // Metodă pentru setarea anului selectat
  setSelectedYear(year: number): void {
    this.selectedYear = year;
  }
}