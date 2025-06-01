import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    // Verificare strictă a autentificării
    if (!this.authService.isAuthenticated()) {
      console.log('AuthGuard: Utilizator neautentificat - redirectare la /auth');
      this.router.navigate(['/auth'], { replaceUrl: true });
      return false;
    }

    // Verificare suplimentară - există datele esențiale?
    const userData = this.authService.getUserData();
    const hasValidData = userData && (userData.email || userData.cnp);
    
    if (!hasValidData) {
      console.log('AuthGuard: Date utilizator invalide - forțare logout');
      this.authService.logout();
      return false;
    }

    return true;
  }
}