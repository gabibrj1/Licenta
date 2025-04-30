import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { LocalCandidatesService } from './services/local-candidates.service';
import { 
  ElectionCycle, 
  LocalElectionType, 
  LocalPosition,
  LocalElectionRule,
  SignificantCandidate,
  ImportantEvent,
  LegislationChange
} from './models/local-candidate.model';

@Component({
  selector: 'app-candidati-locali',
  templateUrl: './candidati-locali.component.html',
  styleUrls: ['./candidati-locali.component.scss']
})
export class CandidatiLocaliComponent implements OnInit, OnDestroy {
  // Date pentru afișare
  electionCycles: ElectionCycle[] = [];
  electionTypes: LocalElectionType[] = [];
  positions: LocalPosition[] = [];
  rules: LocalElectionRule[] = [];
  currentRules: LocalElectionRule[] = [];
  significantCandidates: SignificantCandidate[] = [];
  allCandidates: SignificantCandidate[] = []; // Copie pentru resetare
  importantEvents: ImportantEvent[] = [];
  legislationChanges: LegislationChange[] = [];
  
  // Filtre și opțiuni de afișare
  activeTab: 'overview' | 'rules' | 'candidates' | 'timeline' | 'legislation' = 'overview';
  selectedElectionType: number | null = null;
  selectedElectionCycle: number | null = null;
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = false;
  loadingError: string | null = null;
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(private localCandidatesService: LocalCandidatesService) { }

  ngOnInit(): void {
    this.loadInitialData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Încarcă datele inițiale
  loadInitialData(): void {
    this.isLoading = true;
    
    // Încărcăm toate datele necesare pentru pagina de overview
    this.localCandidatesService.getElectionCycles()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.electionCycles = data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea ciclurilor electorale:', error);
          this.loadingError = 'Nu s-au putut încărca ciclurile electorale. Vă rugăm să încercați din nou mai târziu.';
          this.isLoading = false;
        }
      });
      
    this.localCandidatesService.getElectionTypes()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.electionTypes = data;
        },
        error: (error) => {
          console.error('Eroare la încărcarea tipurilor de alegeri:', error);
        }
      });
      
    // Încărcăm regulile curente
    this.localCandidatesService.getRules(undefined, true)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.currentRules = data;
        },
        error: (error) => {
          console.error('Eroare la încărcarea regulilor curente:', error);
        }
      });
      
    // Încărcăm evenimentele importante
    this.localCandidatesService.getImportantEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.importantEvents = data.sort((a, b) => b.year - a.year); // Sortare descrescătoare după an
        },
        error: (error) => {
          console.error('Eroare la încărcarea evenimentelor importante:', error);
        }
      });
  }

  // Încărcarea datelor pentru fiecare tab
  loadTabData(tab: 'overview' | 'rules' | 'candidates' | 'timeline' | 'legislation'): void {
    this.activeTab = tab;
    
    switch (tab) {
      case 'rules':
        if (this.rules.length === 0) {
          this.isLoading = true;
          this.localCandidatesService.getRules()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
              next: (data) => {
                this.rules = data;
                this.isLoading = false;
              },
              error: (error) => {
                console.error('Eroare la încărcarea regulilor:', error);
                this.isLoading = false;
              }
            });
        }
        break;
        
      case 'candidates':
        if (this.significantCandidates.length === 0) {
          this.isLoading = true;
          this.localCandidatesService.getSignificantCandidates()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
              next: (data) => {
                this.significantCandidates = data;
                this.allCandidates = [...data]; // Salvăm o copie a listei complete
                this.isLoading = false;
              },
              error: (error) => {
                console.error('Eroare la încărcarea candidaților semnificativi:', error);
                this.isLoading = false;
              }
            });
        }
        break;
        
      case 'timeline':
        // Datele de evenimente sunt deja încărcate la inițializare
        break;
        
      case 'legislation':
        if (this.legislationChanges.length === 0) {
          this.isLoading = true;
          this.localCandidatesService.getLegislationChanges()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
              next: (data) => {
                this.legislationChanges = data.sort((a, b) => b.year - a.year); // Sortare descrescătoare după an
                this.isLoading = false;
              },
              error: (error) => {
                console.error('Eroare la încărcarea modificărilor legislative:', error);
                this.isLoading = false;
              }
            });
        }
        break;
    }
  }

  // Metode pentru filtrare
  filterRulesByElectionType(electionTypeId: number): void {
    this.selectedElectionType = electionTypeId;
    this.isLoading = true;
    
    this.localCandidatesService.getRules(electionTypeId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.rules = data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la filtrarea regulilor:', error);
          this.isLoading = false;
        }
      });
  }
  
  filterCandidatesByElectionCycle(electionCycleId: number): void {
    this.selectedElectionCycle = electionCycleId;
    this.isLoading = true;
    
    this.localCandidatesService.getSignificantCandidates(undefined, electionCycleId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.significantCandidates = data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la filtrarea candidaților:', error);
          this.isLoading = false;
        }
      });
  }
  
  // Metodă pentru resetarea filtrelor
  resetFilters(): void {
    this.selectedElectionType = null;
    this.selectedElectionCycle = null;
    
    if (this.activeTab === 'candidates' && this.allCandidates.length > 0) {
      // Restaurează lista completă din copia salvată
      this.significantCandidates = [...this.allCandidates];
    } else if (this.activeTab === 'rules') {
      // Reîncarcă toate regulile
      this.isLoading = true;
      this.localCandidatesService.getRules()
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (data) => {
            this.rules = data;
            this.isLoading = false;
          },
          error: (error) => {
            console.error('Eroare la încărcarea tuturor regulilor:', error);
            this.isLoading = false;
          }
        });
    } else {
      this.loadTabData(this.activeTab);
    }
  }
  
  // Metode de utilitate
  getElectionTypeName(id: number): string {
    const electionType = this.electionTypes.find(type => type.id === id);
    return electionType ? electionType.name : '';
  }
  
  getElectionCycleYear(id: number): number {
    const electionCycle = this.electionCycles.find(cycle => cycle.id === id);
    return electionCycle ? electionCycle.year : 0;
  }
  
  // Obține calea către imaginea candidatului
  getCandidateImageUrl(candidate: SignificantCandidate): string {
    // Creăm un slug din numele candidatului
    const nameSlug = candidate.name.toLowerCase()
      .replace(/ă/g, 'a').replace(/â/g, 'a').replace(/î/g, 'i')
      .replace(/ș/g, 's').replace(/ț/g, 't')
      .replace(/\s+/g, '-');
    
    // Creăm un slug din locație
    const locationSlug = candidate.location.toLowerCase()
      .replace(/ă/g, 'a').replace(/â/g, 'a').replace(/î/g, 'i')
      .replace(/ș/g, 's').replace(/ț/g, 't')
      .replace(/\s+/g, '-');
      
    // Creăm path-ul complet
    return `url(assets/images/local-candidates/${nameSlug}-${locationSlug}.jpg), url(assets/images/local-candidates/placeholder.jpg)`;
  }
}