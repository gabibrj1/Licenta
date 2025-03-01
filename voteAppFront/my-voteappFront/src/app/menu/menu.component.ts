import { Component, OnInit } from '@angular/core';
import { AuthUserService } from '../services/auth-user.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent implements OnInit {
  userEmail: string | null = null;
  message: string | null = null;
  firstName: string | null = null;
  lastName: string | null = null;
  userCNP: string | null = null;


  constructor(private authUserService: AuthUserService, private router: Router) {}

  ngOnInit(): void {
    this.loadUserProfile();
  }

  private loadUserProfile(): void {
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.error('Token lipsă!');
      this.router.navigate(['/auth']);
      return;
    }

    this.authUserService.getUserProfile().subscribe(
      (data) => {
        console.log('✅ Profil utilizator:', data);

        if (data.email) {
          // Utilizator logat cu email și parolă
          this.userEmail = data.email;
          this.userCNP = null;
          this.firstName = null;
          this.lastName = null;
        } else if (data.cnp) {
          // Utilizator logat cu buletinul
          this.userCNP = data.cnp;
          this.firstName = data.first_name;
          this.lastName = data.last_name;
          this.userEmail = null;
        }
      },
      (error) => {
        console.error('🔴 Eroare la obținerea profilului:', error);
        this.router.navigate(['/auth']);
      }
    );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.router.navigate(['/auth']);
  }
}
