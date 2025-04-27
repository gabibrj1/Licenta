import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from '../candidati-prezidentiali/services/presidential-candidates.service';
import { HistoricalEvent } from '../models/candidate.model';

@Component({
  selector: 'app-timeline',
  templateUrl: './timeline.component.html',
  styleUrls: ['./timeline.component.scss']
})
export class TimelineComponent implements OnInit, OnDestroy {
  events: HistoricalEvent[] = [];
  
  // Filtre
  importanceFilter: number | null = null;
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = false;
  loadingError: string | null = null;
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(private candidatesService: PresidentialCandidatesService) { }

  ngOnInit(): void {
    this.loadHistoricalEvents();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadHistoricalEvents(): void {
    this.isLoading = true;
    
    this.candidatesService.getHistoricalEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          // Sortare cronologică (crescătoare pentru timeline)
          this.events = data.sort((a, b) => a.year - b.year);
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea evenimentelor istorice:', error);
          this.loadingError = 'Nu s-au putut încărca evenimentele istorice. Vă rugăm să încercați din nou mai târziu.';
          this.isLoading = false;
        }
      });
  }
  
  applyImportanceFilter(level: number | null): void {
    this.importanceFilter = level;
  }
  
  getFilteredEvents(): HistoricalEvent[] {
    if (this.importanceFilter === null) {
      return this.events;
    }
    
    return this.events.filter(event => event.importance >= this.importanceFilter!);
  }
  
  getImportanceClass(level: number): string {
    switch (level) {
      case 3:
        return 'importance-high';
      case 2:
        return 'importance-medium';
      case 1:
        return 'importance-low';
      default:
        return '';
    }
  }
}