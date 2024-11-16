import { Component, HostListener } from '@angular/core';
import { Location } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent {
  isMenuOpen = false;
  menuTimeout: any;
  loading = {
    home: false,
    auth: false
  };

  constructor(private router: Router, private location: Location) {}


  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
    if (this.isMenuOpen) {
      this.startMenuTimeout();
    } else {
      this.clearMenuTimeout();
    }
  }

  navigateToHome() {
    this.router.navigate(['']); 
    this.isMenuOpen = false; 
  }
  


  navigateTo(route: string) {
    if (route === '') {
      this.loading.home = true;
    } else if (route === 'auth') {
      this.loading.auth = true;
    }

    setTimeout(() => {
      this.router.navigate([route]).finally(() => {
        this.loading.home = false;
        this.loading.auth = false;
        this.isMenuOpen = false; 
      });
    }, 300);
  }


  goBack() {
    this.location.back();
  }

 
  startMenuTimeout() {
    this.clearMenuTimeout();
    this.menuTimeout = setTimeout(() => {
      this.isMenuOpen = false;
    }, 10000); 
  }


  clearMenuTimeout() {
    if (this.menuTimeout) {
      clearTimeout(this.menuTimeout);
      this.menuTimeout = null;
    }
  }


  resetMenuTimeout() {
    if (this.isMenuOpen) {
      this.startMenuTimeout();
    }
  }

 
  @HostListener('window:scroll', [])
  closeMenuOnScroll() {
    if (this.isMenuOpen) {
      this.isMenuOpen = false;
      this.clearMenuTimeout();
    }
  }
}
