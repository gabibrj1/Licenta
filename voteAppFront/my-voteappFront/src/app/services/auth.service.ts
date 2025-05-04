import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
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
      tap(response => {
        this.handleAuthSuccess(response, 'email');
      }),
      catchError(this.handleError)
    );
  }

  // Metoda centralizată pentru procesarea răspunsurilor de autentificare
  public handleAuthSuccess(response: any, authMethod: 'email' | 'id_card' = 'email'): void {
    console.log('Procesare JWT primite:', response);
    
    // Salvăm metoda de autentificare
    localStorage.setItem('auth_method', authMethod);
    
    // Restul codului rămâne neschimbat
    if (response.access) {
      localStorage.setItem(this.TOKEN_KEY, response.access);
      console.log('Token de acces salvat:', response.access.substring(0, 20) + '...');
    } else {
      console.warn('Lipsește token-ul de acces din răspuns!');
    }
    
    // 2. Salvăm datele utilizatorului
    const userData: any = {};
    
    // Procesăm datele utilizatorului din diverse surse posibile
    if (response.user) {
      // Pentru autentificare cu email
      Object.assign(userData, response.user);
    }
    
    // Pentru autentificare cu CNP
    if (response.cnp) {
      userData.cnp = response.cnp;
      localStorage.setItem('user_cnp', response.cnp); // Salvăm separat pentru compatibilitate
    }
    
    // Alte câmpuri posibile
    if (response.first_name) userData.first_name = response.first_name;
    if (response.last_name) userData.last_name = response.last_name;
    if (response.email) userData.email = response.email;
    if (response.is_verified_by_id !== undefined) userData.is_verified_by_id = response.is_verified_by_id;
    
    // Salvăm datele utilizatorului doar dacă există
    if (Object.keys(userData).length > 0) {
      const userDataStr = JSON.stringify(userData);
      localStorage.setItem(this.USER_DATA_KEY, userDataStr);
      console.log('Date utilizator salvate:', userData);
    } else {
      console.warn('Nu s-au găsit date despre utilizator în răspuns!');
    }
  }

  refreshToken(): Observable<any> {
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    
    if (!refreshToken) {
      console.error('Nu există token de refresh pentru reîmprospătare!');
      return throwError(() => new Error('No refresh token available'));
    }

    console.log('Reîmprospătare token cu refresh token:', refreshToken.substring(0, 10) + '...');
    
    return this.http.post(`${this.apiUrl}auth/refresh/`, { refresh: refreshToken }).pipe(
      tap((response: any) => {
        console.log('Răspuns refresh token:', response);
        this.handleAuthSuccess(response);
      }),
      catchError((error) => {
        console.error('Eroare la reîmprospătarea token-ului:', error);
        // În caz de eroare, vom face logout pentru a forța reautentificarea
        this.logout();
        return throwError(() => error);
      })
    );
  }

  logout(): void {
    console.log('Logout - ștergem toate datele din localStorage');
    localStorage.clear();
    this.router.navigate(['/auth']);
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem(this.TOKEN_KEY);
    return !!token;
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getUserData(): any {
    const userDataStr = localStorage.getItem(this.USER_DATA_KEY);
    if (userDataStr) {
      try {
        return JSON.parse(userDataStr);
      } catch (e) {
        console.error('Eroare la parsarea datelor utilizatorului:', e);
        return {};
      }
    }
    return {};
  }

  // Autentificare cu buletin
  loginWithIDCard(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}login-id-card/`, data).pipe(
      tap(response => {
        this.handleAuthSuccess(response, 'id_card');
      }),
      catchError(error => {
        return this.handleError(error);
      })
    );
  }
  
  loginWithFaceRecognition(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}login-id-card/`, formData).pipe(
      tap(response => {
        this.handleAuthSuccess(response, 'id_card');
      }),
      catchError(error => {
        return this.handleError(error);
      })
    );
  }

  // Verificăm token-ul reCAPTCHA direct
  verifyRecaptcha(token: string): Observable<any> {
    return this.http.post(`${this.apiUrl}verify-recaptcha/`, {
      token
    });
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
  
  requestPasswordReset(email: string) {
    return this.http.post<any>(`${this.apiUrl}request-password-reset/`, { email });
  }
  
  resetPassword(email: string, verification_code: string, new_password: string) {
    return this.http.post<any>(`${this.apiUrl}reset-password/`, {
      email,
      verification_code,
      new_password
    });
  }
  
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'A apărut o eroare neprevăzută. Vă rugăm să încercați din nou.';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Eroare: ${error.error.message}`;
    } else if (error.error?.detail) {
      // Server-side error with detail
      errorMessage = error.error.detail;
    } else if (error.status) {
      // Other server error
      errorMessage = `Server Error: ${error.status}, Mesaj: ${error.message}`;
    }
    
    console.error('Auth error:', errorMessage);
    return throwError(() => errorMessage);
  }
  checkTwoFactorRequired(response: any): boolean {
    return response && response.requires_2fa === true;
  }
  
  // Verifică codul 2FA pentru autentificare cu email
  verifyTwoFactorWithEmail(email: string, code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}verify-two-factor/`, {
      email,
      code
    }).pipe(
      tap(response => {
        this.handleAuthSuccess(response, 'email');
      }),
      catchError(this.handleError)
    );
  }
  
  // Verifică codul 2FA pentru autentificare cu CNP
  verifyTwoFactorWithCNP(cnp: string, code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}verify-two-factor/`, {
      cnp, 
      code
    }).pipe(
      tap(response => {
        this.handleAuthSuccess(response, 'id_card');
      }),
      catchError(this.handleError)
    );
  }

}