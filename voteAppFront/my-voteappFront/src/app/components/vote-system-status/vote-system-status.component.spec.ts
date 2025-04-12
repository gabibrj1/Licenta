import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoteSystemStatusComponent } from './vote-system-status.component';

describe('VoteSystemStatusComponent', () => {
  let component: VoteSystemStatusComponent;
  let fixture: ComponentFixture<VoteSystemStatusComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VoteSystemStatusComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoteSystemStatusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
