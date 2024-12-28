import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../src/environments/environment';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl =  environment.apiUrl;

  initCsrf(): Observable<any> {
    return this.http.get(`${this.apiUrl}some-initial-endpoint/`); // Endpoint care returneaza un raspuns simplu, de ex. status 200
  }
  
  constructor(private http: HttpClient, private router: Router) {}

 
  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}register/`, userData).pipe(
      catchError(this.handleError)
    );
  }

 
  verifyEmail(email: string, verification_code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}verify-email/`, { email, verification_code }).pipe(
      catchError(this.handleError)
    );
  }
  loginWithGoogle(): void {
    window.location.href = `${this.apiUrl}accounts/google/login/`;
  }
  
  

  registerWithIDCard(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}register-with-id/`, userData).pipe(
      catchError(this.handleError)
    );
  }



  uploadIDCardForAutofill(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}upload-id/`, formData).pipe(
      catchError(this.handleError)
    );
  }


scanIDCardForAutofill(formData: FormData): Observable<any> {
  return this.http.post(`${this.apiUrl}scan-id/`, formData).pipe(
    catchError(this.handleError)
  );
}

autoFillFromScan(filePath: string): Observable<any> {
  return this.http.post(`${this.apiUrl}autofill_scan_data/`, { file_path: filePath }).pipe(
    catchError(this.handleError)
  );
}




  
  
  sendFeedback(feedbackData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}send-feedback/`, feedbackData, { withCredentials: true }).pipe(
      catchError((error) => throwError(error))
    );
  }
  checkProfanity(message: string): Observable<any> {
    return this.http.post(`${this.apiUrl}check-profanity/`, { message }).pipe(
      catchError(this.handleError)
    );
  }  
  autoFillFromImage(filePath: string): Observable<any> {
    return this.http.post(`${this.apiUrl}autofill_data/`, { file_path: filePath }).pipe(
      catchError(this.handleError)
    );
  }
  
  private handleError(error: HttpErrorResponse){
    let errorMessage = 'A aparut o eroare neasteptata. Incercati din nou';
    if (error.error instanceof ErrorEvent){
      errorMessage = `Eroare: ${error.error.message}`;
    } else {
      if (error.status === 400) {
        if (error.error.email) {
          errorMessage = error.error.email[0];  
        } else if (error.error.cnp) {
          errorMessage = error.error.cnp[0];    
        } else {
          errorMessage = 'Date invalide. Verificati campurile!';
        }
      }
    }
    return throwError(errorMessage);
  }
}
