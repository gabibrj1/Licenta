import { Component, HostListener, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { UserService } from '../user.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent {
  feedback = {
    name: '',
    phone: '',
    email: '',
    message: '',
    phonePrefix: ''

  };
  isProfaneMessage = false;
  countries = [
    { name: 'Romania', prefix: '+40' },
    { name: 'United States', prefix: '+1' },
    { name: 'United Kingdom', prefix: '+44' },
    { name: 'Germany', prefix: '+49' },
    { name: 'France', prefix: '+33' },
    { name: 'Italy', prefix: '+39' },
    { name: 'Spain', prefix: '+34' },
    { name: 'Netherlands', prefix: '+31' },
    { name: 'Switzerland', prefix: '+41' },
    { name: 'Poland', prefix: '+48' },
    { name: 'Sweden', prefix: '+46' },
    { name: 'Norway', prefix: '+47' },
    { name: 'Austria', prefix: '+43' },
    { name: 'Russia', prefix: '+7' },
    { name: 'Belgium', prefix: '+32' },
    { name: 'Greece', prefix: '+30' },
    { name: 'Denmark', prefix: '+45' },
    { name: 'Ireland', prefix: '+353' },
    { name: 'Portugal', prefix: '+351' },
    { name: 'Finland', prefix: '+358' },

    // America de Nord
    { name: 'Canada', prefix: '+1' },
    { name: 'Mexico', prefix: '+52' },

    // Asia
    { name: 'China', prefix: '+86' },
    { name: 'Japan', prefix: '+81' },
    { name: 'India', prefix: '+91' },
    { name: 'South Korea', prefix: '+82' },

    // America de Sud
    { name: 'Brazil', prefix: '+55' },
    { name: 'Argentina', prefix: '+54' },
    { name: 'Chile', prefix: '+56' },
    { name: 'Colombia', prefix: '+57' },

    // Africa
    { name: 'South Africa', prefix: '+27' },
    { name: 'Egypt', prefix: '+20' },
    { name: 'Nigeria', prefix: '+234' },
    { name: 'Kenya', prefix: '+254' },

    // Oceania
    { name: 'Australia', prefix: '+61' },
    { name: 'New Zealand', prefix: '+64' }
];
onNameChange() {
  // Capitalizare pentru fiecare cuvânt din nume
  this.feedback.name = this.feedback.name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
checkMessage(message: string) {
  this.userService.checkProfanity(message).subscribe(response => {
    this.isProfaneMessage = response.containsProfanity;
  });

  // Verificăm numărul minim de cuvinte
  const wordCount = message.split(' ').filter(word => word.trim().length > 0).length;
  this.isProfaneMessage = this.isProfaneMessage || wordCount < 20;
}


onPhonePrefixChange(event: Event) {
  const selectedPrefix = (event.target as HTMLSelectElement).value;
  this.feedback.phone = this.feedback.phone.replace(this.feedback.phonePrefix, '').trim(); // elimină prefixul anterior
  this.feedback.phonePrefix = selectedPrefix; // actualizează prefixul curent
  this.feedback.phone = this.feedback.phonePrefix; // adaugă doar prefixul curent în câmp
}


  reviews = [
    {
      feedback: 'Platforma de vot este intuitivă și sigură. Am economisit timp valoros.',
      name: 'Andrei P.',
      position: 'Director IT',
      rating: 5
    },
    {
      feedback: 'Sunt foarte mulțumit de serviciile oferite. Recomand cu căldură!',
      name: 'Ioana M.',
      position: 'Manager Proiect',
      rating: 4
    },
    {
      feedback: 'Procesul de vot a fost simplu și rapid. Totul a decurs fără probleme.',
      name: 'Gabriel T.',
      position: 'Student',
      rating: 5
    },
    {
      feedback: 'Am folosit VotAI pentru alegerile companiei. A fost o experiență excelentă!',
      name: 'Maria F.',
      position: 'CEO',
      rating: 5
    }
  ];

  loading = {
    signup: false,
    home: false,
    feedback: false
  };
  isMenuOpen = false;
  menuTimeout: any;
  isTop = true;
  isInFooter = false;

  @ViewChild('footer', { static: false }) footer!: ElementRef;

  constructor(
    private router: Router, 
    private userService: UserService, 
    private snackBar: MatSnackBar
  ) {}

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
    if (this.isMenuOpen) {
      this.startMenuTimeout();
    } else {
      this.clearMenuTimeout();
    }
  }

  startMenuTimeout() {
    this.clearMenuTimeout();
    this.menuTimeout = setTimeout(() => {
      this.isMenuOpen = false;
    }, 10000);
  }

  clearMenuTimeout() {
    if (this.menuTimeout) {
      clearTimeout(this.menuTimeout);
      this.menuTimeout = null;
    }
  }

  resetMenuTimeout() {
    if (this.isMenuOpen) {
      this.startMenuTimeout();
    }
  }

  @HostListener('window:scroll', [])
  onScroll() {
    const scrollPosition = window.scrollY + window.innerHeight;
    const footerPosition = this.footer?.nativeElement.offsetTop;
  
    this.isTop = window.scrollY < 100;
    this.isInFooter = scrollPosition >= footerPosition;
  
    // Închide meniul dacă este deschis
    if (this.isMenuOpen) {
      this.isMenuOpen = false;
      this.clearMenuTimeout(); // Curăță timeout-ul
    }
  }

  scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  navigateTo(route: string) {
    if (route === 'auth') {
      this.loading.signup = true;
    } else if (route === '') {
      this.loading.home = true;
    }

    setTimeout(() => {
      this.router.navigate([route]).finally(() => {
        this.loading.signup = false;
        this.loading.home = false;
        this.isMenuOpen = false;
      });
    }, 300);
  }

  scrollToContact() {
    this.closeMenu();
    document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' });
  }

  closeMenu() {
    this.isMenuOpen = false;
  }
  checkProfanity(message: string) {
    this.userService.checkProfanity(message).subscribe(response => {
      this.isProfaneMessage = response.containsProfanity;
  
      if (this.isProfaneMessage) {
        // Afișăm mesajul de eroare și dezactivăm butonul
        this.snackBar.open('Mesajul conține limbaj nepotrivit și nu poate fi trimis.', 'Închide', { duration: 3000 });
      }
    }, error => {
      console.error('Eroare la verificarea limbajului nepotrivit:', error);
    });
  }
  onMessageChange(event: any) {
    const message = event.target.value;
    this.feedback.message = message; // Actualizăm mesajul
    this.checkProfanity(message); // Verificăm injuriile
  }

  onSubmitContactForm() {
    const wordCount = this.feedback.message.split(' ').filter(word => word.trim().length > 0).length;
    
     // Verificăm dacă mesajul este valid înainte de trimitere
  if (this.isProfaneMessage) {
    this.snackBar.open('Mesajul conține limbaj nepotrivit.', 'Închide', { duration: 3000 });
    return;
  }
    // Verificăm dacă mesajul este valid înainte de trimitere
    if (wordCount < 20) {
      this.snackBar.open('Mesajul trebuie să conțină minim 20 de cuvinte.', 'Închide', { duration: 3000 });
      return;
    }
  
    this.loading.feedback = true;
    this.userService.sendFeedback(this.feedback).subscribe({
      next: (response: any) => {
        this.snackBar.open(response.message, 'Închide', { duration: 3000 });
        this.feedback = { name: '', phone: '', email: '', message: '', phonePrefix: '' };
        this.loading.feedback = false;
      },
      error: (err) => {
        if (err.error.error === 'Mesajul conține limbaj nepotrivit și nu a fost trimis.') {
          this.snackBar.open('Mesajul conține limbaj nepotrivit.', 'Închide', { duration: 3000 });
        } else if (err.status === 400) {
          this.snackBar.open(err.error.error || 'Mesaj invalid.', 'Închide', { duration: 3000 });
        } else if (err.status === 403) {
          this.snackBar.open('Se poate trimite feedback numai dacă sunteți autentificat.', 'Închide', { duration: 3000 });
          this.router.navigate(['/auth']);
        } else {
          this.snackBar.open('A apărut o eroare. Încercați din nou.', 'Închide', { duration: 3000 });
        }
        this.loading.feedback = false;
      }
    });
  }}