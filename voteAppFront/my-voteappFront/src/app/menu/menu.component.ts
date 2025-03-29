// menu.component.ts actualizat cu noile rute
import { Component, OnInit, AfterViewInit, ElementRef, ViewChild, OnDestroy  } from '@angular/core';
import { Router } from '@angular/router';
import { interval, Subscription } from 'rxjs';
import { map, switchMap  } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { AuthUserService } from '../services/auth-user.service';
import { ActivatedRoute } from '@angular/router';
import { MapService } from '../services/map.service';
import { VoteSettingsService } from '../services/vote-settings.service';

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
  authMethod: 'email' | 'id_card' = 'email';
  
  // UI state
  currentView: string = 'prezenta';
  currentRound: number = 2;
  electionDate: Date = new Date('2024-12-08');
  currentTime: Date = new Date();
  locationFilter: string = 'romania'; // romania sau strainatate

  // Vote settings
  isVoteActive: boolean = false;
  activeVoteType: string | null = null;
  upcomingVoteType: string | null = null;
  remainingTime: number = 0;
  timeUntilStart: number = 0;
  voteSettingsInterval: Subscription | null = null;

  constructor(
    private authService: AuthService, 
    private authUserService: AuthUserService,
    private router: Router,
    private route: ActivatedRoute,
    private mapService: MapService,
    private voteSettingsService: VoteSettingsService
  ) {}

  ngOnInit(): void {
    console.log('Inițializare componentă menu...');
    
    // Adăugăm o mică întârziere pentru a ne asigura că tokenurile sunt setate corect
    setTimeout(() => {
      this.loadUserProfile();
      
      // Update current time every minute
      interval(60000).pipe(
        map(() => new Date())
      ).subscribe(time => {
        this.currentTime = time;
      });
    
      // Încearcă să încarce datele utilizatorului din localStorage
      this.loadUserDataFromStorage();
      
      // Transmite locația inițială către harta dacă ne aflăm pe pagina de hartă
      if (this.router.url.includes('/harta')) {
        this.router.navigate(['menu/harta'], { 
          queryParams: { location: this.locationFilter },
          replaceUrl: true
        });
      }
      
      // Verifică setările de vot la fiecare secundă
      this.voteSettingsInterval = interval(1000).pipe(
        switchMap(() => this.voteSettingsService.getVoteSettings())
      ).subscribe(
        (settings) => {
          this.updateVoteSettings(settings);
        },
        (error) => {
          console.error('Eroare la obținerea setărilor de vot:', error);
        }
      );
      
      // Verifică setările inițiale
      this.voteSettingsService.getVoteSettings().subscribe(
        (settings) => {
          this.updateVoteSettings(settings);
        },
        (error) => {
          console.error('Eroare la obținerea setărilor de vot:', error);
        }
      );
    }, 500); // Întârziere de 500ms pentru încărcarea tokenurilor
  }
  ngOnDestroy(): void {
    // Anulează subscription pentru a evita memory leak
    if (this.voteSettingsInterval) {
      this.voteSettingsInterval.unsubscribe();
    }
  }
  private updateVoteSettings(settings: any): void {
    this.isVoteActive = settings.is_vote_active;
    
    if (this.isVoteActive) {
      this.activeVoteType = settings.vote_type;
      this.remainingTime = settings.remaining_time;
      this.upcomingVoteType = null;
      this.timeUntilStart = 0;
    } else if (settings.upcoming_vote) {
      this.activeVoteType = null;
      this.remainingTime = 0;
      this.upcomingVoteType = settings.upcoming_vote.vote_type;
      this.timeUntilStart = settings.upcoming_vote.time_until_start;
    } else {
      this.activeVoteType = null;
      this.remainingTime = 0;
      this.upcomingVoteType = null;
      this.timeUntilStart = 0;
    }
  }

  

  // Verifică dacă utilizatorul este autentificat
  isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }

  private loadUserDataFromStorage(): void {
    // Verificăm dacă avem CNP în localStorage (autentificare cu buletin)
    const userCNP = localStorage.getItem('user_cnp');
    const lastAuthMethod = localStorage.getItem('auth_method');
    
    // Setăm metoda de autentificare conform ultimei metode folosite
    if (lastAuthMethod) {
      this.authMethod = lastAuthMethod as 'email' | 'id_card';
    } else {
      // Determinăm metoda din datele existente
      this.authMethod = userCNP ? 'id_card' : 'email';
    }
    
    // Încărcăm datele în funcție de metoda de autentificare
    if (this.authMethod === 'id_card') {
      if (userCNP) {
        this.userCNP = userCNP;
        this.userEmail = null; // Resetăm email-ul
        
        // Încercăm să obținem datele utilizatorului din localStorage
        const userDataStr = localStorage.getItem('user_data');
        if (userDataStr) {
          try {
            this.userData = JSON.parse(userDataStr);
            this.firstName = this.userData.first_name || '';
            this.lastName = this.userData.last_name || '';
            // Eliminăm email-ul din userData dacă există
            if (this.userData.email) {
              delete this.userData.email;
            }
          } catch (e) {
            console.error('Eroare la parsarea datelor utilizatorului:', e);
          }
        }
      }
    } else {
      // Metoda email - resetăm datele de buletin
      this.userCNP = null;
      this.firstName = null;
      this.lastName = null;
      
      // Încercăm să obținem email-ul din localStorage
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
  

// Updated loadUserProfile method for MenuComponent

private loadUserProfile(): void {
  console.log('Loading user profile...');
  
  // First check if we have data in localStorage
  this.loadUserDataFromStorage();
  
  // Also try to get profile data from API
  this.authUserService.getUserProfile().subscribe(
    (data) => {
      console.log('User profile loaded from API:', data);
      
      // Filtrăm datele în funcție de metoda de autentificare
      if (this.authMethod === 'email') {
        // Pentru autentificare cu email, păstrăm doar email-ul
        if (data.email) {
          this.userEmail = data.email;
          
          // Resetăm datele de buletin
          this.userCNP = null;
          this.firstName = null;
          this.lastName = null;
          
          // Construim obiectul de date utilizator doar cu email
          const userData = {
            email: data.email,
            is_active: data.is_active || true
          };
          
          this.userData = userData;
          localStorage.setItem('user_data', JSON.stringify(userData));
        }
      } else {
        // Pentru autentificare cu buletin, păstrăm doar datele de buletin
        if (data.cnp) {
          this.userCNP = data.cnp;
          this.userEmail = null; // Resetăm email-ul
          
          if (data.first_name) {
            this.firstName = data.first_name;
          }
          
          if (data.last_name) {
            this.lastName = data.last_name;
          }
          
          // Construim obiectul de date utilizator fără email
          const userData = {
            cnp: data.cnp,
            first_name: data.first_name || '',
            last_name: data.last_name || '',
            is_verified_by_id: data.is_verified_by_id || true,
            is_active: data.is_active || true
          };
          
          this.userData = userData;
          localStorage.setItem('user_data', JSON.stringify(userData));
          localStorage.setItem('user_cnp', data.cnp);
        }
      }
    },
    (error) => {
      console.error('Error loading profile:', error);
      // Dacă există eroare, ne bazăm doar pe datele din localStorage
    }
  );
}

    // Metodă nouă pentru navigarea către tipul corect de vot
    navigateToVote(): void {
      if (!this.isVoteActive) {
        // Dacă votul nu este activ, sugerăm alternative
        if (this.upcomingVoteType) {
          // Există un vot programat în viitor
          alert(`Votul de tip ${this.getVoteTypeText(this.upcomingVoteType)} va începe în curând. Poți încerca simularea procesului de vot între timp.`);
        } else {
          // Nu există vot programat - sugerăm simularea sau crearea propriului sistem
          alert('Nu există o sesiune de vot activă în acest moment. Poți încerca simularea procesului de vot sau să creezi propriul sistem de vot.');
        }
        return;
      }
    
      // Redirecționăm către pagina corespunzătoare tipului de vot
      // Acum rutele sunt relative la MenuComponent
      switch (this.activeVoteType) {
        case 'parlamentare':
          this.router.navigate(['vot/parlamentare'], { relativeTo: this.route });
          break;
        case 'prezidentiale':
          this.router.navigate(['vot/prezidentiale'], { relativeTo: this.route });
          break;
        case 'locale':
          this.router.navigate(['vot/locale'], { relativeTo: this.route });
          break;
        case 'simulare':
          this.router.navigate(['simulare-vot'], { relativeTo: this.route });
          break;
        default:
          console.error('Tip de vot necunoscut:', this.activeVoteType);
          // Pentru testare, defaultăm la simulare în caz că tipul nu este recunoscut
          this.router.navigate(['simulare-vot'], { relativeTo: this.route });
          break;
      }
    }
      // Helper pentru afișarea tipului de vot într-un format prietenos
      getVoteTypeText(voteType: string | null): string {
        if (!voteType) return 'Necunoscut';
        
        switch (voteType) {
          case 'parlamentare': return 'Alegeri Parlamentare';
          case 'prezidentiale': return 'Alegeri Prezidențiale';
          case 'locale': return 'Alegeri Locale';
          case 'simulare': return 'Simulare';
          default: return voteType;
        }
      }

   // Helper pentru formatarea timpului rămas
   formatRemainingTime(seconds: number): string {
    if (seconds <= 0) return '00:00:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }




  // Navigation
  navigateTo(view: string): void {
    this.currentView = view;
    
    // Rute pentru toate secțiunile
    switch (view) {
      // Secțiunea principală
      case 'voteaza':
        this.navigateToVote();
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
        this.router.navigate(['menu/harta'], {
          queryParams: { location: this.locationFilter }
        });
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
          this.router.navigate(['menu/despre/concept']);
          break;
        case 'creeaza-sistem':
          console.log('Navigare către creeaza-sistem');
          this.router.navigate(['menu/despre/creeaza-sistem']);
          break;
        case 'misiune':
          console.log('Navigare către misiune');
          this.router.navigate(['menu/despre/misiune']);
          break;
        case 'contact':
          console.log('Navigare către contact');
          this.router.navigate(['menu/despre/contact']);
          break;
        
        // Setări Avansate
        case 'setari-cont':
          this.router.navigate(['menu/setari/cont']);
          break;
        case 'securitate':
          this.router.navigate(['menu/setari/securitate']);
          break;
        case 'notificari':
          this.router.navigate(['menu/setari/notificari']);
          break;
        case 'accesibilitate':
          this.router.navigate(['menu/setari/accesibilitate']);
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

// În menu.component.ts
switchLocation(location: string): void {
  this.locationFilter = location;
  
  // Dacă utilizatorul este deja pe pagina hartă, actualizează URL-ul
  if (this.currentView === 'harta') {
    this.router.navigate(['menu/harta'], { 
      queryParams: { location: location },
      replaceUrl: true
    });
  }
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