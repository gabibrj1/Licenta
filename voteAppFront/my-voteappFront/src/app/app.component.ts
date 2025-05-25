import { Component, OnInit, OnDestroy  } from '@angular/core';
import { Router, NavigationEnd  } from '@angular/router';
import { ScreenReaderService } from './services/screen-reader.service';
import { filter} from 'rxjs/operators';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'voteapp';
  private routerSubscription?: Subscription;
  private isFirstLoad = true; // Flag pentru prima încărcare
  
  constructor(
    private screenReaderService: ScreenReaderService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Forțează dezactivarea screen reader-ului DOAR la prima pornire a aplicației
    if (this.isFirstLoad) {
      this.ensureScreenReaderDisabled();
      this.isFirstLoad = false;
    }
    
    // Monitorizează schimbările de rută pentru a re-scana elementele DOAR dacă screen reader-ul este activ
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        // Așteaptă ca pagina să se încarce complet și re-scanează doar dacă screen reader-ul este activ
        setTimeout(() => {
          // Re-scanează doar dacă screen reader-ul este activat manual
          if (this.screenReaderService.isActive()) {
            this.screenReaderService.refreshPageElements();
          }
        }, 500);
      });
  }

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
    
    // Asigură-te că screen reader-ul se curăță la închiderea aplicației
    this.screenReaderService.cleanup();
  }

  private ensureScreenReaderDisabled(): void {
    // Forțează dezactivarea screen reader-ului DOAR la prima pornire a aplicației
    // După activare manuală, rămâne activ chiar și la navigarea între pagini
    this.screenReaderService.disableGlobal();
    
    console.log('App Component: Screen Reader forțat dezactivat la prima pornire - odată activat manual rămâne activ');
    
    // Verificare de siguranță doar la prima încărcare
    setTimeout(() => {
      if (this.screenReaderService.isActive()) {
        console.warn('Screen Reader era activ în mod neașteptat la prima pornire - se forțează dezactivarea');
        this.screenReaderService.disableGlobal();
      }
    }, 100);
  }

  // Opțional: Metodă care poate fi apelată din componenta de accesibilitate
  // Aceasta NU este auto-activare - doar un mod de comunicare între componente
  public enableScreenReaderFromAccessibility(): void {
    // Această metodă ar trebui apelată doar de componenta de accesibilitate când utilizatorul îl activează manual
    console.log('App Component: Screen Reader activat prin pagina de accesibilitate');
  }

  public disableScreenReaderFromAccessibility(): void {
    // Această metodă ar trebui apelată doar de componenta de accesibilitate când utilizatorul îl dezactivează manual
    this.screenReaderService.disableGlobal();
    console.log('App Component: Screen Reader dezactivat prin pagina de accesibilitate');
  }
}