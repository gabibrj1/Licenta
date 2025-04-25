import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, throwError, of } from 'rxjs';
import { catchError, retry, tap, map } from 'rxjs/operators';
import { environment } from '../../src/environments/environment';
import { AuthService } from './auth.service';

// Actualizăm interfețele pentru a folosi email în loc de username

export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  color?: string;
  topic_count: number;
  post_count: number;
  last_topic?: {
    id: number;
    title: string;
    slug: string;
    last_activity: string;
    author: User;
  };
}


export interface Topic {
  id: number;
  title: string;
  slug: string;
  content?: string;
  category: {  // Schimbăm de la number la obiect
    id: number;
    name: string;
    slug: string;
  };
  category_name?: string;
  author: User;
  is_pinned: boolean;
  is_closed: boolean;
  is_approved?: boolean;
  views_count: number;
  created_at: string;
  updated_at?: string;
  last_activity: string;
  post_count: number;
  last_post_date?: string;
  last_post_author?: User;
  posts?: Post[];
}

export interface Post {
  id: number;
  author: User;
  content: string;
  is_solution: boolean;
  created_at: string;
  updated_at: string;
  reaction_count?: number;
  has_attachments?: boolean;
  reactions?: Reaction[];
  attachments?: Attachment[];
}

export interface Reaction {
  id: number;
  user: User;
  reaction_type: string;
  created_at: string;
}


export interface Attachment {
  id: number;
  file: string;
  filename: string;
  file_type?: string;
  file_size: number;
  created_at: string;
}

export interface Notification {
  id: number;
  notification_type: string;
  topic: {
    id: number;
    slug: string;
    title: string;
  };
  topic_title?: string;
  post?: number;
  post_preview?: string;
  is_read: boolean;
  created_at: string;
  topic_slug?: string;
  topic_id?: number;
}
export interface NotificationPreferences {
  notify_replies: boolean;
  notify_mentions: boolean;
  notify_topic_replies: boolean;
}

export interface NewsletterStatus {
  subscribed: boolean;
  email?: string;
}

export interface ForumStats {
  stats: {
    topic_count: number;
    post_count: number;
    user_count: number;
    last_activity: string;
  };
  recent_topics: Topic[];
  popular_topics: Topic[];
}

export interface SearchResult {
  topics: Topic[];
  posts: Post[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({
  providedIn: 'root'
})
export class ForumService {
  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) { }

  // Detectează tipul de acces (rețea sau local)
  private getApiUrl(): string {
    // Dacă URL-ul conține adresa IP a rețelei, folosim networkApiUrl
    if (window.location.hostname === environment.networkIp) {
      return environment.networkApiUrl;
    }
    
    // Detecție explicită pentru a forța URL-ul de rețea când e necesar
    const isNetworkAccess = 
      window.location.hostname !== 'localhost' && 
      window.location.hostname !== '127.0.0.1';
      
    if (isNetworkAccess) {
      console.log('Detectat acces din rețea, folosim networkApiUrl pentru forum');
      return environment.networkApiUrl;
    }
    
    return this.apiUrl;
  }

  // METODE PENTRU CATEGORII
  
  /**
   * Obține lista tuturor categoriilor active
   */
  getCategories(): Observable<Category[]> {
    return this.http.get<Category[]>(`${this.getApiUrl()}forum/categories/`)
      .pipe(
        retry(1),
        tap(categories => console.log(`Obținut ${categories.length} categorii`)),
        catchError(this.handleError<Category[]>('getCategories', []))
      );
  }

  /**
   * Obține o categorie specifică după ID
   */
  getCategory(categoryId: number): Observable<Category> {
    return this.http.get<Category>(`${this.getApiUrl()}forum/categories/${categoryId}/`)
      .pipe(
        retry(1),
        catchError(this.handleError<Category>('getCategory'))
      );
  }

  /**
   * Obține toate subiectele dintr-o categorie
   */
  getTopicsByCategory(categoryId: number, page: number = 1, pageSize: number = 20): Observable<PaginatedResponse<Topic>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
      
    return this.http.get<PaginatedResponse<Topic>>(`${this.getApiUrl()}forum/categories/${categoryId}/topics/`, { params })
      .pipe(
        retry(1),
        catchError(this.handleError<PaginatedResponse<Topic>>('getTopicsByCategory', { count: 0, next: null, previous: null, results: [] }))
      );
  }

  // METODE PENTRU SUBIECTE (TOPICS)
  
