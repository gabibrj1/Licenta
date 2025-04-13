import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmailTokenVerificationComponent } from './email-token-verification.component';

describe('EmailTokenVerificationComponent', () => {
  let component: EmailTokenVerificationComponent;
  let fixture: ComponentFixture<EmailTokenVerificationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [EmailTokenVerificationComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EmailTokenVerificationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
