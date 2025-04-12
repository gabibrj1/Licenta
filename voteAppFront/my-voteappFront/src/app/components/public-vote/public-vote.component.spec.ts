import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PublicVoteComponent } from './public-vote.component';

describe('PublicVoteComponent', () => {
  let component: PublicVoteComponent;
  let fixture: ComponentFixture<PublicVoteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PublicVoteComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PublicVoteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
