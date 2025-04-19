import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-vote-simulation',
  templateUrl: './vote-simulation.component.html',
  styleUrls: ['./vote-simulation.component.scss']
})
export class VoteSimulationComponent implements OnInit, OnDestroy, AfterViewInit {
  // State management
  stepIndex = 0;
  simulationComplete = false;
  activeSystem: 'official' | 'custom' = 'official';
  selectedVoteType: 'presidential' | 'parliamentary' | 'local' | null = null;
  
  // Presidential vote simulation
  presidentialCandidates = [
    { name: 'George Simion', party: 'Alianța pentru Unirea Românilor' },
    { name: 'Crin Antonescu', party: 'PSD-PNL-UDMR' },
    { name: 'Elena Lasconi', party: 'Uniunea Salvați România' },
    { name: 'Lavinia Șandru', party: 'Partidul Umanist Social Liberal' },
    { name: 'Victor Ponta', party: 'Independent' }
  ];
  selectedPrezCandidate: number | null = null;
  
  // Parliamentary vote simulation
  parliamentaryParties = [
    { name: 'Alianța pentru Unirea Românilor', abbreviation: 'AUR' },
    { name: 'Alianța Electorală România Înainte', abbreviation: 'AERI' },
    { name: 'Uniunea Salvați România', abbreviation: 'USR' },
    { name: 'Partidul Umanist Social Liberal', abbreviation: 'PUSL' },
    { name: 'Partidul Național Conservator Român', abbreviation: 'PNCR' }
  ];
  selectedParliamentaryParty: number | null = null;
  
  // Local vote simulation
  localAddress = {
    county: '',
    city: '',
    address: ''
  };
  
  localPositions = [
    {
      title: 'Primar',
      candidates: [
        { name: 'Alexandru Georgescu', party: 'PSD-PNL-UDMR' },
        { name: 'Gabriela Popa', party: 'Uniunea Salvați România' },
        { name: 'Valentin Munteanu', party: 'Alianța pentru Unirea Românilor' }
      ],
      selected: null as number | null
    },
    {
      title: 'Consilier Local',
      candidates: [
        { name: 'Cristian Stanciu', party: 'PSD-PNL-UDMR' },
        { name: 'Daniela Neacșu', party: 'Uniunea Salvați România' },
        { name: 'Florin Ciobanu', party: 'Alianța pentru Unirea Românilor' }
      ],
      selected: null as number | null
    }
  ];
  
  // Confirmation data - eliminat SMS ca opțiune, doar email
  sendConfirmation = false;
  contactInfo = '';
  contactInfoError = false; // Adăugat pentru a afișa erori de validare pentru informațiile de contact
  
  // Custom vote system
  adminApproved = false;
  tokenVerified = false;
  tokenInput = ''; // Adăugat pentru a stoca input-ul token-ului
  customVoteOptions = [
    { name: 'Ana Popescu', description: 'Reprezentant anul II, Facultatea de Drept' },
    { name: 'Mihai Ionescu', description: 'Reprezentant anul III, Facultatea de Informatică' },
    { name: 'Elena Dumitrescu', description: 'Reprezentant anul I, Facultatea de Economie' }
  ];
  selectedCustomOption: number | null = null;
  customVoteSubmitted = false;
  userVoteCounted = false; // Flag pentru a ține cont dacă votul utilizatorului a fost inclus

  officialReferenceCode: string = '';
  customReferenceCode: string = '';


  // Adăugăm proprietăți pentru sistemul personalizat
  customSystem = {
    name: 'Alegerea reprezentantului de grup',
    description: 'Vot pentru alegerea reprezentantului grupului pentru anul universitar 2023-2024',
    participants: 'student1@example.com\nstudent2@example.com\nstudent3@example.com\nstudent4@example.com\nstudent5@example.com'
  };

  // Erori de validare - extinse
  validationErrors = {
    local: {
      county: false,
      city: false,
      address: false,
      candidateSelection: false
    },
    presidential: false,
    parliamentary: false,
    custom: {
      name: false,
      description: false,
      options: false,
      participants: false,
      token: false,
      option: false
    }
  };

  // Stocăm token-ul original
  originalToken = 'BX72F9';

  // Subscriptions management
  private subscriptions = new Subscription();

  constructor() { }

