import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { VoteappFrontComponent } from './voteapp-front/voteapp-front.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';
import { AuthComponent } from './auth/auth.component';
import { HomeComponent } from './home/home.component';
import { MenuComponent } from './menu/menu.component';
import { ReviewsComponent } from './reviews/reviews.component';
import { AuthGuard } from './guards/auth.guard';
const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'auth', component: AuthComponent },
  { path: 'menu', component: MenuComponent, canActivate: [AuthGuard] },
  { path: 'verify-email', component: VerifyEmailComponent },
  { path: 'voteapp-front', component: VoteappFrontComponent},
  { path: 'reviews', component: ReviewsComponent },
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