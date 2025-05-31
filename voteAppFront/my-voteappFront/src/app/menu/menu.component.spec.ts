import { ComponentFixture, TestBed, fakeAsync, tick, flush, discardPeriodicTasks } from '@angular/core/testing';
import { Router, ActivatedRoute } from '@angular/router';
import { of, Subject, NEVER } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

import { MenuComponent } from './menu.component';
import { AuthService } from '../services/auth.service';
import { AuthUserService } from '../services/auth-user.service';
import { MapService } from '../services/map.service';
import { VoteSettingsService } from '../services/vote-settings.service';
import { SecurityService } from '../services/security.service';

describe('MenuComponent', () => {
  let component: MenuComponent;
  let fixture: ComponentFixture<MenuComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let authUserServiceSpy: jasmine.SpyObj<AuthUserService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let mapServiceSpy: jasmine.SpyObj<MapService>;
  let voteSettingsServiceSpy: jasmine.SpyObj<VoteSettingsService>;
  let securityServiceSpy: jasmine.SpyObj<SecurityService>;

  const mockActivatedRoute = {
    queryParams: of({}),
    snapshot: {
      queryParams: {}
    }
  };

  // Mock localStorage complet
  const mockLocalStorage = {
    store: {} as { [key: string]: string },
    getItem: jasmine.createSpy('getItem').and.callFake((key: string) => mockLocalStorage.store[key] || null),
    setItem: jasmine.createSpy('setItem').and.callFake((key: string, value: string) => mockLocalStorage.store[key] = value),
    removeItem: jasmine.createSpy('removeItem').and.callFake((key: string) => delete mockLocalStorage.store[key]),
    clear: jasmine.createSpy('clear').and.callFake(() => mockLocalStorage.store = {}),
    length: 0,
    key: jasmine.createSpy('key')
  };

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', ['logout', 'isAuthenticated']);
    const authUserSpy = jasmine.createSpyObj('AuthUserService', ['getUserProfile']);
    const routerSpyObj = jasmine.createSpyObj('Router', ['navigate'], { url: '/menu' });
    const mapSpy = jasmine.createSpyObj('MapService', ['setCurrentRound']);
    const voteSettingsSpy = jasmine.createSpyObj('VoteSettingsService', ['getVoteSettings']);
    const securitySpy = jasmine.createSpyObj('SecurityService', ['logUserAction']);

    await TestBed.configureTestingModule({
      declarations: [MenuComponent],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: AuthUserService, useValue: authUserSpy },
        { provide: Router, useValue: routerSpyObj },
        { provide: ActivatedRoute, useValue: mockActivatedRoute },
        { provide: MapService, useValue: mapSpy },
        { provide: VoteSettingsService, useValue: voteSettingsSpy },
        { provide: SecurityService, useValue: securitySpy }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(MenuComponent);
    component = fixture.componentInstance;
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    authUserServiceSpy = TestBed.inject(AuthUserService) as jasmine.SpyObj<AuthUserService>;
    routerSpy = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    mapServiceSpy = TestBed.inject(MapService) as jasmine.SpyObj<MapService>;
    voteSettingsServiceSpy = TestBed.inject(VoteSettingsService) as jasmine.SpyObj<VoteSettingsService>;
    securityServiceSpy = TestBed.inject(SecurityService) as jasmine.SpyObj<SecurityService>;

    // Mock localStorage global
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true
    });

    // Setup default mocks
    authServiceSpy.isAuthenticated.and.returnValue(true);
    authUserServiceSpy.getUserProfile.and.returnValue(of({
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      is_active: true
    }));
    voteSettingsServiceSpy.getVoteSettings.and.returnValue(of({
      is_vote_active: false,
      vote_type: null,
      remaining_time: 0
    }));
  });

  beforeEach(() => {
    // Reset localStorage mock store
    mockLocalStorage.store = {
      'access_token': 'mock-token',
      'auth_method': 'email',
      'user_data': JSON.stringify({
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User'
      })
    };

    // Reset all spy calls
    mockLocalStorage.getItem.calls.reset();
    mockLocalStorage.setItem.calls.reset();
    mockLocalStorage.removeItem.calls.reset();
    mockLocalStorage.clear.calls.reset();

    // Nu inițializăm componenta aici - o facem în fiecare test separat
  });

  afterEach(() => {
    // Cleanup timers și subscriptions
    try {
      if (component && component.voteSettingsInterval) {
        component.voteSettingsInterval.unsubscribe();
      }
      
      // Cleanup periodic tasks if any
      discardPeriodicTasks();
    } catch (e) {
      // Ignoră erorile de cleanup
    }
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    fixture.detectChanges();
    expect(component.currentView).toBe('prezenta');
    expect(component.locationFilter).toBe('romania');
    expect(component.isVoteActive).toBeFalse();
    expect(component.availableRounds).toBeDefined();
    expect(component.availableRounds.length).toBeGreaterThan(0);
  });

  describe('Authentication Status', () => {
    it('should check if user is authenticated', () => {
      fixture.detectChanges();
      
      // Act
      const isAuth = component.isAuthenticated();

      // Assert
      expect(authServiceSpy.isAuthenticated).toHaveBeenCalled();
      expect(isAuth).toBeTrue();
    });
  });

  describe('Navigation Functions', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should navigate to different menu sections', () => {
      // Test navigation to statistics
      component.navigateTo('statistici');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/statistici'], jasmine.any(Object));
      expect(component.currentView).toBe('statistici');

      // Test navigation to map
      component.navigateTo('harta');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/harta'], jasmine.any(Object));
      expect(component.currentView).toBe('harta');

      // Test navigation to results
      component.navigateTo('rezultate');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/rezultate'], jasmine.any(Object));
      expect(component.currentView).toBe('rezultate');
    });

    it('should navigate to candidates section', () => {
      component.navigateTo('candidati_prezidentiali');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/candidati_prezidentiali'], jasmine.any(Object));
      expect(component.currentView).toBe('candidati_prezidentiali');
    });

    it('should navigate to about sections', () => {
      component.navigateTo('concept');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/despre/concept']);
      expect(component.currentView).toBe('concept');

      component.navigateTo('misiune');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/despre/misiune']);
      expect(component.currentView).toBe('misiune');
    });

    it('should navigate to advanced settings', () => {
      component.navigateTo('setari-cont');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/setari-cont']);
      expect(component.currentView).toBe('setari-cont');

      component.navigateTo('securitate');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/securitate']);
      expect(component.currentView).toBe('securitate');

      component.navigateTo('accesibilitate');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['menu/accesibilitate']);
      expect(component.currentView).toBe('accesibilitate');
    });

    it('should log navigation actions', () => {
      component.navigateTo('statistici');
      expect(securityServiceSpy.logUserAction).toHaveBeenCalledWith(
        'navigate',
        'statistici',
        jasmine.any(Object)
      );
    });
  });

  describe('Vote Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should handle active vote navigation', () => {
      // Arrange
      component.isVoteActive = true;
      component.activeVoteType = 'prezidentiale';

      // Act
      component.navigateToVote();

      // Assert
      expect(routerSpy.navigate).toHaveBeenCalledWith(['vot/prezidentiale'], jasmine.any(Object));
    });

    it('should handle inactive vote navigation', () => {
      // Arrange
      component.isVoteActive = false;
      spyOn(window, 'alert');

      // Act
      component.navigateToVote();

      // Assert
      expect(window.alert).toHaveBeenCalled();
      expect(routerSpy.navigate).not.toHaveBeenCalled();
    });

    it('should format remaining time correctly', () => {
      expect(component.formatRemainingTime(3661)).toBe('01:01:01');
      expect(component.formatRemainingTime(0)).toBe('00:00:00');
      expect(component.formatRemainingTime(3600)).toBe('01:00:00');
    });

    it('should get vote type text correctly', () => {
      expect(component.getVoteTypeText('prezidentiale')).toBe('Alegeri Prezidențiale');
      expect(component.getVoteTypeText('parlamentare')).toBe('Alegeri Parlamentare');
      expect(component.getVoteTypeText('locale')).toBe('Alegeri Locale');
      expect(component.getVoteTypeText(null)).toBe('Necunoscut');
    });
  });

  describe('Round Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should switch election rounds', () => {
      // Arrange
      const newRound = {
        id: 'tur2_2024',
        name: 'Tur 2 Alegeri Prezidențiale 2024',
        date: new Date('2024-12-22'),
        active: false,
        hasData: false
      };

      // Act
      component.switchRound(newRound);

      // Assert
      expect(component.currentRound).toBe(newRound);
      expect(component.electionDate).toBe(newRound.date);
      expect(component.isDropdownOpen).toBeFalse();
      expect(mapServiceSpy.setCurrentRound).toHaveBeenCalledWith('tur2_2024', false);
    });

    it('should toggle dropdown', () => {
      // Arrange
      expect(component.isDropdownOpen).toBeFalse();

      // Act
      component.toggleDropdown();

      // Assert
      expect(component.isDropdownOpen).toBeTrue();

      // Act again
      component.toggleDropdown();

      // Assert
      expect(component.isDropdownOpen).toBeFalse();
    });
  });

  describe('Location Switching', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should switch between Romania and Strainatate', () => {
      // Test switch to Strainatate
      component.switchLocation('strainatate');
      expect(component.locationFilter).toBe('strainatate');

      // Test switch back to Romania
      component.switchLocation('romania');
      expect(component.locationFilter).toBe('romania');
    });

    it('should update navigation with location parameters when on map page', () => {
      // Arrange
      Object.defineProperty(routerSpy, 'url', {
        get: () => 'menu/harta',
        configurable: true
      });

      // Act
      component.switchLocation('strainatate');

      // Assert
      expect(component.locationFilter).toBe('strainatate');
      expect(routerSpy.navigate).toHaveBeenCalled();
    });
  });

  describe('User Data Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should mask CNP for privacy', () => {
      const cnp = '1234567890123';
      const maskedCnp = component.maskCNP(cnp);
      expect(maskedCnp).toBe('123********23');
    });

    it('should handle empty CNP masking', () => {
      expect(component.maskCNP('')).toBe('');
      expect(component.maskCNP(null as any)).toBe('');
    });
  });

  describe('Logout Functionality', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call logout service', () => {
      // Act
      component.logout();

      // Assert
      expect(authServiceSpy.logout).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle navigation to unknown view', () => {
      // Arrange
      fixture.detectChanges();

      // Act
      component.navigateTo('unknown-view');

      // Assert
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/unknown-view']);
    });
  });

  describe('Vote Type Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should handle different vote types correctly', () => {
      // Test presidential vote
      component.isVoteActive = true;
      component.activeVoteType = 'prezidentiale';
      component.navigateToVote();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['vot/prezidentiale'], jasmine.any(Object));

      // Test parliamentary vote
      component.activeVoteType = 'parlamentare';
      component.navigateToVote();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['vot/parlamentare'], jasmine.any(Object));

      // Test local vote
      component.activeVoteType = 'locale';
      component.navigateToVote();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['vot/locale'], jasmine.any(Object));
    });

    it('should handle upcoming votes', () => {
      // Arrange
      component.isVoteActive = false;
      component.upcomingVoteType = 'prezidentiale';
      spyOn(window, 'alert');

      // Act
      component.navigateToVote();

      // Assert
      expect(window.alert).toHaveBeenCalled();
    });
  });

  describe('Round Navigation', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should handle round switching with navigation updates', () => {
      // Arrange
      const newRound = {
        id: 'tur_activ',
        name: 'Tur Activ',
        date: new Date(),
        active: true,
        hasData: false
      };

      Object.defineProperty(routerSpy, 'url', {
        get: () => 'menu/statistici',
        configurable: true
      });

      // Act
      component.switchRound(newRound);

      // Assert
      expect(component.currentRound.id).toBe('tur_activ');
      expect(mapServiceSpy.setCurrentRound).toHaveBeenCalledWith('tur_activ', false);
    });
  });
});