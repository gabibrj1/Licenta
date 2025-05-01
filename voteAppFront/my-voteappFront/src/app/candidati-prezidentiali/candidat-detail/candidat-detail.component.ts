import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from '../candidati-prezidentiali/services/presidential-candidates.service';
import { CandidateDetail, ElectionParticipation, Controversy } from '../models/candidate.model';
import { Location } from '@angular/common';

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
  
  // Variabile pentru navigare
  previousUrl: string = '';
  returnToYear: number | null = null;
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private candidatesService: PresidentialCandidatesService,
    private location: Location
  ) { }

  ngOnInit(): void {
    // Obținem parametrii din URL
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        this.candidateSlug = params.get('slug') || '';
        
        // Verificăm dacă avem un an specificat în query params
        this.route.queryParamMap.subscribe(queryParams => {
          const year = queryParams.get('year');
          if (year) {
            this.returnToYear = parseInt(year);
          }
        });
        
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
          
          // Dacă nu a fost specificat un an în query params, dar candidatul are participări,
          // setăm returnToYear la cel mai recent an de participare (dacă e candidat istoric)
          if (!this.returnToYear && !this.candidate.is_current && this.candidate.participations && this.candidate.participations.length > 0) {
            const years = this.getParticipationYears();
            if (years.length > 0) {
              this.returnToYear = years[0]; // Primul an (cel mai recent) din lista sortată
            }
          }
          
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

  // Navigare înapoi inteligentă
  goBack(): void {
    if (this.returnToYear) {
      // Navigare către lista de candidați istorici cu anul selectat
      this.router.navigate(['/menu/candidati_prezidentiali'], { 
        queryParams: { 
          tab: 'historical',
          year: this.returnToYear 
        }
      });
    } else if (this.candidate?.is_current) {
      // Navigare către lista de candidați actuali
      this.router.navigate(['/menu/candidati_prezidentiali'], { 
        queryParams: { 
          tab: 'current'
        }
      });
    } else {
      // Navigare simplă înapoi
      this.location.back();
    }
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