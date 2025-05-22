import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PresidentialVoteComponent } from './presidential-vote/presidential-vote.component';
import { PresidentialRound2VoteComponent } from './presidential-round2-vote/presidential-round2-vote.component';
import { ParliamentaryVoteComponent } from './parliamentary-vote/parliamentary-vote.component';
import { LocalVoteComponent } from './local-vote/local-vote.component';
import { VoteSimulationComponent } from './vote-simulation/vote-simulation.component';
import { AuthGuard } from '../guards/auth.guard';

const routes: Routes = [
  // Simulare vot - fără prefixul "menu/" deoarece acum este o rută copil
  { path: 'simulare-vot', component: VoteSimulationComponent },
  
  // Rute pentru votul real - fără prefixul "menu/vot" deoarece acum sunt rute copil
  { path: 'prezidentiale', component: PresidentialVoteComponent, canActivate: [AuthGuard] },
  { path: 'prezidentiale-tur2', component: PresidentialRound2VoteComponent, canActivate: [AuthGuard] },
  { path: 'parlamentare', component: ParliamentaryVoteComponent, canActivate: [AuthGuard] },
  { path: 'locale', component: LocalVoteComponent, canActivate: [AuthGuard] }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class VoteRoutingModule { }