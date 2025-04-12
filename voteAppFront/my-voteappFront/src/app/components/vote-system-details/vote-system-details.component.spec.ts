import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoteSystemDetailsComponent } from './vote-system-details.component';

describe('VoteSystemDetailsComponent', () => {
  let component: VoteSystemDetailsComponent;
  let fixture: ComponentFixture<VoteSystemDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VoteSystemDetailsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoteSystemDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
