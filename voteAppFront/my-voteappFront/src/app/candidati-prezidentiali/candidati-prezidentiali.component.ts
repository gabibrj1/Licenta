import { Component, OnInit, OnDestroy } from '@angular/core';
import { forkJoin, map, Subject, takeUntil } from 'rxjs';
import { PresidentialCandidatesService } from './candidati-prezidentiali/services/presidential-candidates.service';
import { 
  PresidentialCandidate, 
  ElectionYear, 
  HistoricalEvent,
  ElectionParticipation 
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
  
  // Date pentru maparea candidaților la ani electorali
  candidatesByYear: Map<number, PresidentialCandidate[]> = new Map();
  
  // Filtre și opțiuni de afișare
  showCurrent: boolean = true;
  activeTab: 'current' | 'historical' | 'timeline' | 'controversies' | 'media-influence' | 'transition' = 'current';
  selectedYear: number | null = null;
  
  // Variabile pentru starea încărcării datelor
  isLoading: boolean = false;
  loadingError: string | null = null;
  
  // Subject pentru gestionarea dezabonărilor
  private destroy$ = new Subject<void>();

  // Mapare pentru slug-urile candidaților cu diacritice
  readonly CANDIDATE_IMAGE_SLUGS: {[key: string]: string} = {
    // Candidați cu diacritice care trebuie corectați
    'Călin Georgescu': 'calin-georgescu',
    'Viorica Dăncilă': 'viorica-dancila',
    'Nicolae Ciucă': 'nicolae-ciuca',
    'Kelemen Hunor': 'kelemen-hunor',
    'Mircea Geoană': 'mircea-geoana',
    'Traian Băsescu': 'traian-basescu',
    'Adrian Năstase': 'adrian-nastase',
    'Nicușor Dan': 'nicusor-dan',
    'Lavinia Șandru': 'lavinia-sandru',
    'Radu Câmpeanu': 'radu-campeanu',
    'Ion Rațiu': 'ion-ratiu',

    // Candidați din perioada 1990-2024
    'Klaus Iohannis': 'klaus-iohannis',
    'Victor Ponta': 'victor-ponta',
    'Marcel Ciolacu': 'marcel-ciolacu',
    'Elena Lasconi': 'elena-lasconi', 
    'George Simion': 'george-simion',
    'Crin Antonescu': 'crin-antonescu',
    'Mircea Diaconu': 'mircea-diaconu',
    'Dan Barna': 'dan-barna',
    'Corneliu Vadim Tudor': 'corneliu-vadim-tudor',
    'Ion Iliescu': 'ion-iliescu',
    'Theodor Stolojan': 'theodor-stolojan',
    'Emil Constantinescu': 'emil-constantinescu',
    'Petre Roman': 'petre-roman',
    'Gheorghe Funar': 'gheorghe-funar'
  };

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

  // Metodă înlocuită de loadHistoricalCandidateData()
  loadAllCandidates(): void {
    this.loadHistoricalCandidateData();
  }

  // Încarcă toți candidații și organizează datele pentru filtrare
  loadHistoricalCandidateData(): void {
    this.isLoading = true;
    
    // Solicităm mai întâi anii electorali (dacă nu sunt deja încărcați)
    if (this.electionYears.length === 0) {
      this.candidatesService.getElectionYears()
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (years) => {
            this.electionYears = years;
            this.loadCandidateParticipationsByYear();
          },
          error: (error) => {
            console.error('Eroare la încărcarea anilor electorali:', error);
            this.isLoading = false;
            this.loadingError = 'Nu s-au putut încărca anii electorali. Vă rugăm să încercați din nou.';
          }
        });
    } else {
      this.loadCandidateParticipationsByYear();
    }
  }
  
  // Încarcă participările pentru fiecare an electoral
  loadCandidateParticipationsByYear(): void {
    // Creăm un array de observabile, câte unul pentru fiecare an electoral
    const observables = this.electionYears.map(year => 
      this.candidatesService.getElectionYear(year.year).pipe(
        map(electionYearDetail => ({
          year: year.year,
          participations: electionYearDetail.participations
        }))
      )
    );
    
    // Combinăm toate observabilele și așteptăm ca toate să se finalizeze
    forkJoin(observables)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (results) => {
          // Populăm Map-ul candidatesByYear
          results.forEach(result => {
            const yearCandidates: PresidentialCandidate[] = [];
            
            // Pentru fiecare participare, creăm un obiect de tip PresidentialCandidate
            result.participations.forEach(participation => {
              // Verificăm dacă candidatul există deja în listă pentru a evita duplicatele
              const existingCandidate = yearCandidates.find(c => c.id === participation.candidate);
              
              if (!existingCandidate) {
                // Creăm un obiect candidat cu datele din participare
                const candidateSlug = this.getSlugForName(participation.candidate_name);
                const candidate: PresidentialCandidate = {
                  id: participation.candidate,
                  name: participation.candidate_name,
                  party: participation.candidate_party,
                  slug: candidateSlug, // Folosim slug-ul corect
                  is_current: false,
                  biography: '', // Va fi completat când se accesează detaliile
                  photo_url: null,
                  birth_date: null,
                  education: null,
                  political_experience: null,
                  participations: [participation]
                };
                
                yearCandidates.push(candidate);
              } else {
                // Adăugăm participarea la candidatul existent
                if (!existingCandidate.participations) {
                  existingCandidate.participations = [];
                }
                existingCandidate.participations.push(participation);
              }
            });
            
            // Stocăm candidații pentru anul respectiv
            this.candidatesByYear.set(result.year, yearCandidates);
          });
          
          // Combinăm toți candidații într-o singură listă
          this.candidates = Array.from(this.candidatesByYear.values())
            .flat()
            .filter((value, index, self) => 
              index === self.findIndex((t) => t.id === value.id)
            );
          
          this.isLoading = false;
          
          // Dacă este selectat un an, afișăm candidații pentru acel an
          if (this.selectedYear) {
            this.filterCandidatesByElectionYear(this.selectedYear);
          }
          
          // Afișăm în consolă pentru debugging
          console.log('Candidați după ani electorali:', this.candidatesByYear);
        },
        error: (error) => {
          console.error('Eroare la încărcarea datelor despre candidați:', error);
          this.loadingError = 'Nu s-au putut încărca datele despre candidați. Vă rugăm să încercați din nou.';
          this.isLoading = false;
        }
      });
  }
  
  /**
   * Obține slug-ul pentru un nume de candidat
   * @param name Numele candidatului
   * @returns Slug-ul potrivit
   */
  getSlugForName(name: string): string {
    // Verifică dacă există în maparea predefinită
    if (this.CANDIDATE_IMAGE_SLUGS[name]) {
      return this.CANDIDATE_IMAGE_SLUGS[name];
    }
    
    // Altfel, generează un slug
    return this.generateSlug(name);
  }
  
  /**
   * Generează un slug compatibil cu cel generat în backend
   * @param name Numele pentru care se generează slug-ul
   * @returns Slug-ul generat
   */
  generateSlug(name: string): string {
    // Înlocuiește diacriticele cu echivalentele fără diacritice
    const withoutDiacritics = name
      .replace(/ă/g, 'a')
      .replace(/â/g, 'a')
      .replace(/î/g, 'i')
      .replace(/ș/g, 's')
      .replace(/ț/g, 't')
      .replace(/Ă/g, 'A')
      .replace(/Â/g, 'A')
      .replace(/Î/g, 'I')
      .replace(/Ș/g, 'S')
      .replace(/Ț/g, 'T');
    
    // Aplică restul transformărilor pentru slug
    return withoutDiacritics
      .toLowerCase()
      .replace(/[^\w\s-]/g, '') // Elimină caracterele speciale
      .replace(/\s+/g, '-')     // Înlocuiește spațiile cu -
      .replace(/-+/g, '-')      // Elimină - multiple consecutive
      .trim();                   // Elimină spațiile de la început și sfârșit
  }

  /**
   * Obține URL-ul imaginii pentru un candidat
   * @param candidate Candidatul pentru care se obține imaginea
   * @param year Anul electoral (opțional, pentru candidații istorici)
   * @returns URL-ul complet pentru imaginea candidatului
   */
  getCandidateImageUrl(candidate: PresidentialCandidate, year?: number): string {
    // Folosește slug-ul din mapare dacă există, altfel generează unul
    const slug = this.getSlugForName(candidate.name);
    
    // Lista candidaților care au imagini specifice pentru anumite alegeri
    const multipleElectionCandidates: {[key: string]: number[]} = {
      'klaus-iohannis': [2014, 2019],
      'kelemen-hunor': [2014, 2019],
      'traian-basescu': [2004, 2009],
      'ion-iliescu': [1990, 1992, 1996, 2000],
      'emil-constantinescu': [1992, 1996],
      'corneliu-vadim-tudor': [2000, 2004]
    };
    
    // Pentru candidații care apar în mai multe alegeri, putem folosi și anul
    if (year && multipleElectionCandidates[slug] && multipleElectionCandidates[slug].includes(year)) {
      console.log(`Încercăm să încărcăm imaginea specifică pentru ${slug} din anul ${year}`);
      return `url(assets/images/candidates/${slug}-${year}.jpg), url(assets/images/candidates/${slug}.jpg), url(assets/images/candidates/placeholder.jpg)`;
    }
    
    // Încearcă să folosească imaginea de bază sau fallback la placeholder
    console.log(`Încercăm să încărcăm imaginea generică pentru ${slug}`);
    return `url(assets/images/candidates/${slug}.jpg), url(assets/images/candidates/placeholder.jpg)`;
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
  changeTab(tab: 'current' | 'historical' | 'timeline' | 'controversies' | 'media-influence' | 'transition'): void {
    this.activeTab = tab;
    
    // Încarcă datele necesare pentru tab-ul selectat
    if (tab === 'historical' && (this.candidates.length === 0 || this.candidatesByYear.size === 0)) {
      this.loadHistoricalCandidateData();
    }
  }

  // Filtrare candidați după an electoral
  filterCandidatesByElectionYear(year: number): PresidentialCandidate[] {
    // Folosim Map-ul precomputat pentru a găsi candidații pentru anul selectat
    return this.candidatesByYear.get(year) || [];
  }
  
  // Metodă pentru setarea anului selectat
  setSelectedYear(year: number): void {
    this.selectedYear = year;
  }
}