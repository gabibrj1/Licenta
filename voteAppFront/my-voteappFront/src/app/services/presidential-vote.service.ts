import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PresidentialVoteService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Verifică eligibilitatea utilizatorului pentru votul prezidențial
  checkEligibility(): Observable<any> {
    return this.http.get(`${this.apiUrl}vote/presidential/eligibility/`);
  }
  
  checkUserVoteStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}vote/presidential/check-status/`);
  }

  // Obține lista de candidați prezidențiali
  getCandidates(): Observable<any> {
    return this.http.get(`${this.apiUrl}vote/presidential/candidates/`);
  }

  // Trimite votul
  submitVote(data: { 
    candidate_id: number | null, 
    send_receipt: boolean,
    receipt_method: string,
    contact_info: string ,
    voting_section_id?: number | null,
    county_code?: string,
    uat?: string
  }): Observable<any> {
    return this.http.post(`${this.apiUrl}vote/presidential/submit/`, data);
  }

  // Metodă pentru descărcarea PDF-ului cu confirmarea votului
  downloadVoteReceiptPDF(voteReference: string): Observable<Blob> {
    const url = `${this.apiUrl}vote/presidential/receipt-pdf/?vote_reference=${encodeURIComponent(voteReference)}`;
    return this.http.get(url, {
      responseType: 'blob'
    });
  }

  // Helper pentru a deschide PDF-ul într-o nouă fereastră sau a-l descărca
  openVoteReceiptPDF(voteReference: string): void {
    const url = `${this.apiUrl}vote/presidential/receipt-pdf/?vote_reference=${encodeURIComponent(voteReference)}`;
    window.open(url, '_blank');
  }
}