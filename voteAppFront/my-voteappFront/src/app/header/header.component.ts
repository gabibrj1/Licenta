import { Component } from '@angular/core';
import { Location } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent {

  constructor(private router: Router, private location: Location) {}

  // Navigare către o anumită pagină
  navigateTo(route: string) {
    this.router.navigate([route]);
  }

  // Funcția de Back cu logică pentru a naviga în funcție de pagina curentă
  goBack() {
    const currentUrl = this.router.url;

    if (currentUrl === '/auth') {
      this.navigateTo('');
    } else if (currentUrl === '/voteapp-front') {
      this.navigateTo('auth');
    } else {
      this.location.back();
    }
  }
}
