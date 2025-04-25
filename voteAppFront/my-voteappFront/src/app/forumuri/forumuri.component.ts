import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { ForumService, Category, Topic, ForumStats, SearchResult } from '../services/forum.service';
import { Subject } from 'rxjs';
import { takeUntil, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { FormControl } from '@angular/forms';

@Component({
  selector: 'app-forum',
  templateUrl: './forumuri.component.html',
  styleUrls: ['./forumuri.component.scss']
})
export class ForumuriComponent implements OnInit, OnDestroy {
  // State management
  private destroy$ = new Subject<void>();
  
  // Date pentru forum
  categories: Category[] = [];
  forumStats: ForumStats | null = null;
  recentTopics: Topic[] = [];
  popularTopics: Topic[] = [];
  
  // State flags
  loading = {
    categories: true,
    stats: true,
    search: false
  };
  
  error = {
    categories: false,
    stats: false,
    search: false
  };
  
  // Date pentru utilizator
  isLoggedIn = false;
  unreadNotifications = 0;
  
  // Cache pentru imagini de profil
  userAvatars: { [key: string]: string } = {};
  
  // Căutare
  searchControl = new FormControl('');
  searchResults: SearchResult | null = null;
  isSearching = false;
  
  constructor(
    private forumService: ForumService,
    private authService: AuthService,
    private router: Router,
    private titleService: Title
  ) { }

  ngOnInit(): void {
    this.titleService.setTitle('Forum | SmartVote');
    
    // Verificăm starea de autentificare
    this.isLoggedIn = this.authService.isAuthenticated();
    
    // Încarcă datele inițiale
    this.loadCategories();
    this.loadForumStats();
    
    // Încarcă notificările (dacă utilizatorul e autentificat)
    if (this.isLoggedIn) {
      this.loadUnreadNotificationsCount();
    }
    
    // Generăm avatare pentru utilizatori
    this.generateUserAvatars();
    
    // Setăm ascultător pentru căutare
    this.searchControl.valueChanges.pipe(
      takeUntil(this.destroy$),
      debounceTime(300),
      distinctUntilChanged()
    ).subscribe(value => {
      if (value && value.length >= 3) {
        this.searchForum(value);
      } else {
        this.searchResults = null;
        this.isSearching = false;
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Încarcă categoriile de forum
   */
  loadCategories(): void {
    this.loading.categories = true;
    this.error.categories = false;
    
    this.forumService.getCategories()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (categories) => {
          this.categories = categories;
          this.loading.categories = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea categoriilor:', error);
          this.error.categories = true;
          this.loading.categories = false;
        }
      });
  }

  /**
   * Încarcă statisticile forumului
   */
  loadForumStats(): void {
    this.loading.stats = true;
    this.error.stats = false;
    
    this.forumService.getForumStats()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (stats) => {
          this.forumStats = stats;
          this.recentTopics = stats.recent_topics.slice(0, 5);
          this.popularTopics = stats.popular_topics.slice(0, 5);
          this.loading.stats = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea statisticilor:', error);
          this.error.stats = true;
          this.loading.stats = false;
        }
      });
  }

  /**
   * Încarcă numărul de notificări necitite
   */
  loadUnreadNotificationsCount(): void {
    this.forumService.getUnreadNotificationsCount()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.unreadNotifications = data.count;
        },
        error: (error) => {
          console.error('Eroare la încărcarea notificărilor:', error);
        }
      });
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
   * Caută în forum
   */
  searchForum(query: string): void {
    if (!query || query.length < 3) return;
    
    this.isSearching = true;
    this.loading.search = true;
    this.error.search = false;
    
    this.forumService.search(query)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (results) => {
          this.searchResults = results;
          this.loading.search = false;
        },
        error: (error) => {
          console.error('Eroare la căutare:', error);
          this.error.search = true;
          this.loading.search = false;
        }
      });
  }

  /**
   * Închide rezultatele căutării
   */
  clearSearch(): void {
    this.searchControl.setValue('');
    this.searchResults = null;
    this.isSearching = false;
  }

  /**
   * Navighează la pagina unei categorii
   */
  navigateToCategory(categoryId: number, categorySlug: string): void {
    this.router.navigate(['/menu/forum/category', categorySlug], { queryParams: { id: categoryId } });
  }

  /**
   * Navighează la pagina unui subiect
   */
  navigateToTopic(topicId: number, topicSlug: string): void {
    this.router.navigate(['/menu/forum/topic', topicSlug], { queryParams: { id: topicId } });
  }

  /**
   * Navighează la pagina de notificări
   */
  navigateToNotifications(): void {
    this.router.navigate(['/menu/forum/notifications']);
  }

  /**
   * Format pentru timestamp relativ
   */
  getTimeAgo(dateString: string): string {
    return this.forumService.getTimeAgo(dateString);
  }

  /**
   * Inițiază crearea unui nou subiect
   */
  createNewTopic(): void {
    if (!this.isLoggedIn) {
      alert('Trebuie să fiți autentificat pentru a crea un subiect nou.');
      this.router.navigate(['/auth']);
      return;
    }
    
    this.router.navigate(['/menu/forum/new-topic']);
  }
}