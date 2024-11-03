import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Autentificare clasică (email și parolă)
  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login`, { email, password }).pipe(
      catchError(this.handleError)
    );
  }

  // Autentificare cu buletin (CNP, serie, nume și prenume)
  loginWithIDCard(cnp: string, series: string, firstName: string, lastName: string): Observable<any> {
    const idCardData = { cnp, series, firstName, lastName };
    return this.http.post(`${this.apiUrl}/auth/id-card-login`, idCardData).pipe(
      catchError(this.handleError)
    );
  }

  // Încărcare imagine buletin
  uploadIDCard(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}upload-id/`, formData).pipe(
      catchError(this.handleError)
    );
  }

  // Funcție de gestionare a erorilor
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'A apărut o eroare neprevăzută. Vă rugăm să încercați din nou.';
    if (error.error instanceof ErrorEvent) {
      errorMessage = `Eroare: ${error.error.message}`;
    } else {
      errorMessage = `Server Error: ${error.status}, Mesaj: ${error.message}`;
    }
    return throwError(errorMessage);
  }
}
