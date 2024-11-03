import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {
  loading = {
    signup: false,
    home: false,
  };

  constructor(private router: Router) {}
  navigateTo(route: string) {
    if (route === 'auth') {
      this.loading.signup = true;
    } else if (route === '') {
      this.loading.home = true;
    }

    setTimeout(() => {
      this.router.navigate([route]).finally(() => {
        this.loading.signup = false;
        this.loading.home = false;
      });
    }, 300);
  }
}
