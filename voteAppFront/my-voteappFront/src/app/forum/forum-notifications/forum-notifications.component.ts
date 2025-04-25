import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ForumService, Notification } from '../../services/forum.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-forum-notifications',
  templateUrl: './forum-notifications.component.html',
  styleUrls: ['./forum-notifications.component.scss']
})
export class ForumNotificationsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  notifications: Notification[] = [];
  filteredNotifications: Notification[] = [];
  loading = true;
  error = false;
  filterType = 'all';

  // Variabile pentru mesaje de confirmare
  showPreferencesConfirmation = false;
  preferencesMessage = '';
  
  // Setări pentru notificări
  notificationSettings = {
    replies: true,
    mentions: true,
    topicReplies: true
  };
  
  // Stări pentru newsletter
  showEmailField = false;
  showNewsletterConfirmation = false;
  newsletterForm: FormGroup;

  constructor(
    private forumService: ForumService,
    private router: Router,
    private titleService: Title,
    private fb: FormBuilder
  ) {
    // Inițializare formular newsletter
    this.newsletterForm = this.fb.group({
      subscribed: [false],
      email: ['', [Validators.required, Validators.email]]
    });
  }

  ngOnInit(): void {
    this.titleService.setTitle('Notificări | Forum SmartVote');
    this.loadNotifications();
    this.loadUserPreferences();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Încărcarea notificărilor utilizatorului
  loadNotifications(): void {
    this.loading = true;
    this.error = false;
    
    this.forumService.getNotifications()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (notifications) => {
          this.notifications = notifications;
          this.applyFilter();
          this.loading = false;
        },
        error: (error) => {
          console.error('Eroare la încărcarea notificărilor:', error);
          this.error = true;
          this.loading = false;
        }
      });
  }
  
  // Încărcarea preferințelor utilizatorului
  loadUserPreferences(): void {
    this.forumService.getNotificationPreferences()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (preferences) => {
          // Actualizăm setările locale cu cele de pe server
          this.notificationSettings = {
            replies: preferences.notify_replies ?? true,
            mentions: preferences.notify_mentions ?? true,
            topicReplies: preferences.notify_topic_replies ?? true
          };
        },
        error: (error) => {
          console.error('Eroare la încărcarea preferințelor:', error);
          // Folosim valori implicite dacă încărcarea eșuează
        }
      });
      
    // Verificăm dacă utilizatorul este abonat la newsletter
    this.forumService.getNewsletterStatus()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (status) => {
          this.newsletterForm.patchValue({
            subscribed: status.subscribed,
            email: status.email || ''
          });
          
          // Arată câmpul de email dacă utilizatorul este abonat
          this.showEmailField = status.subscribed;
        },
        error: (error) => {
          console.error('Eroare la verificarea statusului newsletter:', error);
        }
      });
  }

  // Salvarea preferințelor de notificări
  saveNotificationPreferences(): void {
    const preferences = {
      notify_replies: this.notificationSettings.replies,
      notify_mentions: this.notificationSettings.mentions,
      notify_topic_replies: this.notificationSettings.topicReplies
    };
    
    this.forumService.updateNotificationPreferences(preferences)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          console.log('Preferințe salvate cu succes:', response);
          
          // Afișăm mesajul de confirmare
          this.preferencesMessage = 'Preferințele au fost salvate cu succes!';
          this.showPreferencesConfirmation = true;
          
          // Ascundem mesajul după 3 secunde
          setTimeout(() => {
            this.closePreferencesConfirmation();
          }, 3000);
        },
        error: (error) => {
          console.error('Eroare la salvarea preferințelor:', error);
          
          // Afișăm mesaj de eroare
          this.preferencesMessage = 'A apărut o eroare la salvarea preferințelor. Încercați din nou.';
          this.showPreferencesConfirmation = true;
        }
      });
  }
  
  // Închidere dialog confirmare preferințe
  closePreferencesConfirmation(): void {
    this.showPreferencesConfirmation = false;
  }
  
  // Închidere toate dialogurile
  closeAllDialogs(): void {
    this.showNewsletterConfirmation = false;
    this.showPreferencesConfirmation = false;
  }
  
  // Toggle pentru câmpul de email
  toggleEmailField(): void {
    const subscribed = this.newsletterForm.get('subscribed')?.value;
    this.showEmailField = subscribed;
    
    if (!subscribed) {
      // Dacă utilizatorul dezactivează abonarea, anulăm abonamentul
      this.forumService.unsubscribeFromNewsletter()
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            console.log('Dezabonare reușită');
          },
          error: (error) => {
            console.error('Eroare la dezabonare:', error);
          }
        });
    }
  }
  
  // Abonare la newsletter
  subscribeToNewsletter(): void {
    if (this.newsletterForm.invalid) return;
    
    const email = this.newsletterForm.get('email')?.value;
    
    this.forumService.subscribeToNewsletter(email)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          console.log('Abonare reușită');
          this.showNewsletterConfirmation = true;
          
          // Ascundem mesajul după 3 secunde
          setTimeout(() => {
            this.closeNewsletterConfirmation();
          }, 3000);
        },
        error: (error) => {
          console.error('Eroare la abonare:', error);
          // Aici ai putea adăuga un mesaj de eroare
        }
      });
  }
  
  // Închidere dialog confirmare newsletter
  closeNewsletterConfirmation(): void {
    this.showNewsletterConfirmation = false;
  }

  // Filtrare notificări
  applyFilter(): void {
    if (this.filterType === 'all') {
      this.filteredNotifications = [...this.notifications];
    } else if (this.filterType === 'unread') {
      this.filteredNotifications = this.notifications.filter(notification => !notification.is_read);
    } else if (this.filterType === 'read') {
      this.filteredNotifications = this.notifications.filter(notification => notification.is_read);
    }
  }

  // Marcare notificare ca citită
  markAsRead(notification: Notification): void {
    if (notification.is_read) return;
    
    this.forumService.markNotificationAsRead(notification.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          notification.is_read = true;
          if (this.filterType === 'unread') {
            this.applyFilter();
          }
        },
        error: (error) => {
          console.error('Eroare la marcarea notificării ca citită:', error);
        }
      });
  }

  // Marcare toate notificările ca citite
  markAllAsRead(): void {
    const unreadNotifications = this.notifications.filter(notification => !notification.is_read);
    if (unreadNotifications.length === 0) return;
    
    this.forumService.markAllNotificationsAsRead()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.notifications.forEach(notification => {
            notification.is_read = true;
          });
          if (this.filterType === 'unread') {
            this.applyFilter();
          }
        },
        error: (error) => {
          console.error('Eroare la marcarea tuturor notificărilor ca citite:', error);
        }
      });
  }

  // Navigare la notificare
  navigateToNotification(notification: Notification): void {
    // Marchează notificarea ca citită dacă nu este deja
    if (!notification.is_read) {
      this.markAsRead(notification);
    }
    
    // Utilizăm type assertion pentru a evita erorile TypeScript
    const notif = notification as any;
    
    // Navigare în funcție de tipul notificării
    if (notif.topic_slug && notif.topic_id) {
      this.router.navigate(
        ['/menu/forum/topic', notif.topic_slug], 
        { queryParams: { id: notif.topic_id } }
      );
    } else {
      this.router.navigate(['/menu/forumuri']);
    }
  }
  
  // Navigare către pagina principală a forumului
  navigateToForum(): void {
    this.router.navigate(['/menu/forumuri']);
  }

  // Obține icon pentru tipul de notificare
  getNotificationIcon(type: string): string {
    switch(type) {
      case 'reply':
      case 'new_post': return '#icon-message';
      case 'mention': return '#icon-user-check';
      case 'topic_reply': return '#icon-comments';
      case 'topic_update': return '#icon-notification';
      case 'system': return '#icon-bullhorn';
      case 'solution': return '#icon-check-square';
      default: return '#icon-bell';
    }
  }

  // Obține etichetă pentru tipul de notificare
  getNotificationTypeLabel(type: string): string {
    switch(type) {
      case 'reply':
      case 'new_post': return 'Răspuns nou';
      case 'mention': return 'Ați fost menționat';
      case 'topic_reply': return 'Răspuns la subiect';
      case 'topic_update': return 'Actualizare subiect';
      case 'system': return 'Notificare sistem';
      case 'solution': return 'Răspuns marcat ca soluție';
      default: return 'Notificare';
    }
  }
}