import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../src/environments/environment';

export interface MapInfo {
  center: {
    lat: number;
    lng: number;
  };
  zoom: number;
  regions: {
    name: string;
    code: string;
    voters: number;
    percentage: number;
  }[];
}

@Injectable({
  providedIn: 'root'
})
export class MapService {
  // URL-ul API
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  getMapInfo(): Observable<MapInfo> {
    console.log('Serviciu: Încercare de a obține date hartă');
    
    // URL-ul către endpoint-ul pentru hartă
    const url = `${this.apiUrl}menu/map/`;
    console.log('URL API apelat:', url);
    
    return this.http.get<MapInfo>(url).pipe(
      tap(data => console.log('Date primite de la API:', data)),
      catchError(error => {
        console.error('Eroare la obținerea datelor hartă:', error);
        
        // În caz de eroare, returnează date fictive pentru testare
        const mockData: MapInfo = {
          center: { lat: 45.9443, lng: 25.0094 },
          zoom: 7,
          regions: [
            { name: 'București', code: 'B', voters: 12500, percentage: 0.65 },
            { name: 'Cluj', code: 'CJ', voters: 8300, percentage: 0.42 },
            { name: 'Iași', code: 'IS', voters: 7600, percentage: 0.38 },
            // ... alte regiuni
          ]
        };
        
        return of(mockData);
      })
    );
  }
}