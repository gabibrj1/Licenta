import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { environment } from '../../src/environments/environment';
import { tap, catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class VoteSystemService {
  private apiUrl = environment.apiUrl;
  private networkApiUrl = environment.networkApiUrl;

  constructor(private http: HttpClient) { }

  // Verifică dacă utilizatorul accesează din rețea sau de pe localhost
  private getApiUrl(): string {
    // Dacă URL-ul conține adresa IP a rețelei, folosim networkApiUrl
    if (window.location.hostname === environment.networkIp) {
      return this.networkApiUrl;
    }
    
    // Detecție explicită pentru a forța URL-ul de rețea când e necesar
    const isNetworkAccess = 
      window.location.hostname !== 'localhost' && 
      window.location.hostname !== '127.0.0.1';
      
    if (isNetworkAccess) {
      console.log('Detectat acces din rețea, folosim networkApiUrl');
      return this.networkApiUrl;
    }
    
    return this.apiUrl;
  }

  // URL pentru frontend - folosit pentru generarea link-urilor
  public getFrontendUrl(): string {
    // Folosim întotdeauna adresa IP de rețea pentru link-urile pentru alte dispozitive
    return `http://${environment.networkIp}:4200`;
  }

  // Metode existente actualizate pentru a folosi getApiUrl()
  
  createVoteSystem(data: any): Observable<any> {
    return this.http.post(`${this.getApiUrl()}vote-systems/create/`, data);
  }

  getUserVoteSystems(): Observable<any> {
    return this.http.get(`${this.getApiUrl()}vote-systems/user/`);
  }

  getVoteSystemDetails(systemId: string): Observable<any> {
    return this.http.get(`${this.getApiUrl()}vote-systems/${systemId}/`);
  }

  updateVoteSystem(systemId: string, data: any): Observable<any> {
    return this.http.put(`${this.getApiUrl()}vote-systems/${systemId}/`, data);
  }

  deleteVoteSystem(systemId: string): Observable<any> {
    return this.http.delete(`${this.getApiUrl()}vote-systems/${systemId}/`);
  }

  submitVote(systemId: string, voteData: any): Observable<any> {
    return this.http.post(`${this.getApiUrl()}vote-systems/${systemId}/vote/`, voteData);
  }

  getPublicVoteSystemDetails(systemId: string): Observable<any> {
    return this.http.get(`${this.getApiUrl()}vote-systems/${systemId}/public/`);
  }

  submitPublicVote(systemId: string, voteData: any): Observable<any> {
    console.log(`Trimitere vot public pentru sistemul ${systemId}:`, voteData);
    
    // Asigură-te că parametrii pentru token și email sunt corect formatați
    if (voteData.token) {
      voteData.token = String(voteData.token).trim();
    }
    
    if (voteData.email) {
      voteData.email = String(voteData.email).trim();
    }
    
    if (voteData.option_id) {
      // Asigură-te că option_id este trimis corect (ca număr sau string)
      voteData.option_id = parseInt(voteData.option_id, 10) || voteData.option_id;
    }
    
    return this.http.post(`${this.getApiUrl()}vote-systems/${systemId}/public-vote/`, voteData)
      .pipe(
        tap(response => console.log('Răspuns trimitere vot public:', response)),
        catchError(error => {
          console.error('Eroare trimitere vot public:', error);
          return throwError(() => error);
        })
      );
  }

  getPublicVoteSystemResults(systemId: string): Observable<any> {
    return this.http.get(`${this.getApiUrl()}vote-systems/${systemId}/public-results/`);
  }

  manageVoterEmails(systemId: string, emails: string[]): Observable<any> {
    console.log(`Adăugare email-uri pentru sistemul ${systemId}:`, emails);
    return this.http.post(`${this.getApiUrl()}vote-systems/${systemId}/manage-emails/`, { 
      emails: emails.join('\n') 
    });
  }

  sendVoteTokens(systemId: string): Observable<any> {
    console.log(`Trimitere token-uri pentru sistemul ${systemId}`);
    
    // Trimitem și URL-ul frontend pentru a fi folosit în email-uri
    const frontendUrl = this.getFrontendUrl();
    console.log(`URL frontend pentru email-uri: ${frontendUrl}`);
    
    return this.http.post(`${this.getApiUrl()}vote-systems/${systemId}/send-tokens/`, {
      frontend_url: frontendUrl
    });
  }

  verifyVoteToken(systemId: string, token: string, email: string): Observable<any> {
    console.log(`Verificare token pentru sistemul ${systemId}: token=${token}, email=${email}`);
    
    // Asigură-te că token și email sunt strings și sunt trimise corect
    const cleanToken = String(token).trim();
    const cleanEmail = String(email).trim();
    
    return this.http.post(`${this.getApiUrl()}vote-systems/${systemId}/verify-token/`, { 
      token: cleanToken, 
      email: cleanEmail 
    }).pipe(
      tap(response => console.log('Răspuns verificare token:', response)),
      catchError(error => {
        console.error('Eroare verificare token:', error);
        return throwError(() => error);
      })
    );
  }

  // Metodă pentru a genera link-uri de distribuire care folosesc adresa de rețea
  generateShareLink(systemId: string, includeToken: boolean = false): string {
    const baseUrl = this.getFrontendUrl();
    
    if (includeToken) {
      // Generăm un token simplu pentru tracking
      const simpleToken = btoa(`${systemId}-${Date.now()}`);
      return `${baseUrl}/vote/${systemId}?token=${simpleToken}`;
    }
    
    return `${baseUrl}/vote/${systemId}`;
  }
  checkActiveVoteSystem(): Observable<any> {
    return this.http.get(`${this.getApiUrl()}vote-systems/check-active/`);
  }
  getVoteSystemResultsUpdate(systemId: string): Observable<any> {
    return this.http.get(`${this.getApiUrl()}vote-systems/${systemId}/results-update/`);
  }

}