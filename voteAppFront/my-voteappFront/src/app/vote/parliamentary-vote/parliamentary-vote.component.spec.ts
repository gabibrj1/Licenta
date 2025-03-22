import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParliamentaryVoteComponent } from './parliamentary-vote.component';

describe('ParliamentaryVoteComponent', () => {
  let component: ParliamentaryVoteComponent;
  let fixture: ComponentFixture<ParliamentaryVoteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ParliamentaryVoteComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ParliamentaryVoteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
