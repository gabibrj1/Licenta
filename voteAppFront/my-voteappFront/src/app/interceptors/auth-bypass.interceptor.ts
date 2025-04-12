// src/app/interceptors/auth-bypass.interceptor.ts
import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class AuthBypassInterceptor implements HttpInterceptor {
  
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Verificăm dacă URL-ul conține rute publice
    if (req.url.includes('/public/') || req.url.includes('/public-vote/') || req.url.includes('/public-results/')) {
      // Nu adăugăm token-uri de autentificare pentru rutele publice
      return next.handle(req);
    }
    
    // Pentru toate celelalte cereri, continuăm lanțul de interceptori
    return next.handle(req);
  }
}