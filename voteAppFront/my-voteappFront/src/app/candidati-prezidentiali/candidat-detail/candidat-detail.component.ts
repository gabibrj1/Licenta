import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from '../candidati-prezidentiali/services/presidential-candidates.service';
import { CandidateDetail, ElectionParticipation, Controversy } from '../models/candidate.model';

@Component({
  selector: 'app-candidat-detail',
  templateUrl: './candidat-detail.component.html',
  styleUrls: ['./candidat-detail.component.scss']
})
export class CandidatDetailComponent implements OnInit, OnDestroy {
  candidateSlug: string = '';
  candidate: CandidateDetail | null = null;
  
  // Gruparea participărilor după an electoral
  participationsByYear: {[key: number]: ElectionParticipation[]} = {};
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = false;
  loadingError: string | null = null;
  
  // Tab-uri pentru detalii
  activeTab: 'biography' | 'electoral-history' | 'controversies' = 'biography';
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private candidatesService: PresidentialCandidatesService
  ) { }

  ngOnInit(): void {
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        this.candidateSlug = params.get('slug') || '';
        this.loadCandidateDetails();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadCandidateDetails(): void {
    if (!this.candidateSlug) return;
    
    this.isLoading = true;
    this.candidatesService.getCandidateBySlug(this.candidateSlug)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.candidate = data;
          this.organizeParticipationsByYear();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea detaliilor candidatului:', error);
          this.loadingError = 'Nu s-au putut încărca detaliile candidatului. Vă rugăm să încercați din nou mai târziu.';
          this.isLoading = false;
        }
      });
  }

  organizeParticipationsByYear(): void {
    if (!this.candidate?.participations) return;
    
    this.participationsByYear = {};
    
    this.candidate.participations.forEach(participation => {
      if (!this.participationsByYear[participation.year]) {
        this.participationsByYear[participation.year] = [];
      }
      this.participationsByYear[participation.year].push(participation);
    });
  }

  changeTab(tab: 'biography' | 'electoral-history' | 'controversies'): void {
    this.activeTab = tab;
  }

  // Metode auxiliare pentru afișare
  getParticipationYears(): number[] {
    return Object.keys(this.participationsByYear)
      .map(year => parseInt(year))
      .sort((a, b) => b - a); // Sortare descrescătoare
  }

  getAgeFromBirthDate(birthDate: string | null): number | null {
    if (!birthDate) return null;
    
    const birth = new Date(birthDate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDifference = today.getMonth() - birth.getMonth();
    
    if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
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