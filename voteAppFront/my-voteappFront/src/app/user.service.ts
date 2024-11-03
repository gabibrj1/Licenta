import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs';
import { environment } from '../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl =  environment.apiUrl;

  initCsrf(): Observable<any> {
    return this.http.get(`${this.apiUrl}some-initial-endpoint/`); // Endpoint care returnează un răspuns simplu, de ex. status 200
  }
  
  constructor(private http: HttpClient) {}

 
  // Register user with email and password
  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}register/`, userData).pipe(
      catchError(this.handleError)
    );
  }

  // Verify email with verification code
  verifyEmail(email: string, verification_code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}verify-email/`, { email, verification_code }).pipe(
      catchError(this.handleError)
    );
  }
  loginWithGoogle(): void {
    window.location.href = `${this.apiUrl}accounts/google/login/`;
  }
  
  

  // Register user with ID card data
  registerWithIDCard(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}register-with-id/`, userData).pipe(
      catchError(this.handleError)
    );
  }

  // Upload ID card image for processing
  uploadIDCard(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}upload-id/`, formData).pipe(
      catchError(this.handleError)
    );
  }

  // În user.service.ts

  uploadIDCardForAutofill(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}autofill-data/`, formData).pipe(
      catchError(this.handleError)
    );
  }


  
  autoFillFromImage(): Observable<any> {
    return this.http.get(`${this.apiUrl}autofill-data/`);
  }
  private handleError(error: HttpErrorResponse){
    let errorMessage = 'A aparut o eroare neasteptata. Incercati din nou';
    if (error.error instanceof ErrorEvent){
      errorMessage = `Eroare: ${error.error.message}`;
    } else {
      if (error.status === 400) {
        if (error.error.email) {
          errorMessage = error.error.email[0];  // capturam mesajul pentru email
        } else if (error.error.cnp) {
          errorMessage = error.error.cnp[0];    // capturam mesajul pentru CNP
        } else {
          errorMessage = 'Date invalide. Verificati campurile!';
        }
      }
    }
    return throwError(errorMessage);
  }
}