  /**
   * Obține o listă paginată de subiecte cu opțiuni de filtrare
   */
  getTopics(params: {
    page?: number,
    pageSize?: number,
    category?: number,
    author?: number,
    search?: string,
    sort?: 'newest' | 'activity' | 'views' | 'responses'
  } = {}): Observable<PaginatedResponse<Topic>> {
    let httpParams = new HttpParams()
      .set('page', (params.page || 1).toString())
      .set('page_size', (params.pageSize || 20).toString());
      
    if (params.category) {
      httpParams = httpParams.set('category', params.category.toString());
    }
    
    if (params.author) {
      httpParams = httpParams.set('author', params.author.toString());
    }
    
    if (params.search) {
      httpParams = httpParams.set('search', params.search);
    }
    
    if (params.sort) {
      httpParams = httpParams.set('sort', params.sort);
    }
    
    return this.http.get<PaginatedResponse<Topic>>(`${this.getApiUrl()}forum/topics/`, { params: httpParams })
      .pipe(
        retry(1),
        catchError(this.handleError<PaginatedResponse<Topic>>('getTopics', { count: 0, next: null, previous: null, results: [] }))
      );
  }

  /**
   * Obține un subiect specific după ID
   */
  getTopic(topicId: number): Observable<Topic> {
    return this.http.get<Topic>(`${this.getApiUrl()}forum/topics/${topicId}/`)
      .pipe(
        map(topic => ({
          ...topic,
          // Asigură-te că category este întotdeauna un obiect
          category: topic.category || {id: 0, name: 'Necategorizat', slug: 'necategorizat'}
        })),
        catchError(this.handleError<Topic>('getTopic'))
      );
  }
  

  /**
   * Obține un subiect specific după slug
   */
  getTopicBySlug(slug: string): Observable<Topic> {
    return this.http.get<Topic>(`${this.getApiUrl()}forum/topics/${slug}/`)
      .pipe(
        retry(1),
        catchError(this.handleError<Topic>('getTopicBySlug'))
      );
  }

  /**
   * Creează un nou subiect
   */
  createTopic(topicData: {
    title: string,
    content: string,
    category: number
  }): Observable<Topic> {
    return this.http.post<Topic>(`${this.getApiUrl()}forum/topics/`, topicData)
      .pipe(
        catchError(this.handleError<Topic>('createTopic'))
      );
  }

  /**
   * Actualizează un subiect existent
   */
  updateTopic(topicId: number, topicData: {
    title?: string,
    content?: string,
    category?: number
  }): Observable<Topic> {
    return this.http.patch<Topic>(`${this.getApiUrl()}forum/topics/${topicId}/`, topicData)
      .pipe(
        catchError(this.handleError<Topic>('updateTopic'))
      );
  }

  /**
   * Obține subiectele recente
   */
  getRecentTopics(): Observable<Topic[]> {
    return this.http.get<Topic[]>(`${this.getApiUrl()}forum/topics/recent/`)
      .pipe(
        retry(1),
        catchError(this.handleError<Topic[]>('getRecentTopics', []))
      );
  }

  /**
   * Obține subiectele populare
   */
  getPopularTopics(): Observable<Topic[]> {
    return this.http.get<Topic[]>(`${this.getApiUrl()}forum/topics/popular/`)
      .pipe(
        retry(1),
        catchError(this.handleError<Topic[]>('getPopularTopics', []))
      );
  }

