import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { VoteappFrontComponent } from './voteapp-front/voteapp-front.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatSidenavModule } from '@angular/material/sidenav';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { SpinnerModule } from '@coreui/angular';
import { MatDialogModule } from '@angular/material/dialog';
import { RegisterComponent } from './register/register.component';
import { AuthComponent } from './auth/auth.component';
import { HomeComponent } from './home/home.component';
import { HeaderComponent } from './header/header.component';
import { GdprDialogComponent } from './gdpr-dialog/gdpr-dialog.component';
import { MenuComponent } from './menu/menu.component';
import { CsrfInterceptor } from './interceptors/csrf.interceptor';
import { AuthInterceptor } from './interceptors/auth.interceptor';
import { ReviewsComponent } from './reviews/reviews.component';
import { DeleteConfirmDialogComponent } from './delete-confirm.dialog/delete-confirm.dialog.component';
import { WarningDialogComponent } from './warning-dialog/warning-dialog.component';
import { ContactComponent } from './contact/contact.component';
import { AppointmentConfirmedComponent } from './appointments/appointment-confirmed.component';
import { AppointmentRejectedComponent } from './appointments/appointment-rejected.component';
import { AppointmentErrorComponent } from './appointments/appointment-error.component';
import { MapComponent } from './map/map.component';
import { NgxEchartsModule } from 'ngx-echarts';
import { VoteModule } from './vote/vote.module';
import { VoteMonitoringService } from './services/vote-monitoring.service'; 
import { PresidentialVoteService } from './services/presidential-vote.service';
import { AuthBypassInterceptor } from './interceptors/auth-bypass.interceptor';

import { AuthGuard } from './guards/auth.guard';
import { ScheduleDialogComponent } from './schedule-dialog/schedule-dialog.component';
import { VoteReceiptComponent } from './components/vote-receipt/vote-receipt.component';
import { CreateVoteSystemComponent } from './components/create-vote-system/create-vote-system.component';
import { MyVoteSystemsComponent } from './components/my-vote-systems/my-vote-systems.component';
import { VoteSystemDetailsComponent } from './components/vote-system-details/vote-system-details.component';
import { VoteSystemStatusComponent } from './components/vote-system-status/vote-system-status.component';
import { PublicVoteComponent } from './components/public-vote/public-vote.component';
import { EmailTokenVerificationComponent } from './components/email-token-verification/email-token-verification.component';
import { MisiuneComponent } from './misiune/misiune.component';
import { ConceptComponent } from './concept/concept.component';
import { NewsComponent } from './news/news.component';
import { ArticleDetailComponent } from './article-detail/article-detail.component';
import { ForumModule } from './forum/forum.module';
import { ForumuriComponent } from './forumuri/forumuri.component';
import { CandidatiPrezidentialiComponent } from './candidati-prezidentiali/candidati-prezidentiali.component';
import { CandidatDetailComponent } from './candidati-prezidentiali/candidat-detail/candidat-detail.component';
import { ControversiesComponent } from './candidati-prezidentiali/controversies/controversies.component';
import { MediaInfluenceComponent } from './candidati-prezidentiali/media-influence/media-influence.component';
import { TimelineComponent } from './candidati-prezidentiali/timeline/timeline.component';
import { PresidentialCandidatesService } from './candidati-prezidentiali/candidati-prezidentiali/services/presidential-candidates.service';
import { TransitionComponent } from './candidati-prezidentiali/transition/transition.component';
import { CandidatiLocaliComponent } from './candidati-locali/candidati-locali.component';
import { SetariContComponent } from './setari-cont/setari-cont.component';
import { ConfirmDialogComponent } from './shared/confirm-dialog/confirm-dialog.component'; 
import { MatDividerModule } from '@angular/material/divider';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TwoFactorDialogComponent } from './shared/two-factor-dialog/two-factor-dialog.component';
import { ClipboardModule } from '@angular/cdk/clipboard';

@NgModule({
  declarations: [
    AppComponent,
    VoteappFrontComponent,
    VerifyEmailComponent,
    RegisterComponent,
    AuthComponent,
    HomeComponent,
    HeaderComponent,
    GdprDialogComponent,
    MenuComponent,
    ReviewsComponent,
    DeleteConfirmDialogComponent,
    WarningDialogComponent,
    ContactComponent,
    ScheduleDialogComponent,
    AppointmentConfirmedComponent,
    AppointmentRejectedComponent,
    AppointmentErrorComponent,
    MapComponent,
    VoteReceiptComponent,
    CreateVoteSystemComponent,
    MyVoteSystemsComponent,
    VoteSystemDetailsComponent,
    VoteSystemStatusComponent,
    PublicVoteComponent,
    EmailTokenVerificationComponent,
    MisiuneComponent,
    ConceptComponent,
    NewsComponent,
    ArticleDetailComponent,
    ForumuriComponent,
    CandidatiPrezidentialiComponent,
    CandidatDetailComponent,
    ControversiesComponent,
    MediaInfluenceComponent,
    TimelineComponent,
    TransitionComponent,
    CandidatiLocaliComponent,
    SetariContComponent,
    ConfirmDialogComponent,
    TwoFactorDialogComponent,

  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    BrowserAnimationsModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatCheckboxModule,
    MatIconModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    ReactiveFormsModule,
    MatSlideToggleModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatCardModule,
    MatSidenavModule,
    FontAwesomeModule,
    SpinnerModule,
    MatDialogModule,
    MatButtonModule,
    ForumModule,
    MatButtonModule,
    MatDividerModule,
    MatTabsModule,
    MatTooltipModule,
    ClipboardModule,
    VoteModule,
    NgxEchartsModule.forRoot({
      echarts: () => import('echarts')
    }),
    AppRoutingModule,
  ],
  
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: CsrfInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: AuthBypassInterceptor, multi: true },
    VoteMonitoringService,
    PresidentialVoteService,
    PresidentialCandidatesService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }