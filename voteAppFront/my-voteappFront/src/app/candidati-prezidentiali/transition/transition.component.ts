import { Component, OnInit, OnDestroy, ViewEncapsulation } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from '../candidati-prezidentiali/services/presidential-candidates.service';
import { 
  PresidentialCandidate, 
  HistoricalEvent,
  Controversy 
} from '../models/candidate.model';

@Component({
  selector: 'app-transition',
  templateUrl: './transition.component.html',
  styleUrls: ['./transition.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class TransitionComponent implements OnInit, OnDestroy {
  // Date pentru afișare
  ceausescu: PresidentialCandidate | null = null;
  transitionEvents: HistoricalEvent[] = [];
  transitionControversies: Controversy[] = [];
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = true;
  loadingError: string | null = null;
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(private candidatesService: PresidentialCandidatesService) { }

  ngOnInit(): void {
    console.log('TransitionComponent initialized');
    this.loadCeausescuData();
    this.loadTransitionEvents();
    this.loadTransitionControversies();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Încarcă datele despre Nicolae Ceaușescu
  loadCeausescuData(): void {
    this.isLoading = true;
    
    this.candidatesService.getCandidates()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (candidates) => {
          // Căutăm un candidat cu numele "Ceaușescu" sau "ceausescu" (case insensitive)
          this.ceausescu = candidates.find(c => 
            c.name.toLowerCase().includes('ceausescu') || 
            c.name.toLowerCase().includes('ceaușescu')
          ) || null;
          
          console.log('Candidat Ceaușescu găsit:', this.ceausescu);
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea datelor despre Ceaușescu:', error);
          this.isLoading = false;
          this.loadingError = 'Eroare la încărcarea datelor despre Nicolae Ceaușescu.';
        }
      });
  }

  // Încarcă evenimentele legate de tranziție
  loadTransitionEvents(): void {
    this.candidatesService.getHistoricalEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (events) => {
          // Filtrăm local evenimentele din perioada 1965-1990
          this.transitionEvents = events
            .filter(event => event.year >= 1965 && event.year <= 1990)
            .sort((a, b) => a.year - b.year); // Sortare cronologică
          
          console.log('Evenimente de tranziție filtrate:', this.transitionEvents.length);
        },
        error: (error) => {
          console.error('Eroare la încărcarea evenimentelor de tranziție:', error);
          this.loadingError = 'Eroare la încărcarea evenimentelor istorice.';
        }
      });
  }

  // Încarcă controversele legate de tranziție
  loadTransitionControversies(): void {
    this.candidatesService.getControversies()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (controversies) => {
          // Filtrăm local controversele din perioada de tranziție
          this.transitionControversies = controversies
            .filter(controversy => {
              const date = new Date(controversy.date);
              const year = date.getFullYear();
              return year >= 1965 && year <= 1990;
            })
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()); // Sortare cronologică
          
          console.log('Controverse de tranziție filtrate:', this.transitionControversies.length);
        },
        error: (error) => {
          console.error('Eroare la încărcarea controverselor din perioada de tranziție:', error);
          this.loadingError = 'Eroare la încărcarea controverselor.';
        }
      });
  }
}