  /**
   * Închide un subiect
   */
  closeTopic(topicId: number): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/topics/${topicId}/close/`, {})
      .pipe(
        catchError(this.handleError<any>('closeTopic'))
      );
  }

  /**
   * Redeschide un subiect
   */
  reopenTopic(topicId: number): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/topics/${topicId}/reopen/`, {})
      .pipe(
        catchError(this.handleError<any>('reopenTopic'))
      );
  }

  /**
   * Fixează un subiect
   */
  pinTopic(topicId: number): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/topics/${topicId}/pin/`, {})
      .pipe(
        catchError(this.handleError<any>('pinTopic'))
      );
  }

  /**
   * Anulează fixarea unui subiect
   */
  unpinTopic(topicId: number): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/topics/${topicId}/unpin/`, {})
      .pipe(
        catchError(this.handleError<any>('unpinTopic'))
      );
  }

  // METODE PENTRU POSTĂRI (POSTS)
  
  /**
   * Obține o listă paginată de postări pentru un subiect
   */
  getPostsByTopic(topicId: number, page: number = 1, pageSize: number = 20): Observable<PaginatedResponse<Post>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString())
      .set('topic', topicId.toString());
      
    return this.http.get<PaginatedResponse<Post>>(`${this.getApiUrl()}forum/posts/`, { params })
      .pipe(
        retry(1),
        catchError(this.handleError<PaginatedResponse<Post>>('getPostsByTopic', { count: 0, next: null, previous: null, results: [] }))
      );
  }

  /**
   * Obține o postare specifică după ID
   */
  getPost(postId: number): Observable<Post> {
    return this.http.get<Post>(`${this.getApiUrl()}forum/posts/${postId}/`)
      .pipe(
        retry(1),
        catchError(this.handleError<Post>('getPost'))
      );
  }

  /**
   * Creează o postare nouă în cadrul unui subiect
   */
  createPost(topicId: number, content: string): Observable<Post> {
    let params = new HttpParams().set('topic', topicId.toString());
    
    return this.http.post<Post>(`${this.getApiUrl()}forum/posts/`, { content }, { params })
      .pipe(
        catchError(this.handleError<Post>('createPost'))
      );
  }

  /**
   * Actualizează o postare existentă
   */
  updatePost(postId: number, content: string): Observable<Post> {
    return this.http.patch<Post>(`${this.getApiUrl()}forum/posts/${postId}/`, { content })
      .pipe(
        catchError(this.handleError<Post>('updatePost'))
      );
  }

  /**
   * Marchează o postare ca soluție
   */
  markAsSolution(postId: number): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/posts/${postId}/mark_solution/`, {})
      .pipe(
        catchError(this.handleError<any>('markAsSolution'))
      );
  }

  /**
   * Adaugă o reacție la o postare
   */
  reactToPost(postId: number, reactionType: string): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/posts/${postId}/react/`, { reaction_type: reactionType })
      .pipe(
        catchError(this.handleError<any>('reactToPost'))
      );
  }

  // METODE PENTRU ATAȘAMENTE
  
  /**
   * Încarcă un atașament pentru o postare
   */
  uploadAttachment(postId: number, file: File): Observable<Attachment> {
    const formData = new FormData();
    formData.append('file', file);
    
    let params = new HttpParams().set('post', postId.toString());
    
    return this.http.post<Attachment>(`${this.getApiUrl()}forum/attachments/`, formData, { params })
      .pipe(
        catchError(this.handleError<Attachment>('uploadAttachment'))
      );
  }

  /**
   * Șterge un atașament
   */
  deleteAttachment(attachmentId: number): Observable<any> {
    return this.http.delete<any>(`${this.getApiUrl()}forum/attachments/${attachmentId}/`)
      .pipe(
        catchError(this.handleError<any>('deleteAttachment'))
      );
  }

  // METODE PENTRU NOTIFICĂRI
  
  /**
   * Obține toate notificările utilizatorului
   */
  getNotifications(): Observable<Notification[]> {
    return this.http.get<Notification[]>(`${this.getApiUrl()}forum/notifications/`)
      .pipe(
        retry(1),
        catchError(this.handleError<Notification[]>('getNotifications', []))
      );
  }

  /**
   * Obține numărul de notificări necitite
   */
  getUnreadNotificationsCount(): Observable<{ count: number }> {
    // Verifică dacă utilizatorul este autentificat - dacă nu, returnează 0 notificări
    if (!this.authService.getAccessToken()) {
      return of({ count: 0 });
    }
    
    return this.http.get<{ count: number }>(`${this.getApiUrl()}forum/notifications/unread_count/`)
      .pipe(
        retry(1),
        catchError(error => {
          console.error('Eroare la obținerea notificărilor:', error);
          return of({ count: 0 });
        })
      );
  }

  /**
   * Marchează o notificare ca citită
   */
  markNotificationAsRead(notificationId: number): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/notifications/${notificationId}/mark_read/`, {})
      .pipe(
        catchError(this.handleError<any>('markNotificationAsRead'))
      );
  }

  /**
   * Marchează toate notificările ca citite
   */
  markAllNotificationsAsRead(): Observable<any> {
    return this.http.post<any>(`${this.getApiUrl()}forum/notifications/mark_all_read/`, {})
      .pipe(
        catchError(this.handleError<any>('markAllNotificationsAsRead'))
      );
  }
  /**
 * Obține preferințele de notificări ale utilizatorului
 */
getNotificationPreferences(): Observable<NotificationPreferences> {
  return this.http.get<NotificationPreferences>(`${this.getApiUrl()}forum/user/notification-preferences/`)
    .pipe(
      retry(1),
      catchError(this.handleError<NotificationPreferences>('getNotificationPreferences', {
        notify_replies: true,
        notify_mentions: true,
        notify_topic_replies: true
      }))
    );
}

/**
 * Actualizează preferințele de notificări
 */
updateNotificationPreferences(preferences: NotificationPreferences): Observable<NotificationPreferences> {
  return this.http.post<NotificationPreferences>(`${this.getApiUrl()}forum/user/notification-preferences/`, preferences)
    .pipe(
      catchError(this.handleError<NotificationPreferences>('updateNotificationPreferences'))
    );
}

/**
 * Verifică statusul abonării la newsletter
 */
getNewsletterStatus(): Observable<NewsletterStatus> {
  return this.http.get<NewsletterStatus>(`${this.getApiUrl()}forum/user/newsletter-status/`)
    .pipe(
      retry(1),
      catchError(this.handleError<NewsletterStatus>('getNewsletterStatus', {
        subscribed: false
      }))
    );
}

/**
 * Abonează utilizatorul la newsletter
 */
subscribeToNewsletter(email: string): Observable<any> {
  return this.http.post<any>(`${this.getApiUrl()}forum/user/subscribe-newsletter/`, { email })
    .pipe(
      catchError(this.handleError<any>('subscribeToNewsletter'))
    );
}

/**
 * Dezabonează utilizatorul de la newsletter
 */
unsubscribeFromNewsletter(): Observable<any> {
  return this.http.post<any>(`${this.getApiUrl()}forum/user/unsubscribe-newsletter/`, {})
    .pipe(
      catchError(this.handleError<any>('unsubscribeFromNewsletter'))
    );
}

  /**
   * Efectuează o căutare în forum
   */
  search(query: string): Observable<SearchResult> {
    let params = new HttpParams().set('q', query);
    
    return this.http.get<SearchResult>(`${this.getApiUrl()}forum/search/`, { params })
      .pipe(
        retry(1),
        catchError(this.handleError<SearchResult>('search', { topics: [], posts: [] }))
      );
  }

  /**
   * Obține statistici despre forum
   */
  getForumStats(): Observable<ForumStats> {
    return this.http.get<ForumStats>(`${this.getApiUrl()}forum/stats/`)
      .pipe(
        retry(1),
        catchError(this.handleError<ForumStats>('getForumStats', {
          stats: { topic_count: 0, post_count: 0, user_count: 0, last_activity: new Date().toISOString() },
          recent_topics: [],
          popular_topics: []
        }))
      );
  }

  /**
   * Format pentru afișarea duratei relative (ex: "acum 5 minute", "acum 2 ore" etc.)
   */
  getTimeAgo(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    let interval = Math.floor(seconds / 31536000); // ani
    if (interval >= 1) {
      return interval === 1 ? 'acum un an' : `acum ${interval} ani`;
    }
    
    interval = Math.floor(seconds / 2592000); // luni
    if (interval >= 1) {
      return interval === 1 ? 'acum o lună' : `acum ${interval} luni`;
    }
    
    interval = Math.floor(seconds / 86400); // zile
    if (interval >= 1) {
      return interval === 1 ? 'ieri' : `acum ${interval} zile`;
    }
    
    interval = Math.floor(seconds / 3600); // ore
    if (interval >= 1) {
      return interval === 1 ? 'acum o oră' : `acum ${interval} ore`;
    }
    
    interval = Math.floor(seconds / 60); // minute
    if (interval >= 1) {
      return interval === 1 ? 'acum un minut' : `acum ${interval} minute`;
    }
    
    return seconds < 10 ? 'chiar acum' : `acum ${Math.floor(seconds)} secunde`;
  }

  /**
   * Format pentru afișarea datei complete
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('ro-RO', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Gestionare generică a erorilor HTTP
   */
  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(`${operation} a eșuat: ${error.message}`);
      
      // Pentru debugging
      if (error.error instanceof ErrorEvent) {
        // Eroare client-side
        console.error('Eroare client:', error.error.message);
      } else {
        // Backend a returnat un cod de eroare
        console.error(`Backend a returnat codul ${error.status}, corpul:`, error.error);
      }
      
      // Returnăm un rezultat gol/default pentru a menține aplicația funcțională
      return result !== undefined ? of(result) : throwError(() => error);
    };
  }
  
  /**
   * Verifică dacă serviciul este online (pentru testare)
   */
  isOnline(): Observable<boolean> {
    return this.http.get<any>(`${this.getApiUrl()}forum/stats/`).pipe(
      map(() => true),
      catchError(() => of(false))
    );
  }
}
