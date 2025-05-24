import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CsvDownloadService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  getDownloadStatus(location: string = 'romania', round: string = 'tur1_2024'): Observable<any> {
    return this.http.get(`${this.apiUrl}csv/status/`, {
      params: { location, round }
    });
  }

  downloadCSV(location: string = 'romania', round: string = 'tur1_2024'): Observable<Blob> {
    return this.http.get(`${this.apiUrl}csv/download/`, {
      params: { location, round },
      responseType: 'blob'
    });
  }
}