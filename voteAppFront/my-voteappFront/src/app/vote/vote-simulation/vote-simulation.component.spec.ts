import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoteSimulationComponent } from './vote-simulation.component';

describe('VoteSimulationComponent', () => {
  let component: VoteSimulationComponent;
  let fixture: ComponentFixture<VoteSimulationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VoteSimulationComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoteSimulationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
