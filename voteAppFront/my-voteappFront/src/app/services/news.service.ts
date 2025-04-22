import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { catchError, retry, tap } from 'rxjs/operators';
import { environment } from '../../src/environments/environment';

export interface NewsArticle {
  id: number;
  title: string;
  slug: string;
  summary: string;
  content?: string;  
  image: string;
  image_credit?: string; 
  publish_date: string;
  author_name: string;
  image_url?: string;
  category: {
    id: number;
    name: string;
    slug: string;
  };
  article_type: string;
  source: string;
  source_url?: string;
  is_featured: boolean;
  views_count: number;
}

export interface ExternalNewsArticle {
  title: string;
  description: string;
  url: string;
  urlToImage: string;
  publishedAt: string;
  source: {
    name: string;
  };
  author: string;
}

export interface ElectionAnalytics {
  id: number;
  title: string;
  type: string;
  data: any;
}

@Injectable({
  providedIn: 'root'
})
export class NewsService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  getLatestNews(limit: number = 10, category?: string, type?: string): Observable<NewsArticle[]> {
    let params = new HttpParams()
      .set('limit', limit.toString());
    
    if (category && category !== 'all') {
      params = params.set('category', category);
    }
    
    if (type && type !== 'all') {
      params = params.set('type', type);
    }
    
    return this.http.get<NewsArticle[]>(`${this.apiUrl}api/latest/`, { params })
      .pipe(
        retry(1),
        tap(data => console.log(`Received ${data.length} articles from API`)),
        catchError(this.handleError<NewsArticle[]>('getLatestNews', []))
      );
  }
  getExternalNews(): Observable<ExternalNewsArticle[]> {
    return this.http.get<ExternalNewsArticle[]>(`${this.apiUrl}api/external/`)
      .pipe(
        retry(1),
        tap(data => console.log(`Received ${data.length} external news items`)),
        catchError(this.handleError<ExternalNewsArticle[]>('getExternalNews', []))
      );
  }
  
  getElectionAnalytics(): Observable<ElectionAnalytics[]> {
    return this.http.get<ElectionAnalytics[]>(`${this.apiUrl}api/analytics/`)
      .pipe(
        retry(1),
        tap(data => console.log(`Received ${data.length} analytics datasets`)),
        catchError(this.handleError<ElectionAnalytics[]>('getElectionAnalytics', []))
      );
  }

  /**
   * Gestionează erorile HTTP și returnează un rezultat sigur
   * @param operation - numele operațiunii care a eșuat
   * @param result - valoarea opțională de returnare
   */
  private handleError<T>(operation = 'operation', result?: T) {
    return (error: HttpErrorResponse): Observable<T> => {
      console.error(`${operation} failed: ${error.message}`);
      
      // Pentru debugging doar în dezvoltare
      if (error.error instanceof ErrorEvent) {
        console.error('Client-side error:', error.error.message);
      } else {
        console.error(`Backend returned code ${error.status}, body was:`, error.error);
      }
      
      // Returnează un rezultat gol (array sau obiect) ca să nu se blocheze aplicația
      return of(result as T);
    };
  }
  getArticleDetail(slug: string): Observable<NewsArticle> {
    return this.http.get<NewsArticle>(`${this.apiUrl}api/article/${slug}/`)
      .pipe(
        retry(1),
        tap(data => console.log(`Received article details for: ${data.title}`)),
        catchError(this.handleError<NewsArticle>('getArticleDetail'))
      );
  }

}