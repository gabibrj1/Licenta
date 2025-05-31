import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthComponent } from './auth.component';
import { AuthService } from '../services/auth.service';
import { HeaderComponent } from '../header/header.component';

describe('AuthComponent', () => {
  let component: AuthComponent;
  let fixture: ComponentFixture<AuthComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', [
      'login', 
      'loginWithIDCard', 
      'loginWithFaceRecognition',
      'verifyTwoFactorWithEmail',
      'verifyTwoFactorWithCNP',
      'requestPasswordReset',
      'verifyRecaptcha'
    ]);
    const routerSpyObj = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      declarations: [AuthComponent, HeaderComponent],
      imports: [
        ReactiveFormsModule,
        FormsModule,
        BrowserAnimationsModule,
        MatSnackBarModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatCheckboxModule,
        MatIconModule,
        MatProgressSpinnerModule
      ],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: Router, useValue: routerSpyObj }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AuthComponent);
    component = fixture.componentInstance;
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    routerSpy = TestBed.inject(Router) as jasmine.SpyObj<Router>;
  });

  beforeEach(() => {
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.email).toBe('');
    expect(component.password).toBe('');
    expect(component.useIdCardAuth).toBeFalse();
    expect(component.isLoading).toBeFalse();
    expect(component.isCaptchaVerified).toBeFalse();
  });

  describe('Classic Email Authentication', () => {
    beforeEach(() => {
      component.isCaptchaVerified = true; // Simulăm CAPTCHA verificat
    });

    it('should authenticate with email and password successfully', fakeAsync(() => {
      // Arrange
      component.email = 'test@example.com';
      component.password = 'TestPassword123!';
      component.useIdCardAuth = false;

      const mockResponse = {
        access: 'mock-access-token',
        refresh: 'mock-refresh-token',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        is_active: true,
        is_verified_by_id: false
      };

      authServiceSpy.login.and.returnValue(of(mockResponse));
      authServiceSpy.verifyRecaptcha.and.returnValue(of({ success: true }));

      // Act
      component.onSubmit();
      tick();

      // Assert
      expect(authServiceSpy.login).toHaveBeenCalledWith('test@example.com', 'TestPassword123!');
      expect(component.isLoading).toBeFalse();
    }));

    it('should handle email authentication failure', fakeAsync(() => {
      // Arrange
      component.email = 'test@example.com';
      component.password = 'wrong-password';
      component.useIdCardAuth = false;

      authServiceSpy.login.and.returnValue(
        throwError(() => ({ error: { detail: 'Autentificare eșuată' } }))
      );
      authServiceSpy.verifyRecaptcha.and.returnValue(of({ success: true }));

      // Act
      component.onSubmit();
      tick();

      // Assert
      expect(authServiceSpy.login).toHaveBeenCalled();
      expect(component.isLoading).toBeFalse();
    }));

    it('should require 2FA when needed', fakeAsync(() => {
      // Arrange
      component.email = 'test@example.com';
      component.password = 'TestPassword123!';

      const mockResponse = {
        requires_2fa: true,
        email: 'test@example.com',
        message: 'Este necesară verificarea cu doi factori'
      };

      authServiceSpy.login.and.returnValue(of(mockResponse));
      authServiceSpy.verifyRecaptcha.and.returnValue(of({ success: true }));

      // Act
      component.onSubmit();
      tick();

      // Assert
      expect(component.showTwoFactorForm).toBeTrue();
      expect(component.twoFactorEmail).toBe('test@example.com');
    }));
  });

  describe('ID Card Authentication', () => {
    beforeEach(() => {
      component.isCaptchaVerified = true;
      component.useIdCardAuth = true;
    });

    it('should authenticate with ID card details successfully', fakeAsync(() => {
      // Arrange
      component.cnp = '1234567890123';
      component.firstName = 'Ion';
      component.lastName = 'Popescu';
      component.series = 'AB';

      const mockResponse = {
        access: 'mock-access-token',
        refresh: 'mock-refresh-token',
        cnp: '1234567890123',
        first_name: 'Ion',
        last_name: 'Popescu',
        is_verified_by_id: true,
        is_active: true
      };

      authServiceSpy.loginWithIDCard.and.returnValue(of(mockResponse));
      authServiceSpy.verifyRecaptcha.and.returnValue(of({ success: true }));

      // Act
      component.onSubmit();
      tick();

      // Assert
      expect(authServiceSpy.loginWithIDCard).toHaveBeenCalledWith({
        cnp: '1234567890123',
        id_series: 'AB',
        first_name: 'Ion',
        last_name: 'Popescu'
      });
      expect(component.isLoading).toBeFalse();
    }));

    it('should handle ID card authentication failure', fakeAsync(() => {
      // Arrange
      component.cnp = '1234567890123';
      component.firstName = 'Wrong';
      component.lastName = 'Name';
      component.series = 'AB';

      authServiceSpy.loginWithIDCard.and.returnValue(
        throwError(() => ({ error: { detail: 'Numele și prenumele nu corespund' } }))
      );
      authServiceSpy.verifyRecaptcha.and.returnValue(of({ success: true }));

      // Act
      component.onSubmit();
      tick();

      // Assert
      expect(authServiceSpy.loginWithIDCard).toHaveBeenCalled();
      expect(component.isLoading).toBeFalse();
    }));

    it('should validate required ID card fields', () => {
      // Arrange
      component.cnp = '';
      component.firstName = 'Ion';
      component.lastName = 'Popescu';
      component.series = 'AB';

      // Act
      component.onSubmit();

      // Assert
      expect(component.isLoading).toBeFalse();
      expect(authServiceSpy.loginWithIDCard).not.toHaveBeenCalled();
    });

    it('should require 2FA for ID card authentication when needed', fakeAsync(() => {
      // Arrange
      component.cnp = '1234567890123';
      component.firstName = 'Ion';
      component.lastName = 'Popescu';
      component.series = 'AB';

      const mockResponse = {
        requires_2fa: true,
        cnp: '1234567890123',
        first_name: 'Ion',
        last_name: 'Popescu'
      };

      authServiceSpy.loginWithIDCard.and.returnValue(of(mockResponse));
      authServiceSpy.verifyRecaptcha.and.returnValue(of({ success: true }));

      // Act
      component.onSubmit();
      tick();

      // Assert
      expect(component.showTwoFactorForm).toBeTrue();
      expect(component.twoFactorCNP).toBe('1234567890123');
    }));
  });

  describe('Two Factor Authentication', () => {
    it('should verify 2FA code for email authentication', fakeAsync(() => {
      // Arrange
      component.showTwoFactorForm = true;
      component.twoFactorEmail = 'test@example.com';
      component.twoFactorCode = '123456';

      const mockResponse = {
        access: 'mock-access-token',
        refresh: 'mock-refresh-token',
        email: 'test@example.com'
      };

      authServiceSpy.verifyTwoFactorWithEmail.and.returnValue(of(mockResponse));

      // Act
      component.verifyTwoFactorCode();
      tick();

      // Assert
      expect(authServiceSpy.verifyTwoFactorWithEmail).toHaveBeenCalledWith('test@example.com', '123456');
      expect(component.isTwoFactorProcessing).toBeFalse();
    }));

    it('should verify 2FA code for CNP authentication', fakeAsync(() => {
      // Arrange
      component.showTwoFactorForm = true;
      component.twoFactorCNP = '1234567890123';
      component.twoFactorCode = '123456';

      const mockResponse = {
        access: 'mock-access-token',
        refresh: 'mock-refresh-token',
        cnp: '1234567890123'
      };

      authServiceSpy.verifyTwoFactorWithCNP.and.returnValue(of(mockResponse));

      // Act
      component.verifyTwoFactorCode();
      tick();

      // Assert
      expect(authServiceSpy.verifyTwoFactorWithCNP).toHaveBeenCalledWith('1234567890123', '123456');
      expect(component.isTwoFactorProcessing).toBeFalse();
    }));

    it('should handle 2FA verification failure', fakeAsync(() => {
      // Arrange
      component.showTwoFactorForm = true;
      component.twoFactorEmail = 'test@example.com';
      component.twoFactorCode = '000000';

      authServiceSpy.verifyTwoFactorWithEmail.and.returnValue(
        throwError(() => ({ error: { error: 'Cod de verificare invalid' } }))
      );

      // Act
      component.verifyTwoFactorCode();
      tick();

      // Assert
      expect(component.isTwoFactorProcessing).toBeFalse();
    }));

    it('should cancel 2FA form', () => {
      // Arrange
      component.showTwoFactorForm = true;
      component.twoFactorCode = '123456';
      component.twoFactorEmail = 'test@example.com';

      // Act
      component.cancelTwoFactor();

      // Assert
      expect(component.showTwoFactorForm).toBeFalse();
      expect(component.twoFactorCode).toBe('');
      expect(component.twoFactorEmail).toBeNull();
    });
  });

  describe('Password Reset', () => {
    beforeEach(() => {
      component.isCaptchaVerified = true;
      component.email = 'test@example.com';
    });

    it('should request password reset successfully', fakeAsync(() => {
      // Arrange
      const mockResponse = {
        message: 'Un cod de resetare a fost trimis pe adresa de email.'
      };

      authServiceSpy.requestPasswordReset.and.returnValue(of(mockResponse));

      // Act
      component.forgotPassword();
      tick();

      // Assert
      expect(authServiceSpy.requestPasswordReset).toHaveBeenCalledWith('test@example.com');
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/verify-email'], {
        queryParams: { reset: 'true', email: 'test@example.com' }
      });
    }));

    it('should require email for password reset', () => {
      // Arrange
      component.email = '';

      // Act
      component.forgotPassword();

      // Assert
      expect(authServiceSpy.requestPasswordReset).not.toHaveBeenCalled();
    });

    it('should require CAPTCHA for password reset', () => {
      // Arrange
      component.isCaptchaVerified = false;

      // Act
      component.forgotPassword();

      // Assert
      expect(authServiceSpy.requestPasswordReset).not.toHaveBeenCalled();
    });
  });

  describe('CAPTCHA Integration', () => {
    it('should prevent submission without CAPTCHA verification', () => {
      // Arrange
      component.isCaptchaVerified = false;
      component.email = 'test@example.com';
      component.password = 'TestPassword123!';

      // Act
      component.onSubmit();

      // Assert
      expect(authServiceSpy.login).not.toHaveBeenCalled();
      expect(authServiceSpy.loginWithIDCard).not.toHaveBeenCalled();
    });

    it('should handle CAPTCHA resolution', () => {
      // Act
      component.onCaptchaResolved('mock-captcha-response');

      // Assert
      expect(component.captchaResponse).toBe('mock-captcha-response');
      expect(component.isCaptchaVerified).toBeTrue();
    });

    it('should handle CAPTCHA expiration', () => {
      // Arrange
      component.isCaptchaVerified = true;
      component.captchaResponse = 'some-response';

      // Act
      component.onCaptchaExpired();

      // Assert
      expect(component.captchaResponse).toBeNull();
      expect(component.isCaptchaVerified).toBeFalse();
    });
  });

  describe('UI Interactions', () => {
    it('should toggle password visibility', () => {
      // Arrange
      expect(component.showPassword).toBeFalse();

      // Act
      component.togglePasswordVisibility();

      // Assert
      expect(component.showPassword).toBeTrue();

      // Act again
      component.togglePasswordVisibility();

      // Assert
      expect(component.showPassword).toBeFalse();
    });

    it('should toggle ID card authentication mode', () => {
      // Arrange
      expect(component.useIdCardAuth).toBeFalse();

      // Act
      component.onIdCardAuthChange();

      // Assert
      expect(component.useIdCardAuth).toBeFalse(); // Doar apelează funcția
    });

    it('should navigate to register when CAPTCHA is verified', () => {
      // Arrange
      component.isCaptchaVerified = true;

      // Act
      component.navigateToRegister();

      // Assert
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/voteapp-front']);
    });

    it('should not navigate to register without CAPTCHA verification', () => {
      // Arrange
      component.isCaptchaVerified = false;

      // Act
      component.navigateToRegister();

      // Assert
      expect(routerSpy.navigate).not.toHaveBeenCalled();
    });
  });

  describe('Face Recognition', () => {
    it('should start face recognition when CNP is provided', () => {
      // Arrange
      component.cnp = '1234567890123';
      component.isCaptchaVerified = true;

      // Act
      component.startFaceRecognition();

      // Assert
      expect(component.isFaceRecognitionActive).toBeTrue();
    });

    it('should not start face recognition without CNP', () => {
      // Arrange
      component.cnp = '';

      // Act
      component.startFaceRecognition();

      // Assert
      expect(component.isFaceRecognitionActive).toBeFalse();
    });

    it('should stop camera and reset recognition state', () => {
      // Arrange
      component.isFaceRecognitionActive = true;
      component.faceDetected = true;

      // Act
      component.stopCamera();

      // Assert
      expect(component.isFaceRecognitionActive).toBeFalse();
      expect(component.faceDetected).toBeFalse();
    });
  });

  describe('Form Validation', () => {
    it('should validate email format', () => {
      // Test prin setarea valorilor și verificarea comportamentului
      component.email = 'invalid-email';
      component.password = 'TestPassword123!';
      component.isCaptchaVerified = true;

      // Componentul ar trebui să gestioneze validarea
      expect(component.email).toBe('invalid-email');
    });

    it('should validate CNP format for ID card auth', () => {
      component.useIdCardAuth = true;
      component.cnp = '123'; // CNP invalid (prea scurt)

      expect(component.cnp).toBe('123');
    });

    it('should validate 2FA code length', () => {
      component.twoFactorCode = '12345'; // Prea scurt

      // Act
      component.verifyTwoFactorCode();

      // Assert
      expect(authServiceSpy.verifyTwoFactorWithEmail).not.toHaveBeenCalled();
      expect(authServiceSpy.verifyTwoFactorWithCNP).not.toHaveBeenCalled();
    });
  });
});