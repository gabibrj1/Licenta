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

  constructor(private authUserService: AuthUserService, private router: Router) {}

  ngOnInit(): void {
    this.loadUserProfile();
  }

  private loadUserProfile(): void {
    this.authUserService.getUserProfile().subscribe(
      (data) => {
        if (data.email) {
          this.userEmail = data.email;
        } else if (data.message) {
          this.message = data.message;
        }
      },
      (error) => {
        console.error('Failed to fetch user profile:', error);
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
