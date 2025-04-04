import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { VoteRoutingModule } from './vote-routing.module';
import { PresidentialVoteComponent } from './presidential-vote/presidential-vote.component';
import { ParliamentaryVoteComponent } from './parliamentary-vote/parliamentary-vote.component';
import { LocalVoteComponent } from './local-vote/local-vote.component';
import { VoteSimulationComponent } from './vote-simulation/vote-simulation.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { VoteMonitoringService } from '../services/vote-monitoring.service';

@NgModule({
  declarations: [
    PresidentialVoteComponent,
    ParliamentaryVoteComponent,
    LocalVoteComponent,
    VoteSimulationComponent
  ],
  imports: [
    CommonModule,
    VoteRoutingModule,
    FormsModule,
    ReactiveFormsModule
  ],
  providers: [
    VoteMonitoringService
  ],
})
export class VoteModule { }
