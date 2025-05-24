import { Component, OnInit, OnDestroy } from '@angular/core';
import { SecurityService } from '../services/security.service';
import { Subscription, interval } from 'rxjs';
import { switchMap } from 'rxjs/operators';

export interface SecurityDashboard {
  statistics: {
    total_events: number;
    recent_events: number;
    active_sessions: number;
    active_alerts: number;
  };
  recent_events: SecurityEvent[];
  active_sessions: UserSession[];
  alerts: SecurityAlert[];
  security_score: number;
}

export interface SecurityEvent {
  id: string;
  event_type: string;
  event_type_display: string;
  description: string;
  risk_level: string;
  risk_level_display: string;
  ip_address: string;
  timestamp: string;
  device_info: any;
  location_info: any;
}

export interface UserSession {
  id: string;
  ip_address: string;
  device_info: any;
  location_info: any;
  created_at: string;
  last_activity: string;
  is_current: boolean;
  duration: string;
}

export interface SecurityAlert {
  id: string;
  alert_type: string;
  alert_type_display: string;
  severity: string;
  severity_display: string;
  title: string;
  message: string;
  created_at: string;
  requires_user_action: boolean;
}

export interface CaptchaStats {
  period_days: number;
  total_attempts: number;
  successful_attempts: number;
  failed_attempts: number;
  success_rate: number;
  context_breakdown: any[];
}

export interface DeviceStats {
  total_devices: number;
  trusted_devices: number;
  suspicious_devices: number;
  recent_devices: number;
  trust_ratio: number;
}

export interface TrustedDevice {
  id: string;
  fingerprint_hash: string;
  platform: string;
  screen_resolution: string;
  first_seen: string;
  last_seen: string;
  usage_count: number;
  is_trusted: boolean;
  is_current: boolean;
}

@Component({
  selector: 'app-security',
  templateUrl: './security.component.html',
  styleUrls: ['./security.component.scss']
})
export class SecurityComponent implements OnInit, OnDestroy {
  
  // Datele principale
  dashboard: SecurityDashboard | null = null;
  securityEvents: SecurityEvent[] = [];
  userSessions: UserSession[] = [];
  securityAlerts: SecurityAlert[] = [];
  analytics: any = null;
  captchaStats: CaptchaStats | null = null;
  deviceStats: DeviceStats | null = null;
  trustedDevices: TrustedDevice[] = [];
  allDevices: TrustedDevice[] = [];
  
  // Starea componentei
  isLoading = true;
  error = '';
  currentTab = 'dashboard';
  
  // Pentru paginare și filtrare
  eventsPage = 1;
  eventsPageSize = 20;
  eventsTotalPages = 1;
  selectedEventType = '';
  selectedRiskLevel = '';
  availableFilters: any = null;
  
  // Pentru analize
  analyticsRange = 30; // ultimele 30 de zile
  
  // Auto-refresh pentru date live
  private refreshSubscription?: Subscription;
  
  constructor(private securityService: SecurityService) {}

