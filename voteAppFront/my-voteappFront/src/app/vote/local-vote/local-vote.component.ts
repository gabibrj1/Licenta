// src/app/vote/local-vote/local-vote.component.ts

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { LocalVoteService } from '../../services/local-vote.service';

@Component({
  selector: 'app-local-vote',
  templateUrl: './local-vote.component.html',
  styleUrls: ['./local-vote.component.scss']
})
export class LocalVoteComponent implements OnInit {
  currentStep = 1; // 1: verificare eligibilitate, 2: confirmare adresă, 3: secție vot, 4: buletinul de vot
  isEligible = false;
  authType = '';
  userInfo: any = null;
  addressForm: FormGroup;
  votingSection: any = null;
  candidates: any = null;
  isLoading = false;
  error = '';
  selectedCandidates: any = {};

  constructor(
    private localVoteService: LocalVoteService,
    private fb: FormBuilder,
    private router: Router
  ) {
    this.addressForm = this.fb.group({
      address: ['', Validators.required],
      city: ['', Validators.required],
      county: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.checkEligibility();
    this.localVoteService.checkUserVoteStatus().subscribe(
      (response) => {
        if (response.has_voted) {
          this.error = response.message;
          // Alternativ, poți redirecționa utilizatorul
          // this.router.navigate(['/menu']);
        }
      },
      (error) => {
        console.error('Error checking vote status:', error);
      }
    );
  }

  checkEligibility(): void {
    this.isLoading = true;
    this.localVoteService.checkEligibility().subscribe(
      (response) => {
        this.isLoading = false;
        this.isEligible = response.eligible;
        this.authType = response.auth_type;
        if (response.eligible) {
          this.userInfo = response.user_info;
          this.currentStep = 2; // Trecem la pasul de confirmare adresă
        }
      },
      (error) => {
        this.isLoading = false;
        this.error = 'A apărut o eroare la verificarea eligibilității.';
        console.error('Error checking eligibility:', error);
      }
    );
  }

  submitAddress(): void {
    if (this.addressForm.valid) {
      this.isLoading = true;
      this.localVoteService.findVotingSection(this.addressForm.value).subscribe(
        (response) => {
          this.isLoading = false;
          this.votingSection = response.section;
          this.currentStep = 3; // Trecem la pasul de afișare a secției de vot
        },
        (error) => {
          this.isLoading = false;
          this.error = error.error.error || 'A apărut o eroare la căutarea secției de vot.';
          console.error('Error finding voting section:', error);
        }
      );
    }
  }

  confirmVotingSection(): void {
    if (this.votingSection) {
      this.isLoading = true;
      // Obținem candidații pentru această locație
      this.localVoteService.getCandidates(
        this.votingSection.county, 
        this.votingSection.city
      ).subscribe(
        (response) => {
          this.isLoading = false;
          this.candidates = response.positions;
          this.currentStep = 4; // Trecem la buletinul de vot
        },
        (error) => {
          this.isLoading = false;
          this.error = 'A apărut o eroare la încărcarea candidaților.';
          console.error('Error loading candidates:', error);
        }
      );
    }
  }

  selectCandidate(position: string, candidateId: number): void {
    this.selectedCandidates[position] = candidateId;
  }

  submitVote(): void {
    if (Object.keys(this.selectedCandidates).length === 0) {
      this.error = 'Trebuie să selectați cel puțin un candidat.';
      return;
    }
    
    this.isLoading = true;
    
    // Procesează voturile pentru fiecare poziție
    const promises = Object.keys(this.selectedCandidates).map(position => {
      const candidateId = this.selectedCandidates[position];
      
      return this.localVoteService.submitVote({
        candidate_id: candidateId,
        voting_section_id: this.votingSection.id
      }).toPromise();
    });
    
    Promise.all(promises)
      .then(responses => {
        this.isLoading = false;
        // Afișează un mesaj de succes
        alert('Votul dumneavoastră a fost înregistrat cu succes!');
        // Redirecționează către pagina principală
        this.router.navigate(['/menu']);
      })
      .catch(error => {
        this.isLoading = false;
        this.error = error.error?.error || 'A apărut o eroare la înregistrarea votului.';
        console.error('Error submitting vote:', error);
      });
  }

  redirectToIDRegistration(): void {
    this.router.navigate(['/auth'], { queryParams: { mode: 'id_card' }});
  }
  get objectKeys() {
    return Object.keys;
  }
  getPositionLabel(positionKey: string): string {
    const positionLabels: {[key: string]: string} = {
      'mayor': 'Primar',
      'councilor': 'Consilier Local',
      'county_president': 'Președinte Consiliu Județean',
      'county_councilor': 'Consilier Județean'
    };
    
    return positionLabels[positionKey] || positionKey;
  }
  
}