  ngOnInit(): void {
    this.officialReferenceCode = this.generateReferenceCode();
    this.customReferenceCode = this.generateReferenceCode();
    // Inițializarea se face fără apeluri API repetitive
    console.log('Componenta de simulare a fost inițializată');
    // Inițializează ora și data pentru sistemul personalizat cu data curentă + 1 zi
    this.initializeCustomSystemDates();
  }

  ngOnDestroy(): void {
    // Dezabonare de la toate subscriptions pentru a preveni memory leaks
    if (this.subscriptions) {
      this.subscriptions.unsubscribe();
    }
    console.log('Componenta de simulare a fost distrusă și toate subscriptions au fost curățate');
  }
  ngAfterViewInit(): void {
    // Prevenim modificarea listei de emailuri în sistemul particular
    setTimeout(() => {
      const emailTextarea = document.querySelector('textarea[[(ngModel)]="customSystem.participants"]') as HTMLTextAreaElement;
      if (emailTextarea) {
        emailTextarea.addEventListener('keydown', function(e) {
          e.preventDefault();
          return false;
        });
        
        emailTextarea.addEventListener('paste', function(e) {
          e.preventDefault();
          return false;
        });
        
        emailTextarea.addEventListener('cut', function(e) {
          e.preventDefault();
          return false;
        });
        
        // Setăm și atributul readonly pentru siguranță suplimentară
        emailTextarea.setAttribute('readonly', 'readonly');
      }
    }, 500); // Folosim un setTimeout pentru a ne asigura că elementul este complet renderizat
  }

