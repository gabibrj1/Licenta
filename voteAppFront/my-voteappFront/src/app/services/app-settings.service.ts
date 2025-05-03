// src/app/services/app-settings.service.ts
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { BehaviorSubject } from 'rxjs';

export interface AppSettings {
  language: string;
  highContrast: boolean;
  largeFont: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AppSettingsService {
  // Valorile implicite
  private defaultSettings: AppSettings = {
    language: 'ro',
    highContrast: false,
    largeFont: false
  };

  // BehaviorSubject pentru setări actualizabile
  private settingsSubject = new BehaviorSubject<AppSettings>(this.defaultSettings);
  public settings$ = this.settingsSubject.asObservable();

  constructor(private translate: TranslateService) {
    // Limbile disponibile
    translate.addLangs(['ro', 'en', 'hu']);
    translate.setDefaultLang('ro');

    // Încărcăm setările din localStorage
    this.loadSettings();
  }

  private loadSettings() {
    try {
      const savedSettings = localStorage.getItem('app_settings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        this.settingsSubject.next(settings);
        
        // Aplicăm setările încărcate
        this.applySettings(settings);
      }
    } catch (e) {
      console.error('Eroare la încărcarea setărilor:', e);
    }
  }

  updateSettings(settings: Partial<AppSettings>) {
    // Actualizăm setările cu proprietățile noi
    const currentSettings = this.settingsSubject.value;
    const newSettings = {...currentSettings, ...settings};
    
    // Salvăm în localStorage
    localStorage.setItem('app_settings', JSON.stringify(newSettings));
    
    // Actualizăm BehaviorSubject
    this.settingsSubject.next(newSettings);
    
    // Aplicăm setările
    this.applySettings(newSettings);
  }

  private applySettings(settings: AppSettings) {
    // Aplicare limbă
    this.translate.use(settings.language);
    
    // Setare atribut lang pe html
    document.documentElement.lang = settings.language;
    
    // Aplicare contrast ridicat
    if (settings.highContrast) {
      document.body.classList.add('high-contrast-theme');
    } else {
      document.body.classList.remove('high-contrast-theme');
    }
    
    // Aplicare font mărit
    if (settings.largeFont) {
      document.body.classList.add('large-font-theme');
    } else {
      document.body.classList.remove('large-font-theme');
    }
  }
}