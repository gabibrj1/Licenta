import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LocalVoteComponent } from './local-vote.component';

describe('LocalVoteComponent', () => {
  let component: LocalVoteComponent;
  let fixture: ComponentFixture<LocalVoteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [LocalVoteComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LocalVoteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