  ngOnInit(): void {
    // Detectează și trimite informații despre dispozitiv
    this.securityService.detectAndSendDeviceInfo();
    
    // Încarcă dashboard-ul
    this.loadDashboard();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  startAutoRefresh(): void {
    // Actualizează dashboard-ul la fiecare 30 secunde
    this.refreshSubscription = interval(30000)
      .pipe(
        switchMap(() => this.securityService.getDashboard())
      )
      .subscribe({
        next: (dashboard) => {
          this.dashboard = dashboard;
        },
        error: (error) => {
          console.error('Eroare la auto-refresh:', error);
        }
      });
  }

  stopAutoRefresh(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  loadDashboard(): void {
    this.isLoading = true;
    this.error = '';
    
    this.securityService.getDashboard().subscribe({
      next: (dashboard) => {
        this.dashboard = dashboard;
        this.isLoading = false;
        
        // Logează accesul la dashboard
        this.securityService.logSecurityEvent(
          'profile_access',
          'Acces la dashboard-ul de securitate',
          { page: 'security_dashboard' }
        ).subscribe();
      },
      error: (error) => {
        this.error = 'Eroare la încărcarea dashboard-ului de securitate: ' + (error.error?.message || error.message);
        this.isLoading = false;
        console.error('Dashboard error:', error);
      }
    });
  }

  switchTab(tab: string): void {
    this.currentTab = tab;
    this.error = '';
    
    // Logează accesul la diferite tab-uri
    this.securityService.logSecurityEvent(
      'page_visit',
      `Acces la tab-ul de securitate: ${tab}`,
      { tab: tab, page: 'security' }
    ).subscribe();
    
    switch (tab) {
      case 'events':
        this.loadSecurityEvents();
        break;
      case 'sessions':
        this.loadUserSessions();
        break;
      case 'alerts':
        this.loadSecurityAlerts();
        break;
      case 'analytics':
        this.loadAnalytics();
        this.loadCaptchaStats();
        break;
      case 'devices':
        this.loadDeviceStats();
        this.loadAllDevices();
        break;
    }
  }

  loadSecurityEvents(): void {
    this.isLoading = true;
    
    this.securityService.getSecurityEvents(
      this.eventsPage,
      this.eventsPageSize,
      this.selectedEventType,
      this.selectedRiskLevel
    ).subscribe({
      next: (response) => {
        this.securityEvents = response.events;
        this.eventsTotalPages = response.pagination.total_pages;
        this.availableFilters = response.available_filters;
        this.isLoading = false;
      },
      error: (error) => {
        this.error = 'Eroare la încărcarea evenimentelor: ' + (error.error?.message || error.message);
        this.isLoading = false;
      }
    });
  }

  loadUserSessions(): void {
    this.isLoading = true;
    
    this.securityService.getUserSessions().subscribe({
      next: (response) => {
        this.userSessions = response.sessions;
        this.isLoading = false;
      },
      error: (error) => {
        this.error = 'Eroare la încărcarea sesiunilor: ' + (error.error?.message || error.message);
        this.isLoading = false;
      }
    });
  }

  loadSecurityAlerts(): void {
    this.isLoading = true;
    
    this.securityService.getSecurityAlerts().subscribe({
      next: (response) => {
        this.securityAlerts = response.alerts;
        this.isLoading = false;
      },
      error: (error) => {
        this.error = 'Eroare la încărcarea alertelor: ' + (error.error?.message || error.message);
        this.isLoading = false;
      }
    });
  }

  loadAnalytics(): void {
    this.isLoading = true;
    
    this.securityService.getAnalytics(this.analyticsRange).subscribe({
      next: (analytics) => {
        this.analytics = analytics;
        this.isLoading = false;
      },
      error: (error) => {
        this.error = 'Eroare la încărcarea analizelor: ' + (error.error?.message || error.message);
        this.isLoading = false;
      }
    });
  }

  loadCaptchaStats(): void {
    this.securityService.getCaptchaStats().subscribe({
      next: (stats) => {
        this.captchaStats = stats;
      },
      error: (error) => {
        console.error('Eroare la încărcarea statisticilor CAPTCHA:', error);
      }
    });
  }

  loadDeviceStats(): void {
    this.securityService.getDeviceStats().subscribe({
      next: (stats) => {
        this.deviceStats = stats;
      },
      error: (error) => {
        console.error('Eroare la încărcarea statisticilor dispozitive:', error);
      }
    });
  }

  loadAllDevices(): void {
    this.isLoading = true;
    
    this.securityService.getAllDevices().subscribe({
      next: (response) => {
        this.allDevices = response.all_devices || [];
        this.trustedDevices = this.allDevices.filter(device => device.is_trusted);
        this.isLoading = false;
      },
      error: (error) => {
        this.error = 'Eroare la încărcarea dispozitivelor: ' + (error.error?.message || error.message);
        this.isLoading = false;
      }
    });
  }

  // Acțiuni pentru sesiuni
  terminateSession(sessionId: string): void {
    if (confirm('Ești sigur că vrei să termini această sesiune? Vei fi deconectat din acel dispozitiv.')) {
      this.securityService.terminateSession(sessionId).subscribe({
        next: (response) => {
          console.log('Sesiune terminată:', response.message);
          this.loadUserSessions(); // Reîncarcă lista
          this.loadDashboard(); // Actualizează dashboard-ul
          
          // Afișează mesaj de succes
          this.showSuccessMessage('Sesiunea a fost terminată cu succes!');
        },
        error: (error) => {
          this.error = 'Eroare la terminarea sesiunii: ' + (error.error?.message || error.message);
        }
      });
    }
  }

  terminateAllSessions(): void {
    if (confirm('Ești sigur că vrei să termini toate sesiunile? Vei fi deconectat din toate dispozitivele except cel curent.')) {
      this.securityService.terminateAllSessions().subscribe({
        next: (response) => {
          console.log('Toate sesiunile terminate:', response.message);
          this.loadUserSessions(); // Reîncarcă lista
          this.loadDashboard(); // Actualizează dashboard-ul
          
          // Afișează mesaj de succes
          this.showSuccessMessage(`${response.terminated_sessions || 'Toate'} sesiunile au fost terminate cu succes!`);
        },
        error: (error) => {
          this.error = 'Eroare la terminarea sesiunilor: ' + (error.error?.message || error.message);
        }
      });
    }
  }

  // Acțiuni pentru alerte
  acknowledgeAlert(alertId: string): void {
    this.securityService.acknowledgeAlert(alertId).subscribe({
      next: (response) => {
        console.log('Alertă recunoscută:', response.message);
        this.loadSecurityAlerts(); // Reîncarcă lista
        this.loadDashboard(); // Actualizează dashboard-ul
      },
      error: (error) => {
        this.error = 'Eroare la recunoașterea alertei: ' + (error.error?.message || error.message);
      }
    });
  }

  // Acțiuni pentru dispozitive - ÎMBUNĂTĂȚIT
  updateDeviceTrust(device: TrustedDevice, action: 'trust' | 'untrust'): void {
    const actionText = action === 'trust' ? 'marcat ca de încredere' : 'eliminat din lista de încredere';
    
    if (confirm(`Ești sigur că vrei ca acest dispozitiv să fie ${actionText}?`)) {
      this.securityService.updateDeviceTrust(device.fingerprint_hash, action).subscribe({
        next: (response) => {
          console.log('Starea dispozitivului actualizată:', response.message);
          
          // Actualizează local starea dispozitivului
          const deviceIndex = this.allDevices.findIndex(d => d.id === device.id);
          if (deviceIndex > -1) {
            this.allDevices[deviceIndex].is_trusted = action === 'trust';
          }
          
          // Actualizează lista de dispozitive de încredere
          this.trustedDevices = this.allDevices.filter(d => d.is_trusted);
          
          // Actualizează statisticile în timp real
          this.updateDeviceStatsLocal(action);
          
          this.showSuccessMessage(`Dispozitivul a fost ${actionText} cu succes!`);
        },
        error: (error) => {
          this.error = 'Eroare la actualizarea stării dispozitivului: ' + (error.error?.message || error.message);
        }
      });
    }
  }

  // Actualizare locală a statisticilor
  private updateDeviceStatsLocal(action: 'trust' | 'untrust'): void {
    if (this.deviceStats) {
      if (action === 'trust') {
        this.deviceStats.trusted_devices++;
      } else {
        this.deviceStats.trusted_devices--;
      }
      
      // Recalculează ratio-ul
      this.deviceStats.trust_ratio = this.deviceStats.total_devices > 0 
        ? Math.round((this.deviceStats.trusted_devices / this.deviceStats.total_devices) * 100)
        : 0;
    }
  }

  // Filtrare evenimente
  applyEventFilters(): void {
    this.eventsPage = 1; // Reset la prima pagină
    this.loadSecurityEvents();
  }

  clearEventFilters(): void {
    this.selectedEventType = '';
    this.selectedRiskLevel = '';
    this.eventsPage = 1;
    this.loadSecurityEvents();
  }

  // Paginare
  onEventsPageChange(page: number): void {
    this.eventsPage = page;
    this.loadSecurityEvents();
  }

  getEventsPageNumbers(): number[] {
    const pages: number[] = [];
    const startPage = Math.max(1, this.eventsPage - 2);
    const endPage = Math.min(this.eventsTotalPages, this.eventsPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  }

  // Funcții helper
  getSecurityScoreColor(score: number | undefined): string {
    const validScore = score || 0;
    if (validScore >= 80) return '#4CAF50'; // Verde
    if (validScore >= 60) return '#FF9800'; // Portocaliu
    return '#f44336'; // Roșu
  }

  getSecurityScoreText(score: number | undefined): string {
    const validScore = score || 0;
    if (validScore >= 80) return 'Excelent';
    if (validScore >= 60) return 'Bun';
    if (validScore >= 40) return 'Mediu';
    return 'Scăzut';
  }

  getRiskLevelColor(riskLevel: string): string {
    switch (riskLevel) {
      case 'low': return '#4CAF50';
      case 'medium': return '#FF9800';
      case 'high': return '#f44336';
      case 'critical': return '#9C27B0';
      default: return '#757575';
    }
  }

  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'info': return '#2196F3';
      case 'warning': return '#FF9800';
      case 'error': return '#f44336';
      case 'critical': return '#9C27B0';
      default: return '#757575';
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('ro-RO');
  }

  formatDuration(durationString: string): string {
    // Parsează durata și formatează-o într-un mod prietenos
    if (!durationString) return 'Necunoscut';
    
    const parts = durationString.split(':');
    if (parts.length >= 2) {
      const hours = parseInt(parts[0], 10);
      const minutes = parseInt(parts[1], 10);
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      } else {
        return `${minutes}m`;
      }
    }
    
    return durationString;
  }

  getDeviceIcon(deviceInfo: any): string {
    if (!deviceInfo) return 'fas fa-question-circle';
    
    if (deviceInfo.is_mobile || deviceInfo.type === 'mobile') return 'fas fa-mobile-alt';
    if (deviceInfo.is_tablet || deviceInfo.type === 'tablet') return 'fas fa-tablet-alt';
    if (deviceInfo.is_pc || deviceInfo.type === 'desktop') return 'fas fa-desktop';
    
    return 'fas fa-laptop';
  }

  getDeviceDisplayName(deviceInfo: any): string {
    if (!deviceInfo) return 'Dispozitiv necunoscut';
    
    const browser = deviceInfo.browser || 'Browser necunoscut';
    const os = deviceInfo.os || 'OS necunoscut';
    
    return `${browser} pe ${os}`;
  }

  refreshCurrentTab(): void {
    switch (this.currentTab) {
      case 'dashboard':
        this.loadDashboard();
        break;
      case 'events':
        this.loadSecurityEvents();
        break;
      case 'sessions':
        this.loadUserSessions();
        break;
      case 'alerts':
        this.loadSecurityAlerts();
        break;
      case 'analytics':
        this.loadAnalytics();
        this.loadCaptchaStats();
        break;
      case 'devices':
        this.loadDeviceStats();
        this.loadAllDevices();
        break;
    }
  }

  changeAnalyticsRange(days: number): void {
    this.analyticsRange = days;
    this.loadAnalytics();
  }

  private showSuccessMessage(message: string): void {
    // Implementează afișarea unui mesaj de succes
    // Poți folosi un toast, notification sau alert simplu
    console.log('SUCCESS:', message);
    // Opțional: poți adăuga o proprietate pentru mesaje de succes
  }

  // Funcții helper pentru sesiuni
  getSessionStatusText(session: UserSession): string {
    if (session.is_current) {
      return 'Sesiunea curentă - dispozitivul pe care te afli acum';
    }
    return 'Sesiune activă pe alt dispozitiv';
  }

  getSessionSecurityLevel(session: UserSession): string {
    const device = session.device_info;
    if (!device) return 'unknown';
    
    // Logic pentru determinarea nivelului de securitate
    if (device.is_mobile) return 'medium';
    if (device.is_pc) return 'high';
    return 'medium';
  }

  // Funcții helper pentru dispozitive
  getDeviceSecurityStatus(device: TrustedDevice): string {
    if (device.is_current) return 'current';
    if (device.is_trusted) return 'trusted';
    return 'unknown';
  }

  canModifyDevice(device: TrustedDevice): boolean {
    return !device.is_current; // Nu poți modifica dispozitivul curent
  }
}