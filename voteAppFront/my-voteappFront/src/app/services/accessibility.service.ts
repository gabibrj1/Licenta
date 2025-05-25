import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AccessibilityService {
  private apiUrl = `${environment.apiUrl}accessibility/`;

  constructor(private http: HttpClient) { }

  getSettings(): Observable<any> {
    return this.http.get(`${this.apiUrl}settings/`);
  }

  updateSettings(settings: any): Observable<any> {
    return this.http.post(`${this.apiUrl}settings/`, settings);
  }

  getTestOptions(): Observable<any> {
    return this.http.get(`${this.apiUrl}test/`);
  }

  getAccessibilityInfo(): Observable<any> {
    return this.http.get(`${this.apiUrl}info/`);
  }
}