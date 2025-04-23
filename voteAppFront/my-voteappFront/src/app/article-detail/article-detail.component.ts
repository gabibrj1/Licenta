import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { NewsService, NewsArticle } from '../services/news.service';
import { switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Component({
  selector: 'app-article-detail',
  templateUrl: './article-detail.component.html',
  styleUrls: ['./article-detail.component.scss']
})
export class ArticleDetailComponent implements OnInit {
  article: NewsArticle | null = null;
  relatedArticles: NewsArticle[] = [];
  loading = true;
  error = false;
  private baseUrl = environment.apiUrl;
  
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private newsService: NewsService,
    private titleService: Title
  ) { }

  ngOnInit(): void {
    // Abonează-te la schimbările de parametri pentru a reactiva la navigarea între articole conexe
    this.route.paramMap.subscribe(params => {
      const slug = params.get('slug');
      if (slug) {
        this.loadArticle(slug);
      } else {
        this.router.navigate(['/menu/news']);
      }
    });
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
  detectImageOrientation() {
    if (this.article && this.article.image_url) {
      const img = new Image();
      img.onload = () => {
        const container = document.querySelector('.article-detail-container');
        if (container) {
          // Elimină orice clase de orientare existente
          container.classList.remove('landscape-image', 'portrait-image', 'high-quality-image');
          
          // Adaugă clasa potrivită în funcție de raportul aspectului
          if (img.width > img.height) {
            container.classList.add('landscape-image');
          } else if (img.height > img.width) {
            container.classList.add('portrait-image');
          }
          
          // Verifică dacă imaginea are rezoluție înaltă
          if (img.width > 1200 || img.height > 900) {
            container.classList.add('high-quality-image');
          }
        }
      };
      img.src = this.article.image_url;
    }
  }


  loadArticle(slug: string): void {
    this.loading = true;
    this.error = false;
    
    // Folosim noul endpoint pentru a obține detaliile complete ale articolului
    this.newsService.getArticleDetail(slug)
      .pipe(
        switchMap(article => {
          // Setăm articolul curent
          this.article = article;
          this.titleService.setTitle(`${article.title} | SmartVote`);

          setTimeout(() => this.detectImageOrientation(), 10);
          
          // Apoi obținem articolele conexe din aceeași categorie
          if (article.category && article.category.slug) {
            return this.newsService.getLatestNews(5, article.category.slug);
          }
          return of([]);
        })
      )
      .subscribe(
        relatedArticles => {
          // Filtrăm articolul curent din lista de articole conexe
          if (this.article) {
            this.relatedArticles = relatedArticles.filter(a => a.id !== this.article?.id);
          }
          this.loading = false;
        },
        error => {
          console.error('Eroare la încărcarea articolului sau a articolelor conexe', error);
          this.error = true;
          this.loading = false;
        }
      );
  }

  // Funcție pentru navigarea înapoi la pagina de știri
  goBackToNews(): void {
    this.router.navigate(['/menu/news']);
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
      return dateString;
    }
  }

  // Helper pentru a gestiona conținutul articolului
  getParagraphs(): string[] {
    if (!this.article || !this.article.content) {
      return ['Conținutul detaliat al articolului va fi disponibil în curând.'];
    }
    return this.article.content.split('\n\n');
  }
}