import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

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
    // altfel folosim apiUrl normal
    if (window.location.hostname === environment.networkIp) {
      return this.networkApiUrl;
    }
    return this.apiUrl;
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
    return this.http.post(`${this.getApiUrl()}vote-systems/${systemId}/public-vote/`, voteData);
  }

  getPublicVoteSystemResults(systemId: string): Observable<any> {
    return this.http.get(`${this.getApiUrl()}vote-systems/${systemId}/public-results/`);
  }
}