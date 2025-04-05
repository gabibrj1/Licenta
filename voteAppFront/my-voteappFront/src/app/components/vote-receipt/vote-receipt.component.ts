import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { LocalVoteService } from '../../services/local-vote.service';

@Component({
  selector: 'app-vote-receipt',
  templateUrl: './vote-receipt.component.html',
  styleUrls: ['./vote-receipt.component.scss']
})
export class VoteReceiptComponent implements OnInit {
  voteReference: string = '';
  isLoading: boolean = false;
  error: string = '';
  
  constructor(
    private route: ActivatedRoute,
    private localVoteService: LocalVoteService
  ) { }
  
  ngOnInit(): void {
    // Obține referința votului din parametrii de rută (dacă există)
    this.route.queryParams.subscribe(params => {
      if (params['vote_reference']) {
        this.voteReference = params['vote_reference'];
      }
    });
  }
  
  downloadPDF(): void {
    if (!this.voteReference) {
      this.error = 'Referința votului lipsește.';
      return;
    }
    
    this.isLoading = true;
    
    this.localVoteService.downloadVoteReceiptPDF(this.voteReference).subscribe({
      next: (blob: Blob) => {
        this.isLoading = false;
        
        // Creează un URL pentru blob și descarcă fișierul
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `confirmare_vot_${this.voteReference}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      },
      error: (error) => {
        this.isLoading = false;
        this.error = 'A apărut o eroare la descărcarea confirmării.';
        console.error('Eroare la descărcarea PDF-ului:', error);
      }
    });
  }
  
  openPDF(): void {
    if (!this.voteReference) {
      this.error = 'Referința votului lipsește.';
      return;
    }
    
    this.localVoteService.openVoteReceiptPDF(this.voteReference);
  }
}