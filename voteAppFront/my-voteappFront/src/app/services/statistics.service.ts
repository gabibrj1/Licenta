import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class StatisticsService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  getVoteStatistics(location: string = 'romania', round: string = 'tur1_2024'): Observable<any> {
    return this.http.get(`${this.apiUrl}statistici/vote-statistici/`, {
      params: { location, round }
    });
  }

  getLiveStatistics(): Observable<any> {
    return this.http.get(`${this.apiUrl}statistici/live-statistici/`);
  }
}