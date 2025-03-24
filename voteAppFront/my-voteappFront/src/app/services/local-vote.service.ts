// src/app/services/local-vote.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class LocalVoteService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Verifică eligibilitatea utilizatorului pentru votul local
  checkEligibility(): Observable<any> {
    return this.http.get(`${this.apiUrl}vote/local/eligibility/`);
  }
  checkUserVoteStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}vote/local/check-status/`);
  }

  // Găsește secția de vot pe baza adresei
  findVotingSection(data: { address: string, city: string, county: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}vote/local/find-section/`, data);
  }

  // Obține candidații pentru o anumită locație și poziție
  getCandidates(county: string, city: string, position?: string): Observable<any> {
    let url = `${this.apiUrl}vote/local/candidates/?county=${county}&city=${city}`;
    if (position) {
      url += `&position=${position}`;
    }
    return this.http.get(url);
  }

  // Trimite votul
  submitVote(data: { candidate_id: number, voting_section_id: number }): Observable<any> {
    return this.http.post(`${this.apiUrl}vote/local/submit/`, data);
  }
}