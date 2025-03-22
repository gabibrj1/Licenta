import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-vote-simulation',
  templateUrl: './vote-simulation.component.html',
  styleUrls: ['./vote-simulation.component.scss']
})
export class VoteSimulationComponent implements OnInit {
  stepIndex = 0;
  simulationComplete = false;

  constructor() { }

  ngOnInit(): void {
  }

  nextStep() {
    if (this.stepIndex < 3) {
      this.stepIndex++;
    } else {
      this.simulationComplete = true;
    }
  }

  prevStep() {
    if (this.stepIndex > 0) {
      this.stepIndex--;
    }
  }

  resetSimulation() {
    this.stepIndex = 0;
    this.simulationComplete = false;
  }
}