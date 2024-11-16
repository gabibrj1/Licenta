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
    message: ''
  };
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

  onSubmitContactForm() {
    this.loading.feedback = true;
    this.userService.sendFeedback(this.feedback).subscribe({
      next: (response: any) => {
        this.snackBar.open(response.message, 'Închide', { duration: 3000 });
        this.feedback = { name: '', phone: '', email: '', message: '' };
        this.loading.feedback = false;
      },
      error: (err) => {
        if (err.status === 403) {
          this.snackBar.open('Se poate trimite feedback numai dacă sunteți autentificat.', 'Închide', { duration: 3000 });
          this.router.navigate(['/auth']);
        } else {
          this.snackBar.open('A apărut o eroare. Încercați din nou.', 'Închide', { duration: 3000 });
        }
        this.loading.feedback = false;
      }
    });
  }
}
