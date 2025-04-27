import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from '../candidati-prezidentiali/services/presidential-candidates.service';
import { Controversy, ElectionYear } from '../models/candidate.model';

@Component({
  selector: 'app-controversies',
  templateUrl: './controversies.component.html',
  styleUrls: ['./controversies.component.scss']
})
export class ControversiesComponent implements OnInit, OnDestroy {
  controversies: Controversy[] = [];
  electionYears: ElectionYear[] = [];
  
  // Filtre
  selectedYear: number | null = null;
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = false;
  loadingError: string | null = null;
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(private candidatesService: PresidentialCandidatesService) { }

  ngOnInit(): void {
    this.loadControversies();
    this.loadElectionYears();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadControversies(year?: number): void {
    this.isLoading = true;
    this.isLoading = true;
    
    const params: any = {};
    if (year) {
      params.election_year = year;
    }
    
    this.candidatesService.getControversies(undefined, year)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.controversies = data.sort((a, b) => 
            new Date(b.date).getTime() - new Date(a.date).getTime() // Sortare descrescătoare după dată
          );
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea controverselor:', error);
          this.loadingError = 'Nu s-au putut încărca controversele. Vă rugăm să încercați din nou mai târziu.';
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

  applyYearFilter(year: number | null): void {
    this.selectedYear = year;
    this.loadControversies(year || undefined);
  }

  getFormattedDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ro-RO', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }
}