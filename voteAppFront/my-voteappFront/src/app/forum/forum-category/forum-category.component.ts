import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { ForumService, Category, Topic, PaginatedResponse } from '../../services/forum.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-forum-category',
  templateUrl: './forum-category.component.html',
  styleUrls: ['./forum-category.component.scss']
})
export class ForumCategoryComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Date pentru categorie
  categorySlug: string = '';
  categoryId: number = 0;
  category: Category | null = null;
  topics: Topic[] = [];
  currentPage = 1;
  totalTopics = 0;
  totalPages = 0;
  
  // Stare
  loading = true;
  error = false;
  
  // Sortare
  sortOptions = [
    { value: 'activity', label: 'Activitate recentă' },
    { value: 'newest', label: 'Cele mai noi' },
    { value: 'views', label: 'Cele mai vizualizate' },
    { value: 'responses', label: 'Cele mai multe răspunsuri' }
  ];
  currentSort = 'activity';
  
  // User data
  isLoggedIn = false;
  userAvatars: { [key: string]: string } = {};
  
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private forumService: ForumService,
    private authService: AuthService,
    private titleService: Title
  ) { }

  ngOnInit(): void {
    // Verificăm starea de autentificare
    this.isLoggedIn = this.authService.isAuthenticated();
    
    // Generăm avatare pentru utilizatori
    this.generateUserAvatars();
    
    // Obținem parametrii din rută
    this.route.paramMap.subscribe(params => {
      this.categorySlug = params.get('slug') || '';
      
      // Obținem ID-ul categoriei din query params
      this.route.queryParamMap.subscribe(queryParams => {
        const categoryId = queryParams.get('id');
        if (categoryId) {
          this.categoryId = parseInt(categoryId, 10);
          this.loadCategory();
          this.loadTopics();
        } else {
          // Încercăm să găsim categoria după slug
          this.loadCategoryBySlug();
        }
      });
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  /**
   * Încarcă categoria după ID
   */
  loadCategory(): void {
    this.forumService.getCategory(this.categoryId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (category) => {
          this.category = category;
          this.titleService.setTitle(`${category.name} | Forum SmartVote`);
        },
        error: (error) => {
          console.error('Eroare la încărcarea categoriei:', error);
          this.error = true;
        }
      });
  }
  
  /**
   * Încarcă categoria după slug (când nu avem ID)
   */
  loadCategoryBySlug(): void {
    this.forumService.getCategories()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (categories) => {
          const category = categories.find(c => c.slug === this.categorySlug);
          if (category) {
            this.category = category;
            this.categoryId = category.id;
            this.titleService.setTitle(`${category.name} | Forum SmartVote`);
            this.loadTopics();
          } else {
            console.error('Categoria nu a fost găsită');
            this.error = true;
          }
        },
        error: (error) => {
          console.error('Eroare la încărcarea categoriilor:', error);
          this.error = true;
        }
      });
  }
  
  /**
   * Încarcă subiectele din categoria curentă
   */
  loadTopics(): void {
    this.loading = true;
    this.error = false;
    
    this.forumService.getTopicsByCategory(this.categoryId, this.currentPage)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: PaginatedResponse<Topic>) => {
          this.topics = response.results;
          this.totalTopics = response.count;
          this.totalPages = Math.ceil(response.count / 20); // 20 este page_size-ul
          this.loading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea subiectelor:', error);
          this.error = true;
          this.loading = false;
        }
      });
  }
  
  /**
   * Încarcă subiectele sortate
   */
  sortTopics(sortBy: string): void {
    this.currentSort = sortBy;
    this.currentPage = 1; // Reset la prima pagină
    this.loadTopicsWithSorting();
  }
  
  /**
   * Încarcă subiectele cu sortare
   */
  loadTopicsWithSorting(): void {
    this.loading = true;
    this.error = false;
    
    this.forumService.getTopics({
      page: this.currentPage,
      category: this.categoryId,
      sort: this.currentSort as any
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: PaginatedResponse<Topic>) => {
          this.topics = response.results;
          this.totalTopics = response.count;
          this.totalPages = Math.ceil(response.count / 20);
          this.loading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea subiectelor:', error);
          this.error = true;
          this.loading = false;
        }
      });
  }
  
  /**
   * Navighează la pagina anterioară
   */
  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadTopicsWithSorting();
    }
  }
  
  /**
   * Navighează la pagina următoare
   */
  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadTopicsWithSorting();
    }
  }
  
  /**
   * Navighează la o pagină specifică
   */
  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadTopicsWithSorting();
    }
  }
  
  /**
   * Generează paginația
   */
  getPagination(): number[] {
    const pages: number[] = [];
    const totalPages = this.totalPages;
    const currentPage = this.currentPage;
    
    // Logică pentru a afișa maxim 5 pagini
    if (totalPages <= 5) {
      // Afișăm toate paginile
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Afișăm maxim 5 pagini
      if (currentPage <= 3) {
        // Suntem la început
        for (let i = 1; i <= 5; i++) {
          pages.push(i);
        }
      } else if (currentPage >= totalPages - 2) {
        // Suntem la sfârșit
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // Suntem la mijloc
        for (let i = currentPage - 2; i <= currentPage + 2; i++) {
          pages.push(i);
        }
      }
    }
    
    return pages;
  }
  
  /**
   * Navighează la un subiect
   */
  navigateToTopic(topicId: number, topicSlug: string): void {
    this.router.navigate(['/menu/forum/topic', topicSlug], { queryParams: { id: topicId } });
  }
  
  /**
   * Inițiază crearea unui nou subiect în categoria curentă
   */
  createNewTopic(): void {
    if (!this.isLoggedIn) {
      alert('Trebuie să fiți autentificat pentru a crea un subiect nou.');
      this.router.navigate(['/auth']);
      return;
    }
    
    this.router.navigate(['/menu/forum/new-topic'], { queryParams: { category: this.categoryId } });
  }
  
  /**
   * Generează avatare pentru utilizatori
   */
  generateUserAvatars(): void {
    const colors = [
      '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
      '#1abc9c', '#d35400', '#34495e', '#16a085', '#27ae60'
    ];
    
    // Pentru generare de avatare bazate pe email
    const userData = this.authService.getUserData();
    const userEmail = userData?.email || '';
    const userInitials = this.getInitialsFromEmail(userEmail);
    
    // Mockup pentru avatare utilizatori
    this.userAvatars = {
      'admin@smartvote.ro': this.getInitialsAvatar('ADM', colors[0]),
      'moderator@smartvote.ro': this.getInitialsAvatar('MOD', colors[1]),
      'alex.popescu@smartvote.ro': this.getInitialsAvatar('AP', colors[2]),
      'maria.ionescu@smartvote.ro': this.getInitialsAvatar('MI', colors[3]),
      'andrei.vasilescu@smartvote.ro': this.getInitialsAvatar('AV', colors[4]),
      'elena.dumitrescu@smartvote.ro': this.getInitialsAvatar('ED', colors[5]),
      'default': this.getInitialsAvatar('U', colors[9]),
    };
    
    // Adăugăm avatarul utilizatorului curent
    if (userEmail) {
      this.userAvatars[userEmail] = this.getInitialsAvatar(userInitials, colors[Math.floor(Math.random() * colors.length)]);
    }
  }
  
  /**
   * Obține inițialele din adresa de email
   */
  getInitialsFromEmail(email: string): string {
    if (!email) return 'U';
    
    // Extrage partea din stânga @ și încearcă să găsească inițiale
    const namePart = email.split('@')[0];
    
    // Dacă conține punct, presupunem format nume.prenume@...
    if (namePart.includes('.')) {
      const parts = namePart.split('.');
      return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
    }
    
    // Altfel, folosim prima literă sau primele două
    return (namePart.length > 1) ? 
      namePart.substring(0, 2).toUpperCase() : 
      namePart.charAt(0).toUpperCase() + 'U';
  }

  /**
   * Generează un avatar cu inițiale
   */
  getInitialsAvatar(initials: string, bgColor: string): string {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    canvas.width = 200;
    canvas.height = 200;
    
    if (context) {
      // Background
      context.fillStyle = bgColor;
      context.fillRect(0, 0, canvas.width, canvas.height);
      
      // Text
      context.fillStyle = 'white';
      context.font = 'bold 80px Arial';
      context.textAlign = 'center';
      context.textBaseline = 'middle';
      context.fillText(initials, canvas.width / 2, canvas.height / 2);
    }
    
    return canvas.toDataURL('image/png');
  }

  /**
   * Obține avatarul unui utilizator după email
   */
  getUserAvatar(email: string): string {
    return this.userAvatars[email] || this.userAvatars['default'];
  }
  
  /**
   * Format pentru timestamp relativ
   */
  getTimeAgo(dateString: string): string {
    return this.forumService.getTimeAgo(dateString);
  }
}