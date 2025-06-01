import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { VoteSystemService } from '../../services/vote-system.service';

@Component({
  selector: 'app-my-vote-systems',
  templateUrl: './my-vote-systems.component.html',
  styleUrls: ['./my-vote-systems.component.scss']
})
export class MyVoteSystemsComponent implements OnInit {
  voteSystems: any[] = [];
  isLoading = true;
  errorMessage = '';
  
  // Filtre pentru sisteme
  activeFilter: string = 'all'; // all, active, completed, pending
  searchQuery: string = '';
  sortBy: string = 'date_desc'; // date_desc, date_asc, votes_desc, votes_asc, name_asc, name_desc

  constructor(
    private voteSystemService: VoteSystemService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadVoteSystems();
  }

  loadVoteSystems(): void {
    this.isLoading = true;
    this.voteSystemService.getUserVoteSystems().subscribe({
      next: (data) => {
        this.voteSystems = data;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = 'Nu s-au putut încărca sistemele de vot. Vă rugăm să încercați din nou mai târziu.';
        this.isLoading = false;
        console.error('Eroare la încărcarea sistemelor de vot:', error);
      }
    });
  }

  // Filtrare și sortare
  applyFilters(): void {
    this.loadVoteSystems();
  }

  // Navighează către detaliile unui sistem de vot
  viewVoteSystem(systemId: string): void {
    this.router.navigate(['/menu/despre/sisteme-vot', systemId]);
  }

  // Navighează către crearea unui nou sistem
  createNewVoteSystem(): void {
    this.router.navigate(['/menu/despre/creeaza-sistem']);
  }

  // Formatează data pentru afișare
  formatDate(date: Date): string {
    if (!date) return '';
    
    // Convertim string la Date dacă e necesar
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    return dateObj.toLocaleDateString('ro-RO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  // Calculează timpul rămas până la încheierea votului
  getRemainingTime(endDate: Date): string {
    if (!endDate) return 'Nedefinit';
    
    const now = new Date();
    const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
    
    if (now > end) return 'Încheiat';
    
    const diffMs = end.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays > 0) {
      return `${diffDays} zile rămase`;
    } else {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      return `${diffHours} ore rămase`;
    }
  }

  // Obține clasa CSS pentru status
  getStatusClass(status: string): string {
    switch (status) {
      case 'active': return 'status-active';
      case 'completed': return 'status-completed';
      case 'pending': return 'status-pending';
      case 'rejected': return 'status-rejected';
      default: return '';
    }
  }

  // Obține textul pentru status
  getStatusText(status: string): string {
    switch (status) {
      case 'active': return 'Activ';
      case 'completed': return 'Încheiat';
      case 'pending': return 'În așteptare';
      case 'rejected': return 'Respins';
      default: return status;
    }
  }

  // Șterge un sistem de vot
  deleteVoteSystem(event: Event, systemId: string): void {
    event.stopPropagation();
    
    if (confirm('Sunteți sigur că doriți să ștergeți acest sistem de vot? Această acțiune este ireversibilă.')) {
      this.voteSystemService.deleteVoteSystem(systemId).subscribe({
        next: () => {
          this.voteSystems = this.voteSystems.filter(system => system.id !== systemId);
        },
        error: (error) => {
          console.error('Eroare la ștergerea sistemului de vot:', error);
          alert('Nu s-a putut șterge sistemul de vot. Vă rugăm să încercați din nou mai târziu.');
        }
      });
    }
  }
}