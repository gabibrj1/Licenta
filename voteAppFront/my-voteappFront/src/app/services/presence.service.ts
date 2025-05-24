import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PresenceService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  getVotingPresence(location: string = 'romania', round: string = 'tur1_2024', page: number = 1, pageSize: number = 10): Observable<any> {
    return this.http.get(`${this.apiUrl}prezenta/voting-presence/`, {
      params: { 
        location, 
        round, 
        page: page.toString(), 
        page_size: pageSize.toString() 
      }
    });
  }

  getLivePresence(): Observable<any> {
    return this.http.get(`${this.apiUrl}prezenta/live-presence/`);
  }
}