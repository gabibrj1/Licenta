import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PresidentialVoteComponent } from './presidential-vote.component';

describe('PresidentialVoteComponent', () => {
  let component: PresidentialVoteComponent;
  let fixture: ComponentFixture<PresidentialVoteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PresidentialVoteComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PresidentialVoteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
