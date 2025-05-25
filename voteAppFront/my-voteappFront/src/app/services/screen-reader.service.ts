import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ScreenReaderService {
  private isEnabled = false; // Pornește întotdeauna dezactivat
  private isGloballyEnabled = false; // Pornește întotdeauna dezactivat
  private synthesis: SpeechSynthesis | null = null;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private voice: SpeechSynthesisVoice | null = null;
  private voicesLoaded = false;
  private globalEventListeners: Array<() => void> = [];
  private lastSpokenText = '';
  private lastSpokenTime = 0;

  constructor() {
    // Doar inițializează synthesis, NU activa nimic automat
    this.initializeSynthesis();
    
    // Asigură-te explicit că service-ul pornește complet dezactivat
    this.forceDisable();
  }

  private forceDisable(): void {
    this.isEnabled = false;
    this.isGloballyEnabled = false;
    this.stopSpeaking();
    this.removeGlobalEventListeners();
  }

  private initializeSynthesis(): void {
    if ('speechSynthesis' in window) {
      this.synthesis = window.speechSynthesis;
      this.loadVoices();
      
      window.speechSynthesis.onvoiceschanged = () => {
        this.loadVoices();
      };
      
      setTimeout(() => {
        if (!this.voicesLoaded) {
          this.loadVoices();
        }
      }, 1000);
    }
  }

  private loadVoices(): void {
    if (!this.synthesis) return;
    
    const voices = this.synthesis.getVoices();
    
    let selectedVoice = null;
    
    // Prioritate pentru română locală
    selectedVoice = voices.find(voice => 
      voice.lang.toLowerCase() === 'ro-ro' && voice.localService
    );
    
    if (!selectedVoice) {
      selectedVoice = voices.find(voice => 
        voice.lang.toLowerCase().startsWith('ro') && voice.localService
      );
    }
    
    if (!selectedVoice) {
      selectedVoice = voices.find(voice => 
        voice.lang.toLowerCase().startsWith('ro')
      );
    }
    
    if (!selectedVoice) {
      selectedVoice = voices.find(voice => 
        voice.name.toLowerCase().includes('romanian') ||
        voice.name.toLowerCase().includes('romania')
      );
    }
    
    // Fallback pentru alte limbi europene
    if (!selectedVoice) {
      selectedVoice = voices.find(voice => 
        voice.lang.toLowerCase().startsWith('en-gb') ||
        voice.lang.toLowerCase().startsWith('en-ie') ||
        voice.lang.toLowerCase().startsWith('de') ||
        voice.lang.toLowerCase().startsWith('it') ||
        voice.lang.toLowerCase().startsWith('fr')
      );
    }
    
    if (!selectedVoice) {
      selectedVoice = voices.find(voice => 
        voice.lang.toLowerCase().startsWith('en')
      );
    }
    
    if (!selectedVoice && voices.length > 0) {
      selectedVoice = voices[0];
    }
    
    this.voice = selectedVoice ?? null;
    this.voicesLoaded = true;
    
    if (this.voice) {
      console.log(`Voce încărcată pentru română: ${this.voice.name} (${this.voice.lang}) - Screen Reader DEZACTIVAT implicit`);
    }
  }

  enableGlobal(): void {
    this.isGloballyEnabled = true;
    this.isEnabled = true;
    this.loadVoices();
    console.log('Screen Reader: Activat manual de utilizator');
    this.speak('Cititorul de ecran a fost activat pe toată aplicația.');
    this.addGlobalEventListeners();
    this.refreshPageElements();
  }

  disableGlobal(): void {
    this.isGloballyEnabled = false;
    this.isEnabled = false;
    this.stopSpeaking();
    this.removeGlobalEventListeners();
    console.log('Screen Reader: Dezactivat manual de utilizator');
    // Nu vorbește când se dezactivează pentru a evita confuzia
  }

  enable(): void {
    if (!this.isGloballyEnabled) {
      this.isEnabled = true;
      this.loadVoices();
      console.log('Screen Reader: Activat pentru această pagină');
      this.speak('Cititorul de ecran a fost activat pentru această pagină.');
      this.addGlobalEventListeners();
    }
  }

  disable(): void {
    if (!this.isGloballyEnabled) {
      this.isEnabled = false;
      this.stopSpeaking();
      this.removeGlobalEventListeners();
      console.log('Screen Reader: Dezactivat pentru această pagină');
    }
  }

  toggle(): boolean {
    if (this.isGloballyEnabled) {
      this.disableGlobal();
    } else {
      this.enableGlobal();
    }
    return this.isEnabled;
  }

  refreshPageElements(): void {
    if (!this.isEnabled) return;
    
    setTimeout(() => {
      this.addHoverListenersToNewElements();
      this.enhanceNewElements();
    }, 300);
  }

  private addHoverListenersToNewElements(): void {
    const interactiveElements = document.querySelectorAll(
      'button, input, select, textarea, a, [role="button"], [role="link"], ' +
      '.clickable, .hoverable, .btn, .nav-link, .menu-item, .vote-button, ' +
      '.candidate-card, .sidebar-link, .nav-item, [tabindex]:not([tabindex="-1"])'
    );

    interactiveElements.forEach((element) => {
      if (!element.hasAttribute('data-screen-reader-enhanced')) {
        element.setAttribute('data-screen-reader-enhanced', 'true');
        
        const mouseEnterHandler = (event: Event) => {
          if (this.isEnabled) {
            this.readElementOnHover(event.target as HTMLElement);
          }
        };

        const clickHandler = (event: Event) => {
          if (this.isEnabled) {
            this.handleElementClick(event.target as HTMLElement);
          }
        };

        element.addEventListener('mouseenter', mouseEnterHandler);
        element.addEventListener('click', clickHandler);
        
        this.globalEventListeners.push(() => {
          element.removeEventListener('mouseenter', mouseEnterHandler);
          element.removeEventListener('click', clickHandler);
        });
      }
    });
  }

  private enhanceNewElements(): void {
    const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
    buttons.forEach(button => {
      const text = button.textContent?.trim();
      if (text && !button.hasAttribute('data-aria-enhanced')) {
        button.setAttribute('aria-label', text);
        button.setAttribute('data-aria-enhanced', 'true');
      }
    });

    const links = document.querySelectorAll('a:not([aria-label])');
    links.forEach(link => {
      const text = link.textContent?.trim();
      const href = link.getAttribute('href');
      if (!text && href && !link.hasAttribute('data-aria-enhanced')) {
        link.setAttribute('aria-label', `Link către ${href}`);
        link.setAttribute('data-aria-enhanced', 'true');
      }
    });
  }

  private readElementOnHover(element: HTMLElement): void {
    if (!this.isEnabled) return;

    const description = this.getElementDescription(element);
    
    if (description) {
      const now = Date.now();
      if (description !== this.lastSpokenText || (now - this.lastSpokenTime) > 2000) {
        this.speak(description, 'medium');
        this.lastSpokenText = description;
        this.lastSpokenTime = now;
      }
    }
  }

  private handleElementClick(element: HTMLElement): void {
    if (!this.isEnabled) return;
    
    // Sări peste citirea dacă este un element badge din testul de tastatură
    if (element.classList.contains('accessibility-element-badge')) {
      return;
    }
    
    // Sări peste citirea dacă se face clic pe un element care conține doar elemente badge
    if (this.isOnlyBadgeContent(element)) {
      return;
    }
    
    const action = this.getActionDescription(element);
    
    if (action) {
      this.speak(action, 'high');
    }
  }

  private isOnlyBadgeContent(element: HTMLElement): boolean {
    // Verifică dacă elementul conține doar numere de badge-uri
    const textContent = element.textContent?.trim() || '';
    
    // Dacă textul este doar numere și elementul are copii badge-uri, sări peste el
    if (/^\d+$/.test(textContent)) {
      const badges = element.querySelectorAll('.accessibility-element-badge');
      if (badges.length > 0) {
        return true;
      }
    }
    
    return false;
  }

  speak(text: string, priority: 'low' | 'medium' | 'high' = 'medium'): void {
    // Vorbește doar dacă este activat explicit
    if (!this.isEnabled || !this.synthesis || !text.trim()) return;

    if (!this.voicesLoaded || !this.voice) {
      this.loadVoices();
    }

    if (priority === 'high') {
      this.stopSpeaking();
    }

    if (priority === 'medium' && this.synthesis.speaking) {
      this.synthesis.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    
    if (this.voice) {
      utterance.voice = this.voice;
    }
    
    if (this.voice?.lang.toLowerCase().startsWith('ro')) {
      utterance.rate = 0.85;
      utterance.pitch = 1.0;
      utterance.volume = 0.9;
    } else {
      utterance.rate = 0.75;
      utterance.pitch = 1.0;
      utterance.volume = 0.9;
    }
    
    utterance.lang = 'ro-RO';

    utterance.onstart = () => {
      this.currentUtterance = utterance;
    };

    utterance.onend = () => {
      this.currentUtterance = null;
    };

    utterance.onerror = (event) => {
      console.error('Eroare speech:', event.error);
      this.currentUtterance = null;
    };

    this.synthesis.speak(utterance);
  }

  stopSpeaking(): void {
    if (this.synthesis) {
      this.synthesis.cancel();
      this.currentUtterance = null;
    }
  }

  private addGlobalEventListeners(): void {
    const focusHandler = (event: FocusEvent) => {
      if (this.isEnabled) {
        this.handleGlobalFocus(event);
      }
    };

    const changeHandler = (event: Event) => {
      if (this.isEnabled) {
        this.handleGlobalChange(event);
      }
    };

    const keydownHandler = (event: KeyboardEvent) => {
      if (this.isEnabled) {
        this.handleGlobalKeydown(event);
      }
    };

    document.addEventListener('focusin', focusHandler);
    document.addEventListener('change', changeHandler);
    document.addEventListener('keydown', keydownHandler);
    
    this.globalEventListeners.push(() => {
      document.removeEventListener('focusin', focusHandler);
      document.removeEventListener('change', changeHandler);
      document.removeEventListener('keydown', keydownHandler);
    });

    this.addHoverListenersToNewElements();
  }

  private removeGlobalEventListeners(): void {
    this.globalEventListeners.forEach(removeListener => removeListener());
    this.globalEventListeners = [];
    
    const enhancedElements = document.querySelectorAll('[data-screen-reader-enhanced]');
    enhancedElements.forEach(element => {
      element.removeAttribute('data-screen-reader-enhanced');
    });
  }

  private handleGlobalFocus(event: FocusEvent): void {
    const element = event.target as HTMLElement;
    
    // Sări peste citirea focus pentru elementele badge
    if (element.classList.contains('accessibility-element-badge')) {
      return;
    }
    
    const description = this.getElementDescription(element);
    
    if (description) {
      this.speak(description, 'medium');
    }
  }

  private handleGlobalChange(event: Event): void {
    const element = event.target as HTMLElement;
    const change = this.getChangeDescription(element);
    
    if (change) {
      this.speak(change, 'high');
    }
  }

  private handleGlobalKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      this.stopSpeaking();
      this.speak('Vorbirea a fost oprită');
      return;
    }
  }

  cleanup(): void {
    this.stopSpeaking();
    this.removeGlobalEventListeners();
    this.isEnabled = false;
    this.isGloballyEnabled = false;
    console.log('Screen Reader: Curățat și dezactivat');
  }

  private getElementDescription(element: HTMLElement): string {
    if (!element) return '';

    // Sări peste elementele badge complet
    if (element.classList.contains('accessibility-element-badge')) {
      return '';
    }

    const tagName = element.tagName.toLowerCase();
    const type = element.getAttribute('type');
    const ariaLabel = element.getAttribute('aria-label');
    const title = element.getAttribute('title');
    const placeholder = element.getAttribute('placeholder');
    
    let text = ariaLabel || element.textContent?.trim() || title || '';
    
    if (text) {
      text = text.replace(/\s+/g, ' ').trim();
      
      // Dacă textul este doar numere și elementul are badge-uri, sări peste el
      if (/^\d+$/.test(text) && element.querySelector('.accessibility-element-badge')) {
        return '';
      }
      
      if (text.length > 150) {
        text = text.substring(0, 150) + '...';
      }
    }
    
    let description = '';
    
    switch (tagName) {
      case 'button':
        description = `Buton: ${text}`;
        if (element.hasAttribute('disabled')) {
          description += ' dezactivat';
        }
        break;
        
      case 'input':
        switch (type) {
          case 'text':
            const value = (element as HTMLInputElement).value;
            description = `Câmp de text: ${text || placeholder || 'fără etichetă'}`;
            if (value) {
              description += `, conține: ${value}`;
            }
            break;
          case 'email':
            description = `Câmp pentru email: ${text || placeholder || 'fără etichetă'}`;
            break;
          case 'password':
            description = `Câmp pentru parolă: ${text || placeholder || 'fără etichetă'}`;
            break;
          case 'checkbox':
            const checked = (element as HTMLInputElement).checked;
            description = `Casetă de bifat: ${text}, ${checked ? 'bifată' : 'nebifată'}`;
            break;
          case 'radio':
            const selected = (element as HTMLInputElement).checked;
            description = `Opțiune: ${text}, ${selected ? 'selectată' : 'neselectată'}`;
            break;
          case 'submit':
            description = `Buton pentru trimitere: ${text || 'Trimite'}`;
            break;
          default:
            description = `Câmp ${type}: ${text}`;
        }
        break;
        
      case 'select':
        const select = element as HTMLSelectElement;
        const selectedOption = select.options[select.selectedIndex];
        description = `Lista de selecție: ${text || 'fără etichetă'}`;
        if (selectedOption) {
          description += `, selectat: ${selectedOption.textContent}`;
        }
        break;
        
      case 'a':
        const href = element.getAttribute('href');
        description = `Link: ${text}`;
        if (href && href !== '#') {
          if (href.startsWith('mailto:')) {
            description += `, pentru email`;
          } else if (href.startsWith('tel:')) {
            description += `, pentru apeluri`;
          }
        }
        break;
        
      case 'h1': case 'h2': case 'h3': case 'h4': case 'h5': case 'h6':
        description = `Titlu nivel ${tagName.charAt(1)}: ${text}`;
        break;
        
      case 'nav':
        description = `Navigare: ${text || 'meniu'}`;
        break;
        
      case 'div':
      case 'span':
        const role = element.getAttribute('role');
        if (role === 'button') {
          description = `Buton: ${text}`;
        } else if (role === 'link') {
          description = `Link: ${text}`;
        } else if (text && element.classList.contains('menu-item')) {
          description = `Element de meniu: ${text}`;
        } else if (text && (element.classList.contains('clickable') || element.hasAttribute('onclick'))) {
          description = `Element clickabil: ${text}`;
        } else if (text) {
          description = text;
        }
        break;
        
      default:
        if (text) {
          description = text;
        }
    }

    if (element.hasAttribute('disabled')) {
      description += ', dezactivat';
    }

    return description;
  }

  private getActionDescription(element: HTMLElement): string {
    const tagName = element.tagName.toLowerCase();
    const type = element.getAttribute('type');
    const text = element.textContent?.trim() || element.getAttribute('aria-label') || '';

    // Sări peste elementele badge
    if (element.classList.contains('accessibility-element-badge')) {
      return '';
    }

    // Sări peste dacă textul este doar numere și elementul are badge-uri
    if (/^\d+$/.test(text) && element.querySelector('.accessibility-element-badge')) {
      return '';
    }

    switch (tagName) {
      case 'button':
        return `Ați apăsat: ${text}`;
      case 'input':
        if (type === 'checkbox') {
          const checked = (element as HTMLInputElement).checked;
          return `Casetă ${checked ? 'bifată' : 'debifată'}`;
        }
        if (type === 'submit') {
          return 'Formular trimis';
        }
        break;
      case 'a':
        return `Navigați la: ${text}`;
      case 'div':
      case 'span':
        if (element.getAttribute('role') === 'button' || element.classList.contains('clickable')) {
          return `Ați selectat: ${text}`;
        }
        break;
    }
    
    return '';
  }

  private getChangeDescription(element: HTMLElement): string {
    const tagName = element.tagName.toLowerCase();
    const text = element.textContent?.trim() || element.getAttribute('aria-label') || '';

    switch (tagName) {
      case 'select':
        const select = element as HTMLSelectElement;
        const selectedOption = select.options[select.selectedIndex];
        return `Selectat: ${selectedOption?.textContent}`;
      case 'input':
        const input = element as HTMLInputElement;
        if (input.type === 'checkbox') {
          return `Casetă ${input.checked ? 'bifată' : 'debifată'}`;
        }
        if (input.type === 'radio') {
          return `Selectat: ${text}`;
        }
        break;
    }
    
    return '';
  }

  isActive(): boolean {
    return this.isEnabled;
  }

  isGloballyActive(): boolean {
    return this.isGloballyEnabled;
  }

  isSpeaking(): boolean {
    return this.synthesis ? this.synthesis.speaking : false;
  }

  getStatus(): string {
    if (this.isGloballyEnabled) {
      return 'Activ Global';
    } else if (this.isEnabled) {
      return 'Activ Local';
    } else {
      return 'Dezactivat';
    }
  }
}