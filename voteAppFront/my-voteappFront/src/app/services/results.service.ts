import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ResultsService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  getVoteResults(location: string = 'romania', round: string = 'tur1_2024'): Observable<any> {
    return this.http.get(`${this.apiUrl}rezultate/vote-rezultate/`, {
      params: { location, round }
    });
  }

  getLiveResults(): Observable<any> {
    return this.http.get(`${this.apiUrl}rezultate/live-rezultate/`);
  }
}