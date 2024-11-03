import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { VoteappFrontComponent } from './voteapp-front/voteapp-front.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';
import { AuthComponent } from './auth/auth.component';
import { HomeComponent } from './home/home.component';
const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'auth', component: AuthComponent },
  { path: 'verify-email', component: VerifyEmailComponent },
  { path: 'voteapp-front', component: VoteappFrontComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
