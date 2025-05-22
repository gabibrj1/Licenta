import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PresidentialRound2VoteComponent } from './presidential-round2-vote.component';

describe('PresidentialRound2VoteComponent', () => {
  let component: PresidentialRound2VoteComponent;
  let fixture: ComponentFixture<PresidentialRound2VoteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PresidentialRound2VoteComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PresidentialRound2VoteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
