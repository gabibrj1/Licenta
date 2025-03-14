// menu.component.ts actualizat cu noile rute
import { Component, OnInit, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { interval } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { AuthUserService } from '../services/auth-user.service';

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent implements OnInit {
  // User data
  userEmail: string | null = null;
  message: string | null = null;
  firstName: string | null = null;
  lastName: string | null = null;
  userCNP: string | null = null;
  userData: any = null;
  
  // UI state
  currentView: string = 'prezenta';
  currentRound: number = 2;
  electionDate: Date = new Date('2024-12-08');
  currentTime: Date = new Date();
  locationFilter: string = 'romania'; // romania sau strainatate

  constructor(
    private authService: AuthService, 
    private authUserService: AuthUserService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadUserProfile();
    
    // Update current time every minute
    interval(60000).pipe(
      map(() => new Date())
    ).subscribe(time => {
      this.currentTime = time;
    });

    // Încearcă să încarce datele utilizatorului din localStorage
    this.loadUserDataFromStorage();
  }

  // Verifică dacă utilizatorul este autentificat
  isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }

  private loadUserDataFromStorage(): void {
    // Verificăm dacă avem CNP în localStorage (autentificare cu buletin)
    const userCNP = localStorage.getItem('user_cnp');
    if (userCNP) {
      this.userCNP = userCNP;
      
      // Încercăm să obținem datele utilizatorului din localStorage
      const userDataStr = localStorage.getItem('user_data');
      if (userDataStr) {
        try {
          this.userData = JSON.parse(userDataStr);
          this.firstName = this.userData.first_name || '';
          this.lastName = this.userData.last_name || '';
        } catch (e) {
          console.error('Eroare la parsarea datelor utilizatorului:', e);
        }
      }
    } else {
      // Dacă nu avem CNP, verificăm dacă există un email de utilizator în localStorage
      const userDataStr = localStorage.getItem('user_data');
      if (userDataStr) {
        try {
          this.userData = JSON.parse(userDataStr);
          if (this.userData.email) {
            this.userEmail = this.userData.email;
          }
        } catch (e) {
          console.error('Eroare la parsarea datelor utilizatorului:', e);
        }
      }
    }
  }

  private loadUserProfile(): void {
    // Dacă avem deja date din localStorage, nu mai facem request
    if (this.userData && (this.userEmail || this.userCNP)) {
      return;
    }

    // Încercăm să obținem datele profilului de la API
    this.authUserService.getUserProfile().subscribe(
      (data) => {
        if (data.email) {
          this.userEmail = data.email;
          this.userCNP = null;
          this.firstName = null;
          this.lastName = null;
        } else if (data.message) {
          this.message = data.message;
        } else if (data.cnp) {
          // Utilizator logat cu buletinul
          this.userCNP = data.cnp;
          this.firstName = data.first_name;
          this.lastName = data.last_name;
          this.userEmail = null;
        }
      },
      (error) => {
        console.error('Eroare la încărcarea profilului:', error);
      }
    );
  }

  // Navigation
  navigateTo(view: string): void {
    this.currentView = view;
    
    // Rute pentru toate secțiunile
    switch (view) {
      // Secțiunea principală
      case 'voteaza':
        this.router.navigate(['menu/voteaza']);
        break;
      case 'simulare-vot':
        this.router.navigate(['menu/simulare-vot']);
        break;
      
      // Prezență la vot
      case 'prezenta':
        this.router.navigate(['menu/prezenta']);
        break;
      case 'statistici':
        this.router.navigate(['menu/statistici']);
        break;
      case 'harta':
        this.router.navigate(['menu/harta']);
        break;
      
      // Candidați
      case 'candidati-locali':
        this.router.navigate(['menu/candidati-locali']);
        break;
      
      // Procese-verbale
      case 'rezultate':
        this.router.navigate(['menu/rezultate']);
        break;
      case 'harta-rezultate':
        this.router.navigate(['menu/harta-rezultate']);
        break;
      
      // Informații
      case 'stiri-analize':
        this.router.navigate(['menu/stiri-analize']);
        break;
      case 'forumuri':
        this.router.navigate(['menu/forumuri']);
        break;
      
        case 'concept':
          console.log('Navigare către concept');
          this.router.navigate(['/menu/despre/concept']);
          break;
        case 'creeaza-sistem':
          console.log('Navigare către creeaza-sistem');
          this.router.navigate(['/menu/despre/creeaza-sistem']);
          break;
        case 'misiune':
          console.log('Navigare către misiune');
          this.router.navigate(['/menu/despre/misiune']);
          break;
        case 'contact':
          console.log('Navigare către contact');
          this.router.navigate(['/menu/despre/contact']);
          break;
        
        // Setări Avansate
        case 'setari-cont':
          this.router.navigate(['/menu/setari/cont']);
          break;
        case 'securitate':
          this.router.navigate(['/menu/setari/securitate']);
          break;
        case 'notificari':
          this.router.navigate(['/menu/setari/notificari']);
          break;
        case 'accesibilitate':
          this.router.navigate(['/menu/setari/accesibilitate']);
          break;
        
        default:
          this.router.navigate([`/${view}`]);
          break;
      }
    }

  // Switch between election rounds
  switchRound(round: number): void {
    this.currentRound = round;
    // Implementează logica pentru a schimba datele în funcție de tur
  }

  switchLocation(location: string): void {
    this.locationFilter = location;
  }

  // Mask CNP for privacy
  maskCNP(cnp: string): string {
    if (!cnp) return '';
    return cnp.substring(0, 3) + '********' + cnp.substring(11);
  }

  logout(): void {
    this.authService.logout();
  }
}