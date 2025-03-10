import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../src/environments/environment';

export interface ContactInfo {
  address: string;
  phone: string;
  email: string;
  business_hours: string;
}

export interface ContactMessage {
    name: string;
    email: string;
    message: string;
  }

@Injectable({
  providedIn: 'root'
})
export class ContactService {
  // URL-ul API
  private apiUrl = environment.apiUrl || 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) { }


  getContactInfo(): Observable<ContactInfo> {
    console.log('Serviciu: Încercare de a obține date de contact');
    
    // Asigură-te că acest URL corespunde cu cel verificat în Postman
    const url = `${this.apiUrl}menu/contact/`;
    console.log('URL API apelat:', url);
    
    return this.http.get<ContactInfo>(url).pipe(
      tap(data => console.log('Date primite de la API:', data)),
      catchError(error => {
        console.error('Eroare la obținerea datelor de contact:', error);
        
        // În caz de eroare, poți returna date fictive pentru a testa afișarea
        // sau poți propaga eroarea mai departe
        
        // Opțiunea 1: Returnează date fictive pentru testare
        const mockData: ContactInfo = {
          address: 'Str. Scafe nr. 14, Prahova (mock)',
          phone: '+40 0723 452 871 (mock)',
          email: 'g.brujbeanu18@gmail.com (mock)',
          business_hours: 'Luni-Vineri: 9:00 - 17:00 (mock)'
        };
        
        return of(mockData);
        
        // Opțiunea 2: Propaga eroarea
        // return throwError(error);
      })
    );
  }
  sendContactMessage(contactData: ContactMessage): Observable<any> {
    return this.http.post(`${this.apiUrl}menu/send-contact/`, contactData);
  }
  
}