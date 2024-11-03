import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoteappFrontComponent } from './voteapp-front.component';

describe('VoteappFrontComponent', () => {
  let component: VoteappFrontComponent;
  let fixture: ComponentFixture<VoteappFrontComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VoteappFrontComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoteappFrontComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