  // Inițializează datele pentru sistemul personalizat
  initializeCustomSystemDates() {
    // Setează data de începere la data curentă
    const currentDate = new Date();
    const startDate = new Date();
    startDate.setDate(currentDate.getDate());
    
    // Setează data de încheiere la data curentă + 2 zile
    const endDate = new Date();
    endDate.setDate(currentDate.getDate() + 2);
    
    // Formatăm datele pentru input-urile HTML
    const formatDate = (date: Date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };
    
    // Formatăm orele pentru input-urile HTML
    const formatTime = (date: Date) => {
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${hours}:${minutes}`;
    };
    
    // Aplicăm valorile la elementele din DOM după ce viewul este inițializat
    setTimeout(() => {
      const startDateInput = document.querySelector('input[type="date"][value="2023-11-15"]') as HTMLInputElement;
      const startTimeInput = document.querySelector('input[type="time"][value="09:00"]') as HTMLInputElement;
      const endDateInput = document.querySelector('input[type="date"][value="2023-11-17"]') as HTMLInputElement;
      const endTimeInput = document.querySelector('input[type="time"][value="18:00"]') as HTMLInputElement;
      
      if (startDateInput) startDateInput.value = formatDate(startDate);
      if (startTimeInput) startTimeInput.value = formatTime(startDate);
      if (endDateInput) endDateInput.value = formatDate(endDate);
      if (endTimeInput) endTimeInput.value = formatTime(endDate);
    }, 0);
  }

  // Navigation methods
  nextStep() {
    const maxSteps = this.getMaxStepsForActiveSystem();
    
    // Validare la pasul 3 pentru sistemele oficiale
    if (this.activeSystem === 'official' && this.stepIndex === 2) {
      if (!this.validateStep3()) {
        return; // Nu permite trecerea la următorul pas dacă validarea eșuează
      }
    }
    
    // Validare la pasul 4 pentru confirmarea votului
    if (this.activeSystem === 'official' && this.stepIndex === 3) {
      if (this.sendConfirmation && !this.validateContactInfo()) {
        return; // Nu permite trecerea la următorul pas dacă validarea eșuează
      }
    }
    
    
    // Validare pentru sistemele particulare
    if (this.activeSystem === 'custom') {
      if (this.stepIndex === 0) {
        // Validează primul pas pentru sistemul de vot personalizat
        if (!this.validateCustomStep1()) {
          return;
        }
      } else if (this.stepIndex === 1) {
        // Validează al doilea pas pentru sistemul de vot personalizat
        if (!this.validateCustomStep2()) {
          return;
        }
      } else if (this.stepIndex === 2) {
        // Validează al treilea pas pentru sistemul de vot personalizat
        if (!this.validateCustomStep3()) {
          return;
        }
      } else if (this.stepIndex === 4) {
        // Validează pasul 5 (pasul 4 fiind indexul 4) pentru sistemul de vot personalizat
        if (!this.validateCustomVoteStep()) {
          return;
        }
      }
    }
    
    if (this.stepIndex < maxSteps - 1) {
      // Tratăm special când mergem la pasul 3 (care este stepIndex = 2)
      if (this.activeSystem === 'official') {
        if (this.stepIndex === 1) {
          // Resetăm tipul de vot pentru a afișa opțiunile inițiale
          this.resetVoteSelections();
          this.stepIndex++;
          return;
        }
      }
      this.stepIndex++;
      
      // Dacă am ajuns la pasul 6 (rezultate) pentru sistemul personalizat
      // adăugăm și votul utilizatorului la rezultate dacă a votat
      if (this.activeSystem === 'custom' && this.stepIndex === 5 && this.customVoteSubmitted && !this.userVoteCounted) {
        this.addUserVoteToResults();
      }
    } else {
      this.simulationComplete = true;
    }
  }

  prevStep() {
    if (this.stepIndex > 0) {
      // Tratăm special când revenim la pasul 3 (care este stepIndex = 2)
      if (this.activeSystem === 'official') {
        if (this.stepIndex === 3) {
          // Resetăm tipul de vot pentru a afișa opțiunile inițiale
          this.resetVoteSelections();
          this.stepIndex--;
          return;
        }
      }
      this.stepIndex--;
    }
  }

  // Metodă pentru resetarea tuturor selecțiilor
  resetVoteSelections() {
    this.selectedVoteType = null;
    this.selectedPrezCandidate = null;
    this.selectedParliamentaryParty = null;
    this.localPositions.forEach(pos => pos.selected = null);
  }

  resetSimulation() {
    this.officialReferenceCode = this.generateReferenceCode();
    this.customReferenceCode = this.generateReferenceCode();
    this.stepIndex = 0;
    this.simulationComplete = false;
    this.resetVoteSelections();
    this.sendConfirmation = false;
    this.contactInfo = '';
    this.contactInfoError = false; // Resetăm erorile de validare pentru informațiile de contact
    this.adminApproved = false;
    this.tokenVerified = false;
    this.tokenInput = ''; // Resetăm input-ul token-ului
    this.selectedCustomOption = null;
    this.customVoteSubmitted = false;
    this.userVoteCounted = false;
    this.localAddress = {
      county: '',
      city: '',
      address: ''
    };
    
    // Resetează erorile de validare
    this.validationErrors = {
      local: {
        county: false,
        city: false,
        address: false,
        candidateSelection: false
      },
      presidential: false,
      parliamentary: false,
      custom: {
        name: false,
        description: false,
        options: false,
        participants: false,
        token: false,
        option: false
      }
    };
    
    // Resetăm valorile pentru sistemul personalizat
    this.customSystem = {
      name: 'Alegerea reprezentantului de grup',
      description: 'Vot pentru alegerea reprezentantului grupului pentru anul universitar 2023-2024',
      participants: 'student1@example.com\nstudent2@example.com\nstudent3@example.com\nstudent4@example.com\nstudent5@example.com'
    };
    
    // Re-inițializează datele pentru sistemul personalizat
    this.initializeCustomSystemDates();
  }

  // System type management
  setActiveSystem(system: 'official' | 'custom') {
    if (this.activeSystem !== system) {
      this.activeSystem = system;
      this.resetSimulation();
    }
  }

  getMaxStepsForActiveSystem(): number {
    return this.activeSystem === 'official' ? 5 : 6;
  }

  getStepsForActiveSystem(): any[] {
    const count = this.getMaxStepsForActiveSystem();
    return new Array(count).fill(0);
  }

  // Vote type selection
  selectVoteType(type: 'presidential' | 'parliamentary' | 'local') {
    this.selectedVoteType = type;
  }

  isVoteTypeSelected(): boolean {
    return this.selectedVoteType !== null;
  }

  // Presidential candidate selection
  selectPrezCandidate(index: number) {
    this.selectedPrezCandidate = this.selectedPrezCandidate === index ? null : index;
    this.validationErrors.presidential = false; // Resetează eroarea când se face o selecție
  }

  getSelectedPrezCandidate() {
    return this.selectedPrezCandidate !== null ? 
      this.presidentialCandidates[this.selectedPrezCandidate] : 
      { name: 'Nici un candidat selectat', party: '' };
  }

  // Parliamentary party selection
  selectParliamentaryParty(index: number) {
    this.selectedParliamentaryParty = this.selectedParliamentaryParty === index ? null : index;
    this.validationErrors.parliamentary = false; // Resetează eroarea când se face o selecție
  }

  getSelectedParliamentaryParty() {
    return this.selectedParliamentaryParty !== null ? 
      this.parliamentaryParties[this.selectedParliamentaryParty] : 
      { name: 'Nici un partid selectat', abbreviation: '' };
  }

  // Local candidate selection
  selectLocalCandidate(position: any, index: number) {
    position.selected = position.selected === index ? null : index;
    // Resetăm eroarea de selecție candidat doar dacă toți candidații sunt selectați
    if (this.allLocalCandidatesSelected()) {
      this.validationErrors.local.candidateSelection = false;
    }
  }
  
  // Verifică dacă toți candidații locali sunt selectați
  allLocalCandidatesSelected(): boolean {
    return this.localPositions.every(position => position.selected !== null);
  }

  // Custom vote system methods
  simulateAdminApproval() {
    this.adminApproved = true;
  }

  simulateTokenVerification() {
    // Verifică dacă tokenul introdus de utilizator este valid
    if (this.tokenInput === this.originalToken) {
      this.tokenVerified = true;
      this.validationErrors.custom.token = false;
    } else {
      this.tokenVerified = false;
      this.validationErrors.custom.token = true;
    }
  }

  selectCustomOption(index: number) {
    this.selectedCustomOption = this.selectedCustomOption === index ? null : index;
    this.validationErrors.custom.option = false; // Resetează eroarea când se face o selecție
  }

  simulateCustomVote() {
    if (this.selectedCustomOption !== null) {
      this.customVoteSubmitted = true;
      this.validationErrors.custom.option = false;
    } else {
      this.validationErrors.custom.option = true;
    }
  }

  // Adaugă votul utilizatorului la rezultate
  addUserVoteToResults() {
    if (this.customVoteSubmitted && this.selectedCustomOption !== null && !this.userVoteCounted) {
      // Implementare a logicii doar vizuale - modificăm înălțimile pentru a reflecta votul utilizatorului
      const chartBars = document.querySelectorAll('.chart-bar') as NodeListOf<HTMLElement>;
      
      if (chartBars && chartBars.length >= 3) {
        // Obține elementul votat de utilizator
        const votedBar = chartBars[this.selectedCustomOption];
        
        if (votedBar) {
          // Extrage procentajul și numărul de voturi
          const votesCountElement = votedBar.querySelector('.votes-count');
          
          if (votesCountElement) {
            const currentText = votesCountElement.textContent || '';
            const match = currentText.match(/(\d+)\s*\((\d+)%\)/);
            
            if (match) {
              const currentVotes = parseInt(match[1]);
              const newVotes = currentVotes + 1;
              
              // Actualizează textul cu numărul de voturi
              votesCountElement.textContent = `${newVotes} (${Math.round((newVotes / 6) * 100)}%)`;
              
              // Actualizează înălțimea barei
              const currentHeight = parseInt(votedBar.style.height);
              votedBar.style.height = `${currentHeight + 10}%`;
              
              // Actualizează și celelalte procente
              chartBars.forEach((bar, idx) => {
                if (idx !== this.selectedCustomOption) {
                  const otherVotesElement = bar.querySelector('.votes-count');
                  if (otherVotesElement) {
                    const otherMatch = otherVotesElement.textContent?.match(/(\d+)\s*\((\d+)%\)/);
                    if (otherMatch) {
                      const votes = parseInt(otherMatch[1]);
                      otherVotesElement.textContent = `${votes} (${Math.round((votes / 6) * 100)}%)`;
                    }
                  }
                }
              });
              
              // Actualizează și informațiile despre câștigător dacă este cazul
              const winnerElement = document.querySelector('.winner-name');
              const winnerDetailsElement = document.querySelector('.winner-details');
              
              if (this.selectedCustomOption === 0 || (this.selectedCustomOption === 0 && newVotes > 1)) {
                if (winnerElement) {
                  winnerElement.textContent = this.customVoteOptions[0].name;
                }
                if (winnerDetailsElement) {
                  winnerDetailsElement.textContent = `${newVotes} voturi (${Math.round((newVotes / 6) * 100)}%)`;
                }
              }
            }
          }
          
          this.userVoteCounted = true;
        }
      }
    }
  }

  // Helper methods
  generateReferenceCode(): string {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 8; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
  }

  getCurrentDateTime(): string {
    const now = new Date();
    return now.toLocaleString('ro-RO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  // Validări pentru sistemele oficiale
  validateStep3(): boolean {
    let isValid = true;

    if (this.selectedVoteType === 'presidential') {
      if (this.selectedPrezCandidate === null) {
        this.validationErrors.presidential = true;
        isValid = false;
        alert('Trebuie să selectați un candidat prezidențial pentru a continua.');
      }
    } else if (this.selectedVoteType === 'parliamentary') {
      if (this.selectedParliamentaryParty === null) {
        this.validationErrors.parliamentary = true;
        isValid = false;
        alert('Trebuie să selectați un partid pentru a continua.');
      }
    } else if (this.selectedVoteType === 'local') {
      // Resetăm toate erorile
      this.validationErrors.local.county = false;
      this.validationErrors.local.city = false;
      this.validationErrors.local.address = false;
      this.validationErrors.local.candidateSelection = false;
      
      // Validare câmpuri adresă
      if (!this.localAddress.county) {
        this.validationErrors.local.county = true;
        isValid = false;
      }
      if (!this.localAddress.city) {
        this.validationErrors.local.city = true;
        isValid = false;
      }
      if (!this.localAddress.address) {
        this.validationErrors.local.address = true;
        isValid = false;
      }

      // Verificare dacă toți candidații au fost selectați
      // MODIFICAT: Verificăm acum că au fost selectați candidați pentru toate pozițiile
      const allSelected = this.allLocalCandidatesSelected();
      if (!allSelected) {
        this.validationErrors.local.candidateSelection = true;
        isValid = false;
        alert('Trebuie să selectați un candidat pentru fiecare poziție (Primar și Consilier Local).');
      }
    } else {
      // Nu s-a selectat niciun tip de vot
      alert('Trebuie să selectați un tip de vot pentru a continua.');
      isValid = false;
    }

    return isValid;
  }

  validateContactInfo(): boolean {
    this.contactInfoError = false;
    
    // Validează adresa de email
    if (this.sendConfirmation) {
      if (!this.contactInfo || !this.isValidEmail(this.contactInfo)) {
        this.contactInfoError = true;
        alert('Vă rugăm să introduceți o adresă de email validă.');
        return false;
      }
    }
    return true;
  }
  
  isValidEmail(email: string): boolean {
    // Verificare de bază
    if (!email || email.trim() === '') {
      return false;
    }
    
    // Expresie regulată complexă pentru validarea adresei de email
    // Această expresie verifică formatarea de bază a emailului
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    if (!emailRegex.test(email)) {
      return false;
    }
    
    // Verificări suplimentare
    
    // Verificăm dacă adresa nu conține ".." consecutive
    if (email.includes('..')) {
      return false;
    }
    
    // Verificăm formatul părților de email
    const parts = email.split('@');
    
    // Verificăm că avem exact o parte locală și un domeniu
    if (parts.length !== 2) {
      return false;
    }
    
    const localPart = parts[0];
    const domain = parts[1];
    
    // Verificăm că partea locală nu începe sau se termină cu punct
    if (localPart.startsWith('.') || localPart.endsWith('.')) {
      return false;
    }
    
    // Verificăm că domeniul conține cel puțin un punct
    if (!domain.includes('.')) {
      return false;
    }
    
    // Verificăm că domeniul nu începe sau se termină cu punct sau cratimă
    if (domain.startsWith('.') || domain.startsWith('-') || 
        domain.endsWith('.') || domain.endsWith('-')) {
      return false;
    }
    
    // Verificăm că domeniul nu conține două puncte consecutive
    if (domain.includes('..')) {
      return false;
    }
    
    // Verificăm că domeniul nu conține două cratime consecutive
    if (domain.includes('--')) {
      return false;
    }
    
    // Verificăm că fiecare parte a domeniului (separate prin puncte) nu începe sau se termină cu cratimă
    const domainParts = domain.split('.');
    for (const part of domainParts) {
      if (part.startsWith('-') || part.endsWith('-')) {
        return false;
      }
      
      // Verificăm că partea de domeniu nu este goală
      if (part.length === 0) {
        return false;
      }
    }
    
    // Verificăm că TLD-ul (ultima parte a domeniului) are cel puțin 2 caractere
    const tld = domainParts[domainParts.length - 1];
    if (tld.length < 2) {
      return false;
    }
    
    // Verificăm că TLD-ul conține doar litere (nu cifre sau simboluri)
    if (!/^[a-zA-Z]+$/.test(tld)) {
      return false;
    }
    
    return true;
  }
  
  isValidPhoneNumber(phone: string): boolean {
    const phoneRegex = /^07\d{8}$/;
    return phoneRegex.test(phone);
  }

  // Validări pentru sistemele particulare
  validateCustomStep1(): boolean {
    // Resetăm erorile
    this.validationErrors.custom.name = false;
    this.validationErrors.custom.description = false;
    
    let isValid = true;
    
    // Validează numele votului și descrierea
    if (!this.customSystem.name || this.customSystem.name.trim() === '') {
      this.validationErrors.custom.name = true;
      isValid = false;
      alert('Numele votului este obligatoriu.');
    }
    
    if (!this.customSystem.description || this.customSystem.description.trim() === '') {
      this.validationErrors.custom.description = true;
      isValid = false;
      alert('Descrierea votului este obligatorie.');
    }
    
    return isValid;
  }

  validateCustomStep2(): boolean {
    // Resetăm erorile
    this.validationErrors.custom.options = false;
    
    // Verifică dacă există cel puțin o opțiune de vot
    const optionInputs = document.querySelectorAll('.option-item input[type="text"]:first-child') as NodeListOf<HTMLInputElement>;
    
    if (!optionInputs || optionInputs.length === 0) {
      this.validationErrors.custom.options = true;
      alert('Trebuie să adăugați cel puțin o opțiune de vot.');
      return false;
    }
    
    // Verifică dacă fiecare opțiune are un titlu
    let allValid = true;
    optionInputs.forEach(input => {
      if (!input.value.trim()) {
        allValid = false;
      }
    });
    
    if (!allValid) {
      this.validationErrors.custom.options = true;
      alert('Toate opțiunile de vot trebuie să aibă un nume valid.');
      return false;
    }
    
    return true;
  }

  validateCustomStep3(): boolean {
    // Resetăm erorile
    this.validationErrors.custom.participants = false;
    
    // Verifică dacă există emailuri adăugate
    if (!this.customSystem.participants || this.customSystem.participants.trim() === '') {
      this.validationErrors.custom.participants = true;
      alert('Trebuie să adăugați cel puțin o adresă de email.');
      return false;
    }
    
    // Verifică dacă există cel puțin 5 emailuri
    const emails = this.customSystem.participants.split('\n').filter(email => email.trim());
    if (emails.length < 5) {
      this.validationErrors.custom.participants = true;
      alert('Trebuie să adăugați cel puțin 5 adrese de email valide.');
      return false;
    }
    
    // Verifică dacă emailurile sunt valide
    let allEmailsValid = true;
    for (const email of emails) {
      if (!this.isValidEmail(email.trim())) {
        allEmailsValid = false;
        break;
      }
    }
    
    if (!allEmailsValid) {
      this.validationErrors.custom.participants = true;
      alert('Toate adresele de email trebuie să fie valide.');
      return false;
    }
    
    return true;
  }

  validateCustomVoteStep(): boolean {
    // Resetăm erorile
    this.validationErrors.custom.token = false;
    this.validationErrors.custom.option = false;
    
    // Verifică dacă tokenul a fost verificat
    if (!this.tokenVerified) {
      this.validationErrors.custom.token = true;
      alert('Trebuie să introduceți un cod de vot valid pentru a continua.');
      return false;
    }
    
    // Verifică dacă a fost selectată o opțiune de vot
    if (this.selectedCustomOption === null) {
      this.validationErrors.custom.option = true;
      alert('Trebuie să selectați o opțiune pentru a putea vota.');
      return false;
    }
    
    return true;
  }
}