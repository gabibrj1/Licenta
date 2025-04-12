import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { VoteappFrontComponent } from './voteapp-front/voteapp-front.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';
import { AuthComponent } from './auth/auth.component';
import { HomeComponent } from './home/home.component';
import { MenuComponent } from './menu/menu.component';
import { ContactComponent } from './contact/contact.component';
import { ReviewsComponent } from './reviews/reviews.component';
import { AuthGuard } from './guards/auth.guard';
import { VoteSimulationComponent } from './vote/vote-simulation/vote-simulation.component';
import { PresidentialVoteComponent } from './vote/presidential-vote/presidential-vote.component';
import { ParliamentaryVoteComponent } from './vote/parliamentary-vote/parliamentary-vote.component';
import { LocalVoteComponent } from './vote/local-vote/local-vote.component';
import { VoteReceiptComponent } from './components/vote-receipt/vote-receipt.component';
import { CreateVoteSystemComponent } from './components/create-vote-system/create-vote-system.component';
import { VoteSystemStatusComponent } from './components/vote-system-status/vote-system-status.component';
import { VoteSystemDetailsComponent } from './components/vote-system-details/vote-system-details.component';
import { MyVoteSystemsComponent } from './components/my-vote-systems/my-vote-systems.component';
import { PublicVoteComponent } from './components/public-vote/public-vote.component';

import { AppointmentConfirmedComponent } from './appointments/appointment-confirmed.component';
import { AppointmentRejectedComponent } from './appointments/appointment-rejected.component';
import { AppointmentErrorComponent } from './appointments/appointment-error.component';
import { MapComponent } from './map/map.component';

const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'auth', component: AuthComponent },
  { 
    path: 'menu', 
    component: MenuComponent,
    children: [
      { path: 'despre/contact', component: ContactComponent },
      { path: 'despre/creeaza-sistem', component: CreateVoteSystemComponent, canActivate: [AuthGuard] },
      { path: 'despre/sisteme-vot', component: MyVoteSystemsComponent, canActivate: [AuthGuard] },
      { path: 'despre/sisteme-vot/:id', component: VoteSystemDetailsComponent, canActivate: [AuthGuard] },
      { path: 'despre/status-vot/:id', component: VoteSystemStatusComponent, canActivate: [AuthGuard] },
      
      { path: 'harta', component: MapComponent},
      // Rute pentru vot și simulare
      { path: 'simulare-vot', component: VoteSimulationComponent },
      { path: 'vot/prezidentiale', component: PresidentialVoteComponent, canActivate: [AuthGuard] },
      { path: 'vot/parlamentare', component: ParliamentaryVoteComponent, canActivate: [AuthGuard] },
      { path: 'vot/locale', component: LocalVoteComponent, canActivate: [AuthGuard] },

      // Aici poți adăuga alte rute pentru conținutul din meniu
      { path: '', redirectTo: '', pathMatch: 'full' } // Modificat: nu mai redirecționăm
    ]
  },
  { path: 'verify-email', component: VerifyEmailComponent },
  { path: 'voteapp-front', component: VoteappFrontComponent},
  { path: 'reviews', component: ReviewsComponent },
  { path: 'vote/:id', component: PublicVoteComponent },

  { path: 'appointment-confirmed', component: AppointmentConfirmedComponent },
  { path: 'appointment-rejected', component: AppointmentRejectedComponent },
  { path: 'appointment-error', component: AppointmentErrorComponent },
  { path: 'harta', component: MapComponent },

  // Adăugăm ruta pentru confirmarea de vot
  { path: 'vote-receipt', component: VoteReceiptComponent, canActivate: [AuthGuard] },
  

  { path: '**', redirectTo: '/auth'} //redirect pt rute inexistente
];

@NgModule({
  imports: [RouterModule.forRoot(routes, {
    scrollPositionRestoration: 'enabled', // Restaurează scroll-ul la poziția 0 pe navigare
    anchorScrolling: 'disabled' // Previne scroll-ul către fragmente
  })],
  exports: [RouterModule]
})
export class AppRoutingModule { }