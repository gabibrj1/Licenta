import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription, interval } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { VoteSystemService } from '../../services/vote-system.service';

@Component({
  selector: 'app-vote-system-status',
  templateUrl: './vote-system-status.component.html',
  styleUrls: ['./vote-system-status.component.scss']
})
export class VoteSystemStatusComponent implements OnInit, OnDestroy {
  systemId: string = '';
  voteSystem: any = null;
  isLoading = true;
  errorMessage = '';
  
  // Pentru polling
  statusCheckInterval: Subscription | null = null;
  
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private voteSystemService: VoteSystemService
  ) {}

  ngOnInit(): void {
    // Obținem ID-ul din URL
    this.systemId = this.route.snapshot.paramMap.get('id') || '';
    
    if (!this.systemId) {
      this.errorMessage = 'ID-ul sistemului de vot lipsește.';
      this.isLoading = false;
      return;
    }
    
    // Verificăm inițial starea votului
    this.checkVoteSystemStatus();
    
    // Setăm un interval pentru a verifica starea la fiecare 30 secunde
    this.statusCheckInterval = interval(30000).pipe(
      switchMap(() => this.voteSystemService.getVoteSystemDetails(this.systemId))
    ).subscribe({
      next: (data) => {
        this.voteSystem = data;
        
        // Dacă sistemul a fost aprobat, redirecționăm către detalii
        if (data.status === 'active') {
          this.router.navigate(['/menu/despre/sisteme-vot', this.systemId]);
        } else if (data.status === 'rejected') {
          // Dacă sistemul a fost respins, afișăm mesajul
          this.errorMessage = `Sistemul de vot a fost respins. Motiv: ${data.rejection_reason || 'Nespecificat'}`;
        }
      },
      error: (error) => {
        console.error('Eroare la verificarea stării:', error);
      }
    });
  }

  ngOnDestroy(): void {
    // Anulăm subscription-ul la interval la distrugerea componentei
    if (this.statusCheckInterval) {
      this.statusCheckInterval.unsubscribe();
    }
  }
  
  checkVoteSystemStatus(): void {
    this.isLoading = true;
    
    this.voteSystemService.getVoteSystemDetails(this.systemId).subscribe({
      next: (data) => {
        this.voteSystem = data;
        this.isLoading = false;
        
        // Dacă sistemul a fost deja aprobat, redirecționăm către detalii
        if (data.status === 'active') {
          this.router.navigate(['/menu/despre/sisteme-vot', this.systemId]);
        } else if (data.status === 'rejected') {
          this.errorMessage = `Sistemul de vot a fost respins. Motiv: ${data.rejection_reason || 'Nespecificat'}`;
        }
      },
      error: (error) => {
        this.isLoading = false;
        this.errorMessage = 'Nu s-au putut încărca detaliile sistemului de vot.';
        console.error('Eroare la încărcarea detaliilor:', error);
      }
    });
  }
  
  // Navighează înapoi la meniu
  goToMenu(): void {
    this.router.navigate(['/menu']);
  }
  
  // Navighează către pagina de creare a unui nou sistem
  createNewSystem(): void {
    this.router.navigate(['/menu/despre/creeaza-sistem']);
  }
}