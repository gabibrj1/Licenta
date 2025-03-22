import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class VoteSettingsService {
  private apiUrl = `${environment.apiUrl}vote-settings/`;
  private adminApiUrl = `${environment.apiUrl}admin/vote-settings/`;

  constructor(private http: HttpClient) { }

  // Obține setările actuale de vot pentru utilizatori
  getVoteSettings(): Observable<any> {
    return this.http.get(this.apiUrl);
  }

  // Metode admin pentru gestionarea setărilor de vot
  getAdminVoteSettings(): Observable<any> {
    return this.http.get(this.adminApiUrl);
  }

  createVoteSettings(settings: any): Observable<any> {
    return this.http.post(this.adminApiUrl, settings);
  }

  updateVoteSettings(id: number, settings: any): Observable<any> {
    return this.http.put(`${this.adminApiUrl}${id}/`, settings);
  }

  deleteVoteSettings(id: number): Observable<any> {
    return this.http.delete(`${this.adminApiUrl}${id}/`);
  }
}