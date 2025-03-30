// src/app/vote/local-vote/local-vote.component.ts

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl } from '@angular/forms';
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
  method: string = ''; // Adăugare proprietate pentru metoda de identificare
  countyExamples: string[] = ['B', 'CJ', 'IS', 'CT', 'TM', 'BV']; // Exemple de județe prescurtate
  multipleSections: any[] = []; // Lista de secții multiple
  streetName: string = ''; // Strada pentru care există multiple secții
  showMultipleSections = false; // Flag pentru afișarea paginii de selecție a secției
  matchedStreet: string = ''; // Strada potrivită în caz de potrivire parțială

  constructor(
    private localVoteService: LocalVoteService,
    private fb: FormBuilder,
    private router: Router
  ) {
    this.addressForm = this.fb.group({
      county: ['', [Validators.required, Validators.maxLength(2), this.countyValidator]],
      city: ['', [Validators.required]],
      address: ['', [Validators.required, this.addressValidator]]
    });

    // Transformă input-ul pentru județ și localitate în litere mari la schimbare
    this.addressForm.get('county')?.valueChanges.subscribe(value => {
      if (value) {
        this.addressForm.get('county')?.setValue(value.toUpperCase(), { emitEvent: false });
      }
    });

    this.addressForm.get('city')?.valueChanges.subscribe(value => {
      if (value) {
        this.addressForm.get('city')?.setValue(value.toUpperCase(), { emitEvent: false });
      }
    });
  }

  // Validator pentru județ
  countyValidator(control: AbstractControl): {[key: string]: any} | null {
    const value = control.value;
    if (value && !/^[A-Z]{1,2}$/.test(value)) {
      return { 'invalidCounty': true };
    }
    return null;
  }

  // Validator pentru adresă (fără prescurtări)
  addressValidator(control: AbstractControl): {[key: string]: any} | null {
    const value = control.value;
    const abbreviations = /\b(str|nr|bl|sc|ap|et)\b/i;
    
    if (value && abbreviations.test(value)) {
      return { 'abbreviationsNotAllowed': true };
    }
    return null;
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
  selectSection(sectionIndex: number): void {
    this.isLoading = true;
    
    // Adaugăm section_selection la obiectul trimis către backend
    const requestData = {
      ...this.addressForm.value,
      section_selection: sectionIndex
    };
    
    this.localVoteService.findVotingSection(requestData).subscribe(
      (response) => {
        this.isLoading = false;
        this.votingSection = response.section;
        this.method = response.method;
        
        if (response.matched_street) {
          this.matchedStreet = response.matched_street;
        }
        
        this.showMultipleSections = false;
        console.log('Secție selectată manual:', this.votingSection.name);
      },
      (error) => {
        this.isLoading = false;
        this.error = error.error?.error || 'A apărut o eroare la selectarea secției de vot.';
        console.error('Error selecting voting section:', error);
      }
    );
  }
  
  backToAddressForm(): void {
    this.showMultipleSections = false;
    this.currentStep = 2;
  }

  submitAddress(): void {
    if (this.addressForm.valid) {
      this.isLoading = true;
      this.error = ''; // Resetăm mesajul de eroare
      this.method = ''; // Resetăm metoda de identificare
      this.matchedStreet = ''; // Resetăm strada potrivită
      this.multipleSections = []; // Resetăm lista de secții multiple
      this.showMultipleSections = false; // Resetăm flag-ul pentru multiple secții
      
      this.localVoteService.findVotingSection(this.addressForm.value).subscribe(
        (response) => {
          this.isLoading = false;
          
          // Verificăm dacă avem multiple secții
          if (response.multiple_sections) {
            this.multipleSections = response.sections;
            this.streetName = response.street;
            this.method = response.method;
            this.showMultipleSections = true;
            this.currentStep = 3; // Păstrăm pasul 3, dar cu afișare diferită
            console.log('Multiple secții găsite:', this.multipleSections.length);
            return;
          }
          
          // Avem o singură secție
          this.votingSection = response.section;
          this.method = response.method; // Salvează metoda de identificare
          
          // Salvează strada potrivită dacă există
          if (response.matched_street) {
            this.matchedStreet = response.matched_street;
          }
          
          // Adaugă logging pentru metoda AI folosită
          console.log('Metoda AI folosită pentru identificare:', response.method);
          
          this.currentStep = 3; // Trecem la pasul de afișare a secției de vot
        },
        (error) => {
          this.isLoading = false;
          this.error = error.error?.error || 'A apărut o eroare la căutarea secției de vot.';
          console.error('Error finding voting section:', error);
        }
      );
    }
  }
// În local-vote.component.ts
confirmVotingSection(): void {
  if (this.votingSection) {
    this.isLoading = true;
    console.log("Se încarcă candidații pentru:", this.votingSection.county, this.votingSection.city);
    
    // Adaugă logging pentru a vedea cererea
    this.localVoteService.getCandidates(
      this.votingSection.county, 
      this.votingSection.city
    ).subscribe(
      (response) => {
        this.isLoading = false;
        console.log("Răspuns candidați:", response); // Adaugă acest log
        this.candidates = response.positions;
        
        // Verifică dacă există candidați
        if (Object.keys(this.candidates || {}).length === 0) {
          this.error = "Nu există candidați înregistrați pentru această localitate.";
          console.warn("Nu s-au găsit candidați");
        } else {
          this.currentStep = 4; // Trecem la buletinul de vot
        }
      },
      (error) => {
        this.isLoading = false;
        this.error = 'A apărut o eroare la încărcarea candidaților: ' + 
                     (error.error?.error || error.message || JSON.stringify(error));
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
  
  // Helper pentru a afișa numele metodei într-un format mai prietenos
// Helper pentru a afișa numele metodei într-un format mai prietenos
getMethodName(methodCode: string): string {
  const methodNames: {[key: string]: string} = {
    'direct_lookup_exact': 'căutare directă',
    'direct_lookup_normalized': 'căutare normalizată',
    'direct_lookup_partial': 'potrivire parțială',
    'direct_lookup_exact_multiple': 'căutare directă (multiple secții)',
    'direct_lookup_normalized_multiple': 'căutare normalizată (multiple secții)',
    'direct_lookup_partial_multiple': 'potrivire parțială (multiple secții)',
    'direct_lookup_exact_selected': 'secție selectată manual',
    'direct_lookup_normalized_selected': 'secție selectată manual',
    'direct_lookup_partial_selected': 'secție selectată manual',
    'direct_lookup': 'căutare directă',
    'ml_model': 'model de inteligență artificială',
    'fallback': 'metodă alternativă',
    'unknown': 'metodă necunoscută'
  };
  
  return methodNames[methodCode] || 'metodă necunoscută';
}

  // Metoda care returnează un județ aleator din lista de exemple
  getRandomCountyExample(): string {
    const randomIndex = Math.floor(Math.random() * this.countyExamples.length);
    return this.countyExamples[randomIndex];
  }
}