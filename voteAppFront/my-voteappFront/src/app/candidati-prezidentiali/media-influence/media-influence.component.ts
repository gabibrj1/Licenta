import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from '../candidati-prezidentiali/services/presidential-candidates.service';
import { MediaInfluence, ElectionYear } from '../models/candidate.model';

@Component({
  selector: 'app-media-influence',
  templateUrl: './media-influence.component.html',
  styleUrls: ['./media-influence.component.scss']
})
export class MediaInfluenceComponent implements OnInit, OnDestroy {
  mediaInfluences: MediaInfluence[] = [];
  electionYears: ElectionYear[] = [];
  
  // Filtre
  selectedMediaType: string | null = null;
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = false;
  loadingError: string | null = null;
  
  // Opțiuni pentru tipuri de media
  mediaTypes = [
    { value: null, label: 'Toate' },
    { value: 'traditional', label: 'Mass-media tradițională' },
    { value: 'social', label: 'Social media' },
    { value: 'online', label: 'Media online' },
    { value: 'other', label: 'Altele' }
  ];
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(private candidatesService: PresidentialCandidatesService) { }

  ngOnInit(): void {
    this.loadMediaInfluences();
    this.loadElectionYears();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMediaInfluences(mediaType?: string): void {
    this.isLoading = true;
    
    this.candidatesService.getMediaInfluences(mediaType || undefined)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.mediaInfluences = data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea influențelor media:', error);
          this.loadingError = 'Nu s-au putut încărca influențele media. Vă rugăm să încercați din nou mai târziu.';
          this.isLoading = false;
        }
      });
  }

  loadElectionYears(): void {
    this.candidatesService.getElectionYears()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.electionYears = data.sort((a, b) => b.year - a.year); // Sortare descrescătoare
        },
        error: (error) => {
          console.error('Eroare la încărcarea anilor electorali:', error);
        }
      });
  }

  applyMediaTypeFilter(type: string | null): void {
    this.selectedMediaType = type;
    this.loadMediaInfluences(type || undefined);
  }

  // Metode pentru filtrare și grupare
  getMediaInfluencesByYear(year: number): MediaInfluence[] {
    return this.mediaInfluences.filter(influence => influence.election_year === year);
  }
  
  getImpactLevelClass(level: number): string {
    switch (level) {
      case 3:
        return 'impact-high';
      case 2:
        return 'impact-medium';
      case 1:
        return 'impact-low';
      default:
        return '';
    }
  }
}