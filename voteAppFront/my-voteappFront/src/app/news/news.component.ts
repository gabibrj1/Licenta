import { Component, OnInit, OnDestroy } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { NewsService, NewsArticle, ExternalNewsArticle, ElectionAnalytics } from '../services/news.service';
import { forkJoin, of, Subject } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, finalize, takeUntil } from 'rxjs/operators';
import { environment } from '../../src/environments/environment';

@Component({
  selector: 'app-news',
  templateUrl: './news.component.html',
  styleUrls: ['./news.component.scss']
})
export class NewsComponent implements OnInit, OnDestroy {

  // base url pentru imagini
  private baseUrl = environment.apiUrl;

  // Știrile din aplicație
  featuredArticles: NewsArticle[] = [];
  latestNews: NewsArticle[] = [];
  latestAnalysis: NewsArticle[] = [];
  
  // Știri externe
  externalNews: ExternalNewsArticle[] = [];
  
  // Variabile pentru starea aplicației
  newsLoading = true;
  externalNewsLoading = true;
  analyticsLoading = true;
  newsError = false;
  externalNewsError = false;
  analyticsError = false;
  
  // Categorii și filtre
  selectedCategory = 'all';
  selectedType = 'all';
  
  // Analize electorale
  electionAnalytics: ElectionAnalytics[] = [];
  
  // Pentru debounce și cleanup
  private filterChanges = new Subject<void>();
  private destroy$ = new Subject<void>();
  
  // Comparații între sisteme de vot
  votingSystems = [
    {
      name: 'SmartVote',
      features: {
        security: 95,
        accessibility: 90,
        transparency: 96,
        speed: 98,
        cost: 85
      },
      description: 'Sistemul SmartVote folosește tehnologii avansate de recunoaștere facială și criptare pentru a asigura identitatea utilizatorilor și securitatea votului.'
    },
    {
      name: 'Voatz',
      features: {
        security: 85,
        accessibility: 75,
        transparency: 80,
        speed: 90,
        cost: 70
      },
      description: 'Voatz utilizează blockchain pentru securizarea voturilor, dar are limitări în ceea ce privește verificarea și transparența.'
    },
    {
      name: 'Democracy Live',
      features: {
        security: 80,
        accessibility: 88,
        transparency: 75,
        speed: 85,
        cost: 78
      },
      description: 'Democracy Live oferă bună accesibilitate, dar are vulnerabilități în procesul de verificare a identității.'
    },
    {
      name: 'E-stonia',
      features: {
        security: 90,
        accessibility: 85,
        transparency: 90,
        speed: 95,
        cost: 75
      },
      description: 'Sistemul estonian este unul dintre cele mai mature, cu peste 15 ani de implementare și îmbunătățiri continue.'
    }
  ];
  
  // Riscuri și soluții
  securityRisks = [
    {
      risk: 'Atacuri de tip phishing',
      solution: 'Autentificare multi-factor și recunoaștere facială',
      description: 'SmartVote folosește verificarea identității în mai multe etape, inclusiv recunoaștere facială și scanarea documentelor oficiale.'
    },
    {
      risk: 'Manipularea voturilor',
      solution: 'Criptare end-to-end și înregistrare securizată',
      description: 'Toate voturile sunt criptate înainte de transmitere și sunt înregistrate în baze de date securizate cu audit trails.'
    },
    {
      risk: 'Atacuri DDoS',
      solution: 'Infrastructură distribuită și protecție împotriva DDoS',
      description: 'Sistemul este proiectat pentru a rezista la atacuri de tip Distributed Denial of Service prin utilizarea unei infrastructuri robuste și scalabile.'
    },
    {
      risk: 'Manipulare de către insideri',
      solution: 'Separarea responsabilităților și audit independent',
      description: 'Nicio persoană nu are acces complet la sistem, iar auditurile independente verifică integritatea procesului.'
    },
    {
      risk: 'Pierderea anonimității',
      solution: 'Separarea identității de votul propriu-zis',
      description: 'După verificarea identității, votul este complet separat de datele personale, asigurând anonimitatea.'
    }
  ];

  constructor(
    private newsService: NewsService,
    private titleService: Title
  ) { }

  ngOnInit(): void {
    this.titleService.setTitle('Știri și Analize | SmartVote');
    this.loadAllData();
    
    // Configurează debounce pentru filtrare
    this.filterChanges.pipe(
      takeUntil(this.destroy$),
      debounceTime(300), // Așteaptă 300ms între apeluri
      distinctUntilChanged()
    ).subscribe(() => {
      this.loadNewsData();
    });
  }
  
