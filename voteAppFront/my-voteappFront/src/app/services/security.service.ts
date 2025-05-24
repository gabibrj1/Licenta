import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SecurityService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Dashboard și evenimente principale
  getDashboard(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/dashboard/`);
  }

  getSecurityEvents(page: number = 1, pageSize: number = 20, eventType?: string, riskLevel?: string): Observable<any> {
    const params: any = {
      page: page.toString(),
      page_size: pageSize.toString()
    };
    
    if (eventType) {
      params.event_type = eventType;
    }
    
    if (riskLevel) {
      params.risk_level = riskLevel;
    }
    
    return this.http.get(`${this.apiUrl}security/events/`, { params });
  }

  // Gestionarea sesiunilor
  getUserSessions(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/sessions/`);
  }

  terminateSession(sessionKey: string): Observable<any> {
    return this.http.post(`${this.apiUrl}security/sessions/terminate/`, {
      session_key: sessionKey
    });
  }

  terminateAllSessions(): Observable<any> {
    return this.http.delete(`${this.apiUrl}security/sessions/`);
  }

  // Gestionarea alertelor
  getSecurityAlerts(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/alerts/`);
  }

  acknowledgeAlert(alertId: string): Observable<any> {
    return this.http.patch(`${this.apiUrl}security/alerts/`, {
      alert_id: alertId
    });
  }

  // Analize și statistici
  getAnalytics(days: number = 30): Observable<any> {
    return this.http.get(`${this.apiUrl}security/analytics/`, {
      params: { days: days.toString() }
    });
  }

  // CAPTCHA
  getCaptchaStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/captcha/stats/`);
  }

  logCaptchaAttempt(isSuccess: boolean, captchaType: string = 'recaptcha', context: string = ''): Observable<any> {
    return this.http.post(`${this.apiUrl}security/captcha/log/`, {
      is_success: isSuccess,
      captcha_type: captchaType,
      context: context
    });
  }

  logCaptchaResult(success: boolean, context: string): void {
    this.logCaptchaAttempt(success, 'recaptcha', context).subscribe({
      next: () => {
        console.log(`CAPTCHA ${success ? 'success' : 'failure'} logged for context: ${context}`);
      },
      error: (error) => {
        console.error('Error logging CAPTCHA attempt:', error);
      }
    });
  }

  // Device Management - ÎMBUNĂTĂȚIT
  getTrustedDevices(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/devices/trusted/`);
  }

  // NOUĂ METODĂ - Pentru toate dispozitivele
  getAllDevices(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/devices/all/`);
  }

  getDeviceStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/devices/stats/`);
  }

  updateDeviceTrust(fingerprintHash: string, action: 'trust' | 'untrust'): Observable<any> {
    return this.http.patch(`${this.apiUrl}security/devices/trusted/`, {
      fingerprint_hash: fingerprintHash,
      action: action
    });
  }

  // Metodă pentru logarea evenimentelor de securitate custom
  logSecurityEvent(eventType: string, description: string, additionalData?: any): Observable<any> {
    return this.http.post(`${this.apiUrl}security/events/log/`, {
      event_type: eventType,
      description: description,
      additional_data: additionalData || {}
    });
  }

  // Metodă pentru logarea evenimentelor specifice votului
  logVoteSecurityEvent(eventType: string, description: string, additionalData?: any): Observable<any> {
    return this.http.post(`${this.apiUrl}security/vote-events/`, {
      event_type: eventType,
      description: description,
      additional_data: additionalData || {}
    });
  }

  // Metodă pentru detectarea automată a device-ului
  detectAndSendDeviceInfo(): void {
    const deviceInfo = this.getDeviceInfo();
    
    this.http.post(`${this.apiUrl}security/fingerprint/`, deviceInfo).subscribe({
      next: (response) => {
        console.log('Device fingerprint sent successfully:', response);
      },
      error: (error) => {
        console.error('Error sending device fingerprint:', error);
      }
    });
  }

  // Metodă pentru logarea acțiunilor utilizatorului
  logUserAction(action: string, page: string, details?: any): void {
    const logData = {
      event_type: 'page_visit',
      description: `${action} pe pagina ${page}`,
      additional_data: {
        action: action,
        page: page,
        timestamp: new Date().toISOString(),
        ...details
      }
    };

    this.logSecurityEvent(logData.event_type, logData.description, logData.additional_data).subscribe({
      next: () => {
        console.log(`Acțiune logată: ${action} pe ${page}`);
      },
      error: (error) => {
        console.error('Eroare la logarea acțiunii:', error);
      }
    });
  }

  // Metodă pentru verificarea stării de securitate în timp real
  getSecurityStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}security/status/`);
  }

  // Metodă pentru logarea schimbărilor în încrederea dispozitivelor
  logDeviceTrustChange(deviceId: string, action: string, details?: any): void {
    this.logSecurityEvent(
      'device_trust_changed',
      `Starea de încredere schimbată pentru dispozitiv: ${action}`,
      {
        device_id: deviceId,
        action: action,
        timestamp: new Date().toISOString(),
        ...details
      }
    ).subscribe({
      next: () => {
        console.log(`Device trust change logged: ${action} for device ${deviceId}`);
      },
      error: (error) => {
        console.error('Error logging device trust change:', error);
      }
    });
  }

  private getDeviceInfo(): any {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    let canvasFingerprint = '';
    
    if (ctx) {
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('Device fingerprint canvas 🔒', 2, 2);
      canvasFingerprint = canvas.toDataURL().substring(0, 50);
    }

    return {
      screen_resolution: `${screen.width}x${screen.height}`,
      color_depth: screen.colorDepth,
      timezone_offset: new Date().getTimezoneOffset(),
      language: navigator.language || (navigator as any).userLanguage,
      platform: navigator.platform,
      user_agent: navigator.userAgent,
      has_cookies: navigator.cookieEnabled,
      has_local_storage: typeof(Storage) !== "undefined",
      has_session_storage: typeof(sessionStorage) !== "undefined",
      canvas_fingerprint: canvasFingerprint,
      device_type: this.detectDeviceType(),
      device_memory: (navigator as any).deviceMemory || 'unknown',
      hardware_concurrency: navigator.hardwareConcurrency || 'unknown'
    };
  }

  private detectDeviceType(): string {
    const userAgent = navigator.userAgent.toLowerCase();
    
    if (/tablet|ipad|playbook|silk/i.test(userAgent)) {
      return 'tablet';
    }
    if (/mobi|android|touch|blackberry|nokia|windows phone/i.test(userAgent)) {
      return 'mobile';
    }
    return 'desktop';
  }
}