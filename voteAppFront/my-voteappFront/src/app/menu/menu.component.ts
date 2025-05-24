import { Component, OnInit, AfterViewInit, ElementRef, ViewChild, OnDestroy  } from '@angular/core';
import { Router } from '@angular/router';
import { interval, Subscription } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { AuthUserService } from '../services/auth-user.service';
import { ActivatedRoute } from '@angular/router';
import { MapService } from '../services/map.service';
import { VoteSettingsService } from '../services/vote-settings.service';

export interface ElectionRound {
  id: string;
  name: string;
  date: Date;
  active: boolean;
  hasData: boolean; // Indică dacă runda are date preîncărcate
}

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent implements OnInit, OnDestroy {
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
  electionDate: Date = new Date('2024-12-08');
  currentTime: Date = new Date();
  locationFilter: string = 'romania'; // romania sau strainatate
  isDropdownOpen: boolean = false; // Stare pentru dropdown

  // Tururile de alegeri disponibile
  availableRounds: ElectionRound[] = [
    {
      id: 'tur1_2024',
      name: 'Tur 1 Alegeri Prezidențiale 2024',
      date: new Date('2024-12-08'),
      active: false,
      hasData: true // Are date preîncărcate
    },
    {
      id: 'tur2_2024',
      name: 'Tur 2 Alegeri Prezidențiale 2024 (ANULAT)', // Adăugă ANULAT în numele turului
      date: new Date('2024-12-22'),
      active: false,
      hasData: false // Schimbă în false pentru a nu avea date
    },
    {
      id: 'tur_activ',
      name: 'Tur Activ',
      date: new Date(),
      active: true,
      hasData: false // Nu are date preîncărcate (acestea vor fi colectate în timp real)
    }
  ];
  
  // Turul curent selectat
  currentRound: ElectionRound;

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
  ) {
    // Inițializăm runda curentă cu Tur 1 2024 implicit
    this.currentRound = this.availableRounds[0];
  }

  ngOnInit(): void {
    console.log('Inițializare componentă menu...');
    
    // Verificăm query parameters pentru turul curent
    this.route.queryParams.subscribe(params => {
      if (params['round']) {
        const roundId = params['round'];
        const round = this.availableRounds.find(r => r.id === roundId);
        if (round) {
          this.currentRound = round;
          this.electionDate = round.date;
          
          // Notificăm serviciul de hartă despre turul curent
          this.mapService.setCurrentRound(round.id, round.hasData);
        }
      }
    });
    
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
      
      // Transmite locația inițială și turul către harta dacă ne aflăm pe pagina de hartă
      if (this.router.url.includes('/harta')) {
        this.router.navigate(['menu/harta'], { 
          queryParams: { 
            location: this.locationFilter,
            round: this.currentRound.id
          },
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
  
  // Toggle dropdown
  toggleDropdown(): void {
    this.isDropdownOpen = !this.isDropdownOpen;
  }
  
  private updateVoteSettings(settings: any): void {
    //console.log('Settings primite:', settings); 
    this.isVoteActive = settings.is_vote_active;
    
    if (this.isVoteActive) {
      this.activeVoteType = settings.vote_type;
      //console.log('Tip vot activ setat la:', this.activeVoteType);
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

switchRound(round: ElectionRound): void {
  console.log(`Schimbare către turul: ${round.name}`);
  
  // Actualizăm turul curent
  this.currentRound = round;
  
  // Actualizăm data alegerilor afișată
  this.electionDate = round.date;
  
  // Închide dropdown-ul
  this.isDropdownOpen = false;
  
  // Notificăm serviciul de hartă despre schimbarea turului
  this.mapService.setCurrentRound(round.id, round.hasData);
  
  // Obține ruta curentă pentru a determina ce pagină să reîmprospăteze
  const currentUrl = this.router.url;
  
  // Obține parametrii actuali din URL pentru a păstra starea
  const currentParams: {[key: string]: any} = { ...this.route.snapshot.queryParams };
  
  // Adăugăm noul tur la parametri, păstrând restul parametrilor
  currentParams['round'] = round.id;
  
  // Păstrăm parametrul location, sau folosim valoarea implicită
  if (!currentParams['location']) {
    currentParams['location'] = this.locationFilter;
  }
  
  // Determină ce pagină să reîmprospăteze pe baza URL-ului curent
  if (currentUrl.includes('/harta')) {
    // Pentru pagina de hartă
    setTimeout(() => {
      this.router.navigate(['menu/harta'], { 
        queryParams: currentParams
      });
    }, 100);
  } else if (currentUrl.includes('/statistici')) {
    // Pentru pagina de statistici - NOUA LOGICĂ
    setTimeout(() => {
      this.router.navigate(['menu/statistici'], { 
        queryParams: currentParams
      });
    }, 100);
  } else if (currentUrl.includes('/rezultate')) {
    // Pentru pagina de rezultate
    setTimeout(() => {
      this.router.navigate(['menu/rezultate'], { 
        queryParams: currentParams
      });
    }, 100);
  }else if (currentUrl.includes('/prezenta')) {
    // Pentru pagina de prezenta
    setTimeout(() => {
      this.router.navigate(['menu/prezenta'], { 
        queryParams: currentParams
      });
    }, 100);
  }
  else if (currentUrl.includes('/csv-download')) {
    // Pentru pagina de descarca csv
    setTimeout(() => {
      this.router.navigate(['menu/csv-download'], { 
        queryParams: currentParams
      });
    }, 100);
  }
}
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
  
  // Normalizează string-ul (elimină spații)
  const voteType = this.activeVoteType?.trim();
  
  // Folosim if-else în loc de switch pentru mai multă flexibilitate
  if (voteType === 'parlamentare') {
    this.router.navigate(['vot/parlamentare'], { relativeTo: this.route });
  } else if (voteType === 'prezidentiale') {
    this.router.navigate(['vot/prezidentiale'], { relativeTo: this.route });
  } else if (voteType === 'prezidentiale_tur2') {
    this.router.navigate(['vot/prezidentiale-tur2'], { relativeTo: this.route });
  } else if (voteType === 'locale') {
    this.router.navigate(['vot/locale'], { relativeTo: this.route });
  } else if (voteType === 'simulare') {
    this.router.navigate(['simulare-vot'], { relativeTo: this.route });
  } else {
    console.error('Tip de vot necunoscut:', voteType);
    // Pentru testare, defaultăm la simulare în caz că tipul nu este recunoscut
    this.router.navigate(['simulare-vot'], { relativeTo: this.route });
  }
}

// Helper pentru afișarea tipului de vot într-un format prietenos
getVoteTypeText(voteType: string | null): string {
  if (!voteType) return 'Necunoscut';
  
  const normalizedType = voteType.trim();
  
  if (normalizedType === 'parlamentare') return 'Alegeri Parlamentare';
  if (normalizedType === 'prezidentiale') return 'Alegeri Prezidențiale';
  if (normalizedType === 'prezidentiale_tur2') return 'Alegeri Prezidențiale Turul 2';
  if (normalizedType === 'locale') return 'Alegeri Locale';
  if (normalizedType === 'simulare') return 'Simulare';
  
  return voteType;
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

      case 'csv-download':
        this.router.navigate(['menu/csv-download'], {
          queryParams: { 
            location: this.locationFilter,
             round: this.currentRound.id
          }
        });
        break;
      
      // Prezență la vot
      case 'prezenta':
        this.router.navigate(['menu/prezenta'], {
          queryParams: { 
            location: this.locationFilter,
            round: this.currentRound.id
        }
        });
        break;
      
      case 'statistici':
        this.router.navigate(['menu/statistici'], {
          queryParams: { 
            location: this.locationFilter,
            round: this.currentRound.id
          }
       });
       break;
      case 'harta':
        // Notificăm serviciul de hartă despre turul curent înainte de navigare
        this.mapService.setCurrentRound(this.currentRound.id, this.currentRound.hasData);
        
        // Apoi navigăm cu parametrii corecți
        this.router.navigate(['menu/harta'], {
          queryParams: { 
            location: this.locationFilter,
            round: this.currentRound.id
          }
        });
        break;
      
      // Candidați
      case 'candidati_locali':
        this.router.navigate(['menu/candidati_locali']);
        break;

      case 'candidati_prezidentiali':
        this.router.navigate(['menu/candidati_prezidentiali'], {
          queryParams: { location: this.locationFilter }
        });
        break;
      
      // Procese-verbale
      case 'rezultate':
        this.router.navigate(['menu/rezultate'], {
          queryParams: { 
            location: this.locationFilter,
            round: this.currentRound.id
          }
        });
        break;
      case 'harta-rezultate':
        this.router.navigate(['menu/harta-rezultate']);
        break;
      
      // Informații
      case 'news':
        this.router.navigate(['menu/news']);
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
        this.router.navigate(['menu/setari-cont']);
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

switchLocation(location: string): void {
  console.log(`Schimbare către locația: ${location}`);
  
  // Actualizăm filtrul de locație
  this.locationFilter = location;
  
  // Obține ruta curentă și parametrii existenți
  const currentUrl = this.router.url;
  const currentParams: {[key: string]: any} = { ...this.route.snapshot.queryParams };
  
  // Actualizează parametrii cu noua locație
  currentParams['location'] = location;
  currentParams['round'] = this.currentRound.id;
  
  // Tratament special pentru harta
  if (currentUrl.includes('/harta')) {
    // Pentru hartă, actualizăm mai întâi serviciul pentru a evita conflictele
    this.mapService.setCurrentRound(this.currentRound.id, this.currentRound.hasData);
    
    // Navigăm imediat fără timeout și cu replaceUrl pentru o tranziție mai rapidă
    const pathWithoutParams = currentUrl.split('?')[0];
    this.router.navigate([pathWithoutParams], { 
      queryParams: currentParams,
      replaceUrl: true // Înlocuiește URL-ul curent în loc să adauge în istoric
    });
  } 
  // Pentru alte pagini (statistici, prezență, etc.)
  else if (currentUrl.includes('/statistici') || 
           currentUrl.includes('/rezultate') ||
           currentUrl.includes('/prezenta') ||
           currentUrl.includes('/csv-download') ||
           currentUrl.includes('/candidati_prezidentiali')) {
    
    // Pentru acestea păstrăm logica standard
    const pathWithoutParams = currentUrl.split('?')[0];
    this.router.navigate([pathWithoutParams], { 
      queryParams: currentParams
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