import { Component, OnInit, OnDestroy, Renderer2, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { AccessibilityService } from '../services/accessibility.service';
import { SecurityService } from '../services/security.service';
import { ScreenReaderService } from '../services/screen-reader.service';

export interface AccessibilitySettings {
  font_size: string;
  contrast_mode: string;
  animations: string;
  focus_highlights: boolean;
  extended_time: boolean;
  simplified_interface: boolean;
  audio_assistance: boolean;
  keyboard_navigation: boolean;
  extra_confirmations: boolean;
  large_buttons: boolean;
  screen_reader_support: boolean;
  audio_notifications: boolean;
}

export interface AccessibilityFeature {
  title: string;
  description: string;
  available: boolean;
}

@Component({
  selector: 'app-accessibility',
  templateUrl: './accessibility.component.html',
  styleUrls: ['./accessibility.component.scss']
})
export class AccessibilityComponent implements OnInit, OnDestroy {
  
  settings: AccessibilitySettings = {
    font_size: 'medium',
    contrast_mode: 'normal',
    animations: 'enabled',
    focus_highlights: false,
    extended_time: true, // Always enabled
    simplified_interface: false,
    audio_assistance: false,
    keyboard_navigation: false,
    extra_confirmations: true, // Always enabled
    large_buttons: false,
    screen_reader_support: false, // Start disabled, user must enable manually
    audio_notifications: false
  };
  
  features: AccessibilityFeature[] = [];
  contactInfo: any = null;
  
  isLoading = true;
  isSaving = false;
  error = '';
  successMessage = '';
  
  // Screen Reader Status
  isScreenReaderActive = false;
  screenReaderStatus = 'Dezactivat';
  
  // Keyboard Navigation Test Status
  isKeyboardTestActive = false;
  keyboardTestStatus = 'Inactiv';
  
  // Track if screen reader was auto-enabled by audio assistance
  private screenReaderAutoEnabled = false;
  // Track if keyboard test was auto-enabled by keyboard navigation
  private keyboardTestAutoEnabled = false;
  
  private audioContext: AudioContext | null = null;
  private skipLinksAdded = false;
  private keyboardListener?: () => void;
  
  fontSizeOptions = [
    { value: 'small', label: 'Mic (14px)' },
    { value: 'medium', label: 'Mediu (16px)' },
    { value: 'large', label: 'Mare (18px)' },
    { value: 'extra_large', label: 'Extra Mare (22px)' }
  ];
  
  contrastOptions = [
    { value: 'normal', label: 'Normal' },
    { value: 'high', label: 'Contrast Ridicat' },
    { value: 'dark', label: 'Temă Întunecată' }
  ];
  
  animationOptions = [
    { value: 'enabled', label: 'Activate' },
    { value: 'reduced', label: 'Reduse' },
    { value: 'disabled', label: 'Dezactivate' }
  ];

  constructor(
    private accessibilityService: AccessibilityService,
    private securityService: SecurityService,
    private renderer: Renderer2,
    public screenReaderService: ScreenReaderService,
    @Inject(DOCUMENT) private document: Document
  ) {}

  ngOnInit(): void {
    // NU forța dezactivarea dacă screen reader-ul este deja activ din activare manuală anterioară
    // Doar verifică și sincronizează starea la prima încărcare a aplicației
    this.initializeAudioContext();
    this.loadSettings();
    this.loadAccessibilityInfo();
    this.ensureVoicesLoaded();
    this.updateScreenReaderStatus();
    this.updateKeyboardTestStatus();
  }

  ngOnDestroy(): void {
    if (this.keyboardListener) {
      this.keyboardListener();
    }
    
    this.cleanupKeyboardTest();
  }

  private initializeAudioContext(): void {
    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (e) {
      console.log('Audio context not supported');
    }
  }

  private ensureVoicesLoaded(): void {
    if ('speechSynthesis' in window) {
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        console.log('Available voices:', voices.length);
      };
      
      window.speechSynthesis.onvoiceschanged = loadVoices;
      loadVoices();
    }
  }

  private updateScreenReaderStatus(): void {
    this.isScreenReaderActive = this.screenReaderService.isActive();
    this.screenReaderStatus = this.isScreenReaderActive ? 'Activ' : 'Dezactivat';
  }

  private updateKeyboardTestStatus(): void {
    this.keyboardTestStatus = this.isKeyboardTestActive ? 'Activ' : 'Inactiv';
  }

  loadSettings(): void {
    this.isLoading = true;
    this.error = '';
    
    this.accessibilityService.getSettings().subscribe({
      next: (settings) => {
        // Păstrează starea curentă a screen reader-ului dacă este deja activ
        const wasScreenReaderActive = this.screenReaderService.isActive();
        
        // Ensure required settings are always enabled, but preserve screen reader state
        this.settings = {
          ...settings,
          extended_time: true,
          extra_confirmations: true,
          // Păstrează starea actuală dacă screen reader-ul este activ manual
          screen_reader_support: wasScreenReaderActive || settings.screen_reader_support
        };
        
        this.applySettingsToInterface();
        this.isLoading = false;
        
        // NU activează automat screen reader-ul - păstrează starea curentă
        // Screen reader-ul rămâne în starea în care era (activ sau inactiv)
        
        this.securityService.logUserAction(
          'access_accessibility_settings',
          'accessibility',
          { settings_loaded: true, screen_reader_preserved: wasScreenReaderActive }
        );
      },
      error: (error) => {
        this.error = 'Eroare la încărcarea setărilor de accesibilitate: ' + 
                    (error.error?.message || error.message);
        this.isLoading = false;
        console.error('Accessibility settings error:', error);
      }
    });
  }

  loadAccessibilityInfo(): void {
    this.accessibilityService.getAccessibilityInfo().subscribe({
      next: (info) => {
        // Filter out unwanted features
        this.features = (info.accessibility_features || []).filter((feature: AccessibilityFeature) => 
          feature.title !== 'Interfață Simplificată' && 
          feature.title !== 'Verificare Facială Asistată'
        );
        this.contactInfo = info.contact_info || null;
      },
      error: (error) => {
        console.error('Error loading accessibility info:', error);
      }
    });
  }

  saveSettings(): void {
    this.isSaving = true;
    this.error = '';
    this.successMessage = '';
    
    this.accessibilityService.updateSettings(this.settings).subscribe({
      next: (response) => {
        this.successMessage = response.message || 'Setările au fost salvate cu succes!';
        this.settings = response.settings || this.settings;
        
        // Ensure required settings remain enabled, but don't force screen_reader_support
        this.settings.extended_time = true;
        this.settings.extra_confirmations = true;
        
        this.isSaving = false;
        
        localStorage.setItem('accessibility_settings', JSON.stringify(this.settings));
        
        this.announceToScreenReader('Setările de accesibilitate au fost salvate cu succes');
        this.playNotificationSound('success');
        
        this.securityService.logUserAction(
          'update_accessibility_settings',
          'accessibility',
          { settings: this.settings }
        );
        
        setTimeout(() => {
          this.successMessage = '';
        }, 3000);
      },
      error: (error) => {
        this.error = 'Eroare la salvarea setărilor: ' + 
                    (error.error?.error || error.error?.message || error.message);
        this.isSaving = false;
        this.playNotificationSound('error');
        console.error('Save settings error:', error);
      }
    });
  }

  onSettingChange(settingName: string, value: any): void {
    console.log(`Setting changed: ${settingName} = ${value}`);
    (this.settings as any)[settingName] = value;
    this.applySpecificSetting(settingName, value);
    
    // Simplified announcements for checkbox changes
    if (typeof value === 'boolean') {
      this.announceToScreenReader(value ? 'Casetă bifată' : 'Casetă debifată');
    } else {
      // For non-boolean values (select dropdowns)
      const announcement = `Setarea ${this.getSettingDisplayName(settingName)} a fost schimbată la ${value}`;
      this.announceToScreenReader(announcement);
    }
    
    // Handle special cases
    if (settingName === 'audio_assistance') {
      if (value) {
        // Auto-enable screen reader when audio assistance is enabled
        if (!this.isScreenReaderActive) {
          this.enableScreenReader();
          this.screenReaderAutoEnabled = true;
        }
      } else {
        // Auto-disable screen reader when audio assistance is disabled (only if it was auto-enabled)
        if (this.isScreenReaderActive && this.screenReaderAutoEnabled) {
          this.disableScreenReader();
          this.screenReaderAutoEnabled = false;
        }
      }
    }
    
    if (settingName === 'keyboard_navigation') {
      if (value) {
        // Auto-enable keyboard test when keyboard navigation is enabled
        if (!this.isKeyboardTestActive) {
          this.startKeyboardTest();
          this.keyboardTestAutoEnabled = true;
        }
      } else {
        // Auto-disable keyboard test when keyboard navigation is disabled (only if it was auto-enabled)
        if (this.isKeyboardTestActive && this.keyboardTestAutoEnabled) {
          this.stopKeyboardTest();
          this.keyboardTestAutoEnabled = false;
        }
      }
    }

    // Handle manual screen reader toggle via checkbox - ONLY manual activation allowed
    if (settingName === 'screen_reader_support') {
      if (value) {
        // Only enable if user explicitly checked the box
        if (!this.isScreenReaderActive) {
          this.enableScreenReader();
        }
      } else {
        // Only disable if it wasn't auto-enabled by audio assistance
        if (this.isScreenReaderActive && !this.screenReaderAutoEnabled) {
          this.disableScreenReader();
        }
      }
    }
  }

  private getSettingDisplayName(settingName: string): string {
    const names: {[key: string]: string} = {
      'font_size': 'mărimea fontului',
      'contrast_mode': 'modul de contrast',
      'animations': 'animațiile',
      'focus_highlights': 'evidențierea focus-ului',
      'extended_time': 'timpul extins',
      'simplified_interface': 'interfața simplificată',
      'audio_assistance': 'asistența audio',
      'keyboard_navigation': 'navigarea cu tastatura',
      'extra_confirmations': 'confirmările suplimentare',
      'large_buttons': 'butoanele mari',
      'screen_reader_support': 'suportul pentru cititor de ecran',
      'audio_notifications': 'notificările audio'
    };
    return names[settingName] || settingName;
  }

  enableScreenReader(): void {
    this.screenReaderService.enableGlobal();
    this.updateScreenReaderStatus();
    
    setTimeout(() => {
      this.screenReaderService.speak(
        'Cititor de ecran activat pe toată aplicația. Navigați cu mouse-ul peste elemente pentru a auzi descrierea lor.',
        'high'
      );
    }, 500);
  }

  disableScreenReader(): void {
    this.screenReaderService.disableGlobal();
    this.updateScreenReaderStatus();
  }

  toggleScreenReader(): void {
    if (this.isScreenReaderActive) {
      this.disableScreenReader();
      // Reset auto-enabled flag when manually disabled
      this.screenReaderAutoEnabled = false;
      // Update checkbox state
      this.settings.screen_reader_support = false;
    } else {
      this.enableScreenReader();
      // Don't set auto-enabled flag when manually enabled
      this.screenReaderAutoEnabled = false;
      // Update checkbox state
      this.settings.screen_reader_support = true;
    }
  }

  testScreenReader(): void {
    // Just test the voice without enabling/disabling the screen reader
    this.screenReaderService.speak('Aceasta este o propoziție pentru testarea cititorului de ecran', 'high');
    this.playNotificationSound('info');
  }

  startKeyboardTest(): void {
    if (!this.isKeyboardTestActive) {
      this.isKeyboardTestActive = true;
      this.updateKeyboardTestStatus();
      
      if (!this.isScreenReaderActive) {
        this.enableScreenReader();
      }
      
      this.screenReaderService.speak(
        'Test navigare cu tastatura activat! Elementele focusabile sunt evidențiate. Apăsați din nou butonul pentru a opri testul.',
        'high'
      );
      
      this.highlightFocusableElements();
      this.playNotificationSound('info');
    } else {
      this.stopKeyboardTest();
    }
  }

  stopKeyboardTest(): void {
    if (this.isKeyboardTestActive) {
      this.isKeyboardTestActive = false;
      this.updateKeyboardTestStatus();
      this.cleanupKeyboardTest();
      this.screenReaderService.speak('Test navigare cu tastatura oprit');
    }
  }

  toggleKeyboardTest(): void {
    if (this.isKeyboardTestActive) {
      this.stopKeyboardTest();
      // Reset auto-enabled flag when manually stopped
      this.keyboardTestAutoEnabled = false;
    } else {
      this.startKeyboardTest();
      // Don't set auto-enabled flag when manually started
      this.keyboardTestAutoEnabled = false;
    }
  }

  private cleanupKeyboardTest(): void {
    const enhancedElements = this.document.querySelectorAll('.accessibility-element-badge');
    enhancedElements.forEach(badge => {
      if (badge.parentElement) {
        this.renderer.removeChild(badge.parentElement, badge);
      }
    });
    
    const focusableElements = this.document.querySelectorAll('[data-keyboard-test-highlight]');
    focusableElements.forEach(element => {
      element.removeAttribute('data-keyboard-test-highlight');
      this.renderer.removeStyle(element, 'animation');
      this.renderer.removeStyle(element, 'border');
      this.renderer.removeStyle(element, 'background-color');
      this.renderer.removeStyle(element, 'box-shadow');
    });
  }

  private applySpecificSetting(settingName: string, value: any): void {
    const body = this.document.body;
    const html = this.document.documentElement;
    
    switch (settingName) {
      case 'font_size':
        this.applyFontSize(html, value);
        break;
        
      case 'contrast_mode':
        this.applyContrastMode(body, value);
        break;
        
      case 'animations':
        this.applyAnimationSettings(body, value);
        break;
        
      case 'focus_highlights':
        if (value) {
          this.renderer.addClass(body, 'accessibility-focus-highlights');
          this.enhanceFocusIndicators();
        } else {
          this.renderer.removeClass(body, 'accessibility-focus-highlights');
          this.removeFocusIndicators();
        }
        break;
        
      case 'large_buttons':
        if (value) {
          this.renderer.addClass(body, 'accessibility-large-buttons');
        } else {
          this.renderer.removeClass(body, 'accessibility-large-buttons');
        }
        break;
        
      case 'simplified_interface':
        if (value) {
          this.renderer.addClass(body, 'accessibility-simplified');
        } else {
          this.renderer.removeClass(body, 'accessibility-simplified');
        }
        break;
        
      case 'keyboard_navigation':
        if (value) {
          this.enableKeyboardNavigation();
          this.addSkipLinks();
          this.renderer.addClass(body, 'accessibility-keyboard-nav');
        } else {
          this.renderer.removeClass(body, 'accessibility-keyboard-nav');
        }
        break;
        
      case 'screen_reader_support':
        if (value) {
          this.enhanceScreenReaderSupport();
          this.renderer.addClass(body, 'accessibility-screen-reader');
        } else {
          this.renderer.removeClass(body, 'accessibility-screen-reader');
        }
        break;
    }
  }

  applySettingsToInterface(): void {
    const body = this.document.body;
    const html = this.document.documentElement;
    
    // Păstrează starea curentă a screen reader-ului
    const wasScreenReaderActive = this.screenReaderService.isActive();
    
    this.removeAllAccessibilityClasses(body);
    
    this.applyFontSize(html, this.settings.font_size);
    this.applyContrastMode(body, this.settings.contrast_mode);
    this.applyAnimationSettings(body, this.settings.animations);
    
    if (this.settings.focus_highlights) {
      this.renderer.addClass(body, 'accessibility-focus-highlights');
      this.enhanceFocusIndicators();
    }
    
    if (this.settings.large_buttons) {
      this.renderer.addClass(body, 'accessibility-large-buttons');
    }
    
    if (this.settings.simplified_interface) {
      this.renderer.addClass(body, 'accessibility-simplified');
    }
    
    if (this.settings.keyboard_navigation) {
      this.enableKeyboardNavigation();
      this.addSkipLinks();
      this.renderer.addClass(body, 'accessibility-keyboard-nav');
    }
    
    // Pentru screen reader support, păstrează starea activă dacă era deja activat
    if (this.settings.screen_reader_support || wasScreenReaderActive) {
      this.enhanceScreenReaderSupport();
      this.renderer.addClass(body, 'accessibility-screen-reader');
      // NU dezactiva screen reader-ul dacă era deja activ
    }
    
    console.log('Applied accessibility settings:', this.settings, 'Screen Reader preserved:', wasScreenReaderActive);
  }

  private removeAllAccessibilityClasses(element: Element): void {
    const classesToRemove = [
      'accessibility-font-small', 'accessibility-font-medium', 'accessibility-font-large', 'accessibility-font-extra-large',
      'accessibility-contrast-normal', 'accessibility-contrast-high', 'accessibility-contrast-dark',
      'accessibility-animations-enabled', 'accessibility-animations-reduced', 'accessibility-animations-disabled',
      'accessibility-focus-highlights', 'accessibility-large-buttons', 'accessibility-simplified',
      'accessibility-keyboard-nav', 'accessibility-screen-reader'
    ];
    
    classesToRemove.forEach(className => {
      this.renderer.removeClass(element, className);
    });
  }

  private applyFontSize(element: Element, fontSize: string): void {
    const sizes = {
      'small': '14px',
      'medium': '16px',
      'large': '18px',
      'extra_large': '22px'
    };
    
    const selectedSize = sizes[fontSize as keyof typeof sizes] || '16px';
    this.renderer.setStyle(element, 'font-size', selectedSize);
    this.renderer.addClass(this.document.body, `accessibility-font-${fontSize}`);
    console.log(`Applied font size: ${selectedSize}`);
  }

  private applyContrastMode(element: Element, contrastMode: string): void {
    // Remove existing contrast classes
    this.renderer.removeClass(element, 'accessibility-contrast-normal');
    this.renderer.removeClass(element, 'accessibility-contrast-high');
    this.renderer.removeClass(element, 'accessibility-contrast-dark');
    
    this.renderer.addClass(element, `accessibility-contrast-${contrastMode}`);
    
    if (contrastMode === 'high') {
      this.renderer.setStyle(element, 'filter', 'contrast(150%) brightness(110%)');
    } else if (contrastMode === 'dark') {
      this.renderer.setStyle(element, 'background-color', '#1a1a1a');
      this.renderer.setStyle(element, 'color', '#ffffff');
    } else {
      this.renderer.removeStyle(element, 'filter');
      this.renderer.removeStyle(element, 'background-color');
      this.renderer.removeStyle(element, 'color');
    }
    console.log(`Applied contrast mode: ${contrastMode}`);
  }

  private applyAnimationSettings(element: Element, animations: string): void {
    // Remove existing animation classes
    this.renderer.removeClass(element, 'accessibility-animations-enabled');
    this.renderer.removeClass(element, 'accessibility-animations-reduced');
    this.renderer.removeClass(element, 'accessibility-animations-disabled');
    
    this.renderer.addClass(element, `accessibility-animations-${animations}`);
    
    const existingStyles = this.document.querySelectorAll('style[data-accessibility-animations]');
    existingStyles.forEach(style => style.remove());
    
    if (animations === 'disabled') {
      const style = this.renderer.createElement('style');
      this.renderer.setAttribute(style, 'data-accessibility-animations', 'disabled');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }
      `;
      this.renderer.appendChild(this.document.head, style);
    } else if (animations === 'reduced') {
      const style = this.renderer.createElement('style');
      this.renderer.setAttribute(style, 'data-accessibility-animations', 'reduced');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0.1s !important;
          transition-duration: 0.1s !important;
        }
      `;
      this.renderer.appendChild(this.document.head, style);
    }
    console.log(`Applied animation settings: ${animations}`);
  }

  private enhanceFocusIndicators(): void {
    const existingStyles = this.document.querySelectorAll('style[data-accessibility-focus]');
    existingStyles.forEach(style => style.remove());
    
    const style = this.renderer.createElement('style');
    this.renderer.setAttribute(style, 'data-accessibility-focus', 'enhanced');
    style.textContent = `
      .accessibility-focus-highlights *:focus,
      .accessibility-focus-highlights *:focus-visible {
        outline: 3px solid #3498db !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.25) !important;
        border-radius: 4px !important;
        background-color: rgba(52, 152, 219, 0.1) !important;
        transform: scale(1.02) !important;
        transition: all 0.2s ease !important;
      }
    `;
    this.renderer.appendChild(this.document.head, style);
  }

  private removeFocusIndicators(): void {
    const existingStyles = this.document.querySelectorAll('style[data-accessibility-focus]');
    existingStyles.forEach(style => style.remove());
  }

  private enableKeyboardNavigation(): void {
    if (this.keyboardListener) {
      this.keyboardListener();
    }
    
    this.keyboardListener = this.renderer.listen('document', 'keydown', (event: KeyboardEvent) => {
      this.handleKeyboardNavigation(event);
    });
    
    const interactiveElements = this.document.querySelectorAll('button, input, select, textarea, a, [tabindex]');
    interactiveElements.forEach((element) => {
      if (!element.hasAttribute('tabindex')) {
        this.renderer.setAttribute(element, 'tabindex', '0');
      }
    });
  }

  private handleKeyboardNavigation(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      if (this.isKeyboardTestActive) {
        this.stopKeyboardTest();
        return;
      }
      this.screenReaderService.stopSpeaking();
    }
  }

  private addSkipLinks(): void {
    if (this.skipLinksAdded) return;
    
    const skipLinksContainer = this.renderer.createElement('div');
    this.renderer.addClass(skipLinksContainer, 'skip-links');
    this.renderer.setStyle(skipLinksContainer, 'position', 'fixed');
    this.renderer.setStyle(skipLinksContainer, 'top', '-100px');
    this.renderer.setStyle(skipLinksContainer, 'left', '0');
    this.renderer.setStyle(skipLinksContainer, 'z-index', '9999');
    this.renderer.setStyle(skipLinksContainer, 'background', '#000');
    this.renderer.setStyle(skipLinksContainer, 'color', '#fff');
    this.renderer.setStyle(skipLinksContainer, 'padding', '10px');
    
    const skipLinks = [
      { text: 'Salt la conținutul principal', target: 'main, .main-content' },
      { text: 'Salt la meniu', target: 'nav, .side-nav' },
      { text: 'Salt la footer', target: 'footer' }
    ];
    
    skipLinks.forEach(link => {
      const skipLink = this.renderer.createElement('a');
      this.renderer.setAttribute(skipLink, 'href', '#');
      this.renderer.setProperty(skipLink, 'textContent', link.text);
      this.renderer.setStyle(skipLink, 'color', '#fff');
      this.renderer.setStyle(skipLink, 'text-decoration', 'underline');
      this.renderer.setStyle(skipLink, 'margin-right', '15px');
      
      this.renderer.listen(skipLink, 'focus', () => {
        this.renderer.setStyle(skipLinksContainer, 'top', '0');
      });
      
      this.renderer.listen(skipLink, 'blur', () => {
        this.renderer.setStyle(skipLinksContainer, 'top', '-100px');
      });
      
      this.renderer.listen(skipLink, 'click', (event: Event) => {
        event.preventDefault();
        const target = this.document.querySelector(link.target);
        if (target) {
          (target as HTMLElement).focus();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
      
      this.renderer.appendChild(skipLinksContainer, skipLink);
    });
    
    this.renderer.insertBefore(this.document.body, skipLinksContainer, this.document.body.firstChild);
    this.skipLinksAdded = true;
  }

  private enhanceScreenReaderSupport(): void {
    const buttons = this.document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
    buttons.forEach(button => {
      const text = button.textContent?.trim();
      if (text) {
        this.renderer.setAttribute(button, 'aria-label', text);
      }
    });
    
    if (!this.document.querySelector('#accessibility-announcements')) {
      const liveRegion = this.renderer.createElement('div');
      this.renderer.setAttribute(liveRegion, 'id', 'accessibility-announcements');
      this.renderer.setAttribute(liveRegion, 'aria-live', 'polite');
      this.renderer.setAttribute(liveRegion, 'aria-atomic', 'true');
      this.renderer.addClass(liveRegion, 'sr-only');
      this.renderer.appendChild(this.document.body, liveRegion);
    }
  }

  private highlightFocusableElements(): void {
    const focusableElements = this.document.querySelectorAll('button, input, select, textarea, a, [tabindex]:not([tabindex="-1"])');
    
    focusableElements.forEach((element, index) => {
      this.renderer.setAttribute(element, 'data-keyboard-test-highlight', 'true');
      this.renderer.setStyle(element, 'animation', 'accessibility-highlight 3s ease-in-out infinite');
      this.renderer.setStyle(element, 'border', '3px solid #3498db');
      this.renderer.setStyle(element, 'background-color', 'rgba(52, 152, 219, 0.1)');
      this.renderer.setStyle(element, 'box-shadow', '0 0 15px rgba(52, 152, 219, 0.6)');
      
      const badge = this.renderer.createElement('span');
      this.renderer.setProperty(badge, 'textContent', (index + 1).toString());
      this.renderer.setStyle(badge, 'position', 'absolute');
      this.renderer.setStyle(badge, 'top', '-10px');
      this.renderer.setStyle(badge, 'right', '-10px');
      this.renderer.setStyle(badge, 'background-color', '#3498db');
      this.renderer.setStyle(badge, 'color', 'white');
      this.renderer.setStyle(badge, 'border-radius', '50%');
      this.renderer.setStyle(badge, 'width', '24px');
      this.renderer.setStyle(badge, 'height', '24px');
      this.renderer.setStyle(badge, 'display', 'flex');
      this.renderer.setStyle(badge, 'align-items', 'center');
      this.renderer.setStyle(badge, 'justify-content', 'center');
      this.renderer.setStyle(badge, 'font-size', '12px');
      this.renderer.setStyle(badge, 'font-weight', 'bold');
      this.renderer.setStyle(badge, 'z-index', '1000');
      this.renderer.addClass(badge, 'accessibility-element-badge');
      
      const currentPosition = window.getComputedStyle(element).position;
      if (currentPosition === 'static') {
        this.renderer.setStyle(element, 'position', 'relative');
      }
      
      this.renderer.appendChild(element, badge);
    });
  }

  announceToScreenReader(message: string): void {
    const announcement = this.renderer.createElement('div');
    this.renderer.setAttribute(announcement, 'aria-live', 'polite');
    this.renderer.setAttribute(announcement, 'aria-atomic', 'true');
    this.renderer.addClass(announcement, 'sr-only');
    this.renderer.setProperty(announcement, 'textContent', message);
    
    this.renderer.appendChild(this.document.body, announcement);
    
    setTimeout(() => {
      if (this.document.body.contains(announcement)) {
        this.renderer.removeChild(this.document.body, announcement);
      }
    }, 1000);
    
    if (this.isScreenReaderActive) {
      this.screenReaderService.speak(message, 'medium');
    }
  }

  private playNotificationSound(type: 'success' | 'error' | 'info'): void {
    if (!this.audioContext) return;
    
    try {
      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      const frequencies = {
        success: [523.25, 659.25, 783.99],
        error: [349.23, 293.66],
        info: [440, 554.37]
      };
      
      const freq = frequencies[type];
      oscillator.frequency.setValueAtTime(freq[0], this.audioContext.currentTime);
      
      if (freq.length > 1) {
        oscillator.frequency.setValueAtTime(freq[1], this.audioContext.currentTime + 0.1);
      }
      
      if (freq.length > 2) {
        oscillator.frequency.setValueAtTime(freq[2], this.audioContext.currentTime + 0.2);
      }
      
      gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
      
      oscillator.start(this.audioContext.currentTime);
      oscillator.stop(this.audioContext.currentTime + 0.3);
      
    } catch (e) {
      console.log('Audio notification failed:', e);
    }
  }

  openAccessibilityGuide(): void {
    const guideWindow = window.open('', '_blank', 'width=900,height=700,scrollbars=yes,resizable=yes');
    if (guideWindow) {
      guideWindow.document.write(`
        <html lang="ro">
          <head>
            <title>Ghid Complet de Accesibilitate</title>
            <meta charset="UTF-8">
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; background: #2c3e50; color: #fff; }
              h1, h2 { color: #3498db; }
              .feature { margin: 15px 0; padding: 20px; border-left: 4px solid #3498db; background-color: rgba(255,255,255,0.1); border-radius: 8px; }
              .contact { background-color: rgba(46, 204, 113, 0.2); padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #2ecc71; }
              .highlight { background-color: rgba(243, 156, 18, 0.2); padding: 15px; border-radius: 5px; border-left: 4px solid #f39c12; margin: 15px 0; }
            </style>
          </head>
          <body>
            <h1>🌟 Ghid Complet de Accesibilitate</h1>
            <h2>Aplicația de vot online cu AI - accesibilă tuturor utilizatorilor</h2>
            
            <div class="highlight">
              <strong>📋 Rezumat rapid:</strong> Această aplicație oferă suport complet pentru utilizatorii cu dizabilități prin funcții avansate de accesibilitate, inclusiv un cititor de ecran intern.
            </div>
            
            <div class="feature">
              <h3>🔊 Suport pentru Cititori de Ecran</h3>
              <p><strong>Compatibil cu aplicații de screen reader profesionale:</strong> JAWS, NVDA, VoiceOver și TalkBack.</p>
              <p><strong>Screen Reader Intern:</strong> Aplicația include propriul cititor de ecran care funcționează în română și poate fi activat din setările de accesibilitate.</p>
            </div>
            
            <div class="feature">
              <h3>⌨️ Navigarea cu Tastatura</h3>
              <p><strong>Comenzi disponibile:</strong></p>
              <ul>
                <li><strong>Tab</strong> - Navigează la următorul element</li>
                <li><strong>Shift + Tab</strong> - Navigează la elementul anterior</li>
                <li><strong>Enter / Spațiu</strong> - Activează butoanele</li>
                <li><strong>Escape</strong> - Oprește vocea sau închide ferestre</li>
              </ul>
            </div>
            
            <div class="feature">
              <h3>👁️ Opțiuni Vizuale</h3>
              <ul>
                <li><strong>Contrast Ridicat:</strong> Îmbunătățește vizibilitatea</li>
                <li><strong>Tema Întunecată:</strong> Reduce oboseala ochilor</li>
                <li><strong>Font Variabil:</strong> De la 14px la 22px</li>
                <li><strong>Butoane Mari:</strong> Dimensiuni mărite</li>
                <li><strong>Control Animații:</strong> Dezactivare sau reducere</li>
              </ul>
            </div>
            
            <div class="feature">
              <h3>🗳️ Asistență pentru Vot</h3>
              <ul>
                <li><strong>Timp Extins:</strong> Timp suplimentar pentru vot (activat automat)</li>
                <li><strong>Confirmări Multiple:</strong> Verificări suplimentare (activat automat)</li>
                <li><strong>Asistență Audio:</strong> Ghidare vocală pas cu pas</li>
                <li><strong>Navigare Simplificată:</strong> Interfață optimizată</li>
              </ul>
            </div>
            
            <div class="contact">
              <h3>📞 Contact pentru Asistență Accesibilitate</h3>
              <p><strong>Pentru asistență specializată:</strong></p>
              <ul>
                <li><strong>📧 Email:</strong> g.brujbeanu18@gmail.com</li>
                <li><strong>📱 Telefon:</strong> +40 723 452 871</li>
                <li><strong>🕐 Program:</strong> Luni-Vineri: 9:00 - 17:00</li>
              </ul>
            </div>
          </body>
        </html>
      `);
      guideWindow.focus();
    }
  }

  resetToDefaults(): void {
    if (confirm('Sunteți sigur că doriți să resetați setările modificabile la valorile implicite?')) {
      // Forțează dezactivarea cititorului de ecran mai întâi
      if (this.isScreenReaderActive) {
        this.disableScreenReader();
      }
      
      this.settings = {
        font_size: 'medium',
        contrast_mode: 'normal',
        animations: 'enabled',
        focus_highlights: false,
        extended_time: true, // Mențineți activat
        simplified_interface: false,
        audio_assistance: false,
        keyboard_navigation: false,
        extra_confirmations: true, // Mențineți activat
        large_buttons: false,
        screen_reader_support: false, // Pornire întotdeauna dezactivată - doar activare manuală
        audio_notifications: false
      };
      
      // reseteaza auto-enabled flags
      this.screenReaderAutoEnabled = false;
      this.keyboardTestAutoEnabled = false;
      
      this.applySettingsToInterface();
      this.saveSettings();
    }
  }

  previewSetting(settingType: string, value: any): void {
    if (settingType === 'font_size') {
      this.applyFontSize(this.document.documentElement, value);
    } else if (settingType === 'contrast_mode') {
      this.applyContrastMode(this.document.body, value);
    } else if (settingType === 'animations') {
      this.applyAnimationSettings(this.document.body, value);
    }
    
    this.announceToScreenReader(`Previzualizare: ${settingType} schimbat la ${value}`);
  }

  resetPreview(): void {
    this.applySettingsToInterface();
  }
}