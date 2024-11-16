import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, tap} from 'rxjs/operators';
import { environment } from '../../src/environments/environment';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_DATA_KEY = 'user_data';

  constructor(private http: HttpClient, private router: Router) {}

  // auth clasica (email si parola)
  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}auth/login/`, { email, password }).pipe(
      tap(response => this.handleAuthSuccess(response)),
      catchError(this.handleError)
    );
  }

  public handleAuthSuccess(response: any): void {
    console.log('JWT primite:', response);
    localStorage.setItem(this.TOKEN_KEY, response.access);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refresh);
    if (response.user) {
      localStorage.setItem(this.USER_DATA_KEY, JSON.stringify(response.user));
    }
  }
  

  refreshToken(): Observable<any> {
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      return throwError('No refresh token available');
    }

    return this.http.post(`${this.apiUrl}auth/refresh/`, { refresh: refreshToken }).pipe(
      tap((response: any) => this.handleAuthSuccess(response)),
      catchError(this.handleError)
    );
  }

  logout(): void {
    localStorage.clear();
    this.router.navigate(['/auth']);
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem(this.TOKEN_KEY);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  // Autentificare cu buletin (CNP, serie, nume si prenume)
  loginWithIDCard(cnp: string, series: string, firstName: string, lastName: string): Observable<any> {
    const idCardData = { cnp, series, firstName, lastName };
    return this.http.post(`${this.apiUrl}/auth/id-card-login`, idCardData).pipe(
      catchError(this.handleError)
    );
  }

  // incarcare imagine buletin
  uploadIDCard(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}upload-id/`, formData).pipe(
      catchError(this.handleError)
    );
  }


  socialLoginCallback(code: string, provider: string): Observable<any> {
    return this.http.post(`${this.apiUrl}social-login/callback/`, { code, provider }).pipe(
      tap((response) => {
        this.handleAuthSuccess(response);
      }),
      catchError(this.handleError)
    );
  }
  

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