  ngOnDestroy(): void {
    // Curățare pentru a preveni memory leaks
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadAllData(): void {
    this.loadNewsData();
    this.loadExternalNews();
    this.loadElectionAnalytics();
  }

  getCategoryIcon(category: string): string {
    const iconMap: { [key: string]: string } = {
      'elections': '#elections-icon',
      'politics': '#politics-icon',
      'technology': '#technology-icon',
      'security': '#security-icon',
      'analysis': '#analysis-icon',
      'opinion': '#opinion-icon',
      'news': '#news-icon',
      'external': '#external-news-icon',
      'general': '#featured-icon'
    };
    
    return iconMap[category] || '#featured-icon';
  }
  getImageUrl(imagePath: string): string {
    if (!imagePath) {
      return '/assets/images/news/default.jpg';
    }
    
    // Dacă e deja un URL complet (include protocol sau domeniu)
    if (imagePath.startsWith('http')) {
      return imagePath;
    }
    
    // Dacă începe cu /media, adaugă domeniul backend-ului
    if (imagePath.startsWith('/media/')) {
      return `http://127.0.0.1:8000${imagePath}`;
    }
    
    // Pentru nume simple de fișiere, construiește calea completă
    if (!imagePath.includes('/')) {
      return `http://127.0.0.1:8000/media/news/images/${imagePath}`;
    }
    
    // Pentru alte cazuri
    return `http://127.0.0.1:8000${imagePath.startsWith('/') ? '' : '/'}${imagePath}`;
  }

  loadNewsData(): void {
    this.newsLoading = true;
    this.newsError = false;
    
    console.log(`Loading news with category=${this.selectedCategory}, type=${this.selectedType}`);
    
    // Utilizăm forkJoin pentru a face toate cererile în paralel
    forkJoin({
      featured: this.newsService.getLatestNews(5, this.selectedCategory, this.selectedType).pipe(
        catchError(err => {
          console.error('Eroare la încărcarea articolelor promovate', err);
          return of([]);
        })
      ),
      latest: this.newsService.getLatestNews(8, this.selectedCategory, 'news').pipe(
        catchError(err => {
          console.error('Eroare la încărcarea ultimelor știri', err);
          return of([]);
        })
      ),
      analysis: this.newsService.getLatestNews(5, this.selectedCategory, 'analysis').pipe(
        catchError(err => {
          console.error('Eroare la încărcarea analizelor', err);
          return of([]);
        })
      )
    }).pipe(
      takeUntil(this.destroy$)
    ).subscribe(
      (results) => {
        this.featuredArticles = results.featured;
        this.latestNews = results.latest;
        this.latestAnalysis = results.analysis;
        
        // Logare pentru debugging
        console.log(`Loaded ${this.featuredArticles.length} featured articles`);
        console.log(`Loaded ${this.latestNews.length} latest news`);
        console.log(`Loaded ${this.latestAnalysis.length} analysis articles`);
        
        this.newsLoading = false;
      },
      (error) => {
        console.error('Error combining news data streams', error);
        this.newsError = true;
        this.newsLoading = false;
      }
    );
  }

  loadExternalNews(): void {
    this.externalNewsLoading = true;
    this.externalNewsError = false;
    
    this.newsService.getExternalNews().subscribe(
      (data) => {
        this.externalNews = data;
        this.externalNewsLoading = false;
        console.log(`Loaded ${this.externalNews.length} external news items`);
      },
      (error) => {
        console.error('Error loading external news', error);
        this.externalNewsError = true;
        this.externalNewsLoading = false;
      }
    );
  }

  loadElectionAnalytics(): void {
    this.analyticsLoading = true;
    this.analyticsError = false;
    
    this.newsService.getElectionAnalytics().subscribe(
      (data) => {
        this.electionAnalytics = data;
        this.analyticsLoading = false;
        console.log(`Loaded ${this.electionAnalytics.length} analytics datasets`);
      },
      (error) => {
        console.error('Error loading analytics', error);
        this.analyticsError = true;
        this.analyticsLoading = false;
      }
    );
  }

  filterNews(): void {
    console.log(`Filtering news: category=${this.selectedCategory}, type=${this.selectedType}`);
    // Apelăm direct loadNewsData în loc de a folosi debounce, care poate cauza probleme
    this.loadNewsData();
  }
  
  getCategoryName(slug: string): string {
    const categoryMap = {
      'elections': 'Alegeri',
      'politics': 'Politică',
      'technology': 'Tehnologie',
      'security': 'Securitate'
    };
    return categoryMap[slug as keyof typeof categoryMap] || slug;
  }

  getTypeName(type: 'news' | 'analysis' | 'opinion' | string): string {
    const typeMap = {
      'news': 'Știri',
      'analysis': 'Analize',
      'opinion': 'Opinii'
    };
    return typeMap[type as 'news' | 'analysis' | 'opinion'] || type;
  }

  resetCategoryFilter(): void {
    this.selectedCategory = 'all';
    this.filterNews();
  }

  resetTypeFilter(): void {
    this.selectedType = 'all';
    this.filterNews();
  }

  resetAllFilters(): void {
    this.selectedCategory = 'all';
    this.selectedType = 'all';
    this.filterNews();
  }

  formatDate(dateString: string): string {
    if (!dateString) {
      return '';
    }
    
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ro-RO', { 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric' 
      });
    } catch (error) {
      console.error('Error formatting date:', error);
      return dateString; // Returnează string-ul original în caz de eroare
    }
  }
}