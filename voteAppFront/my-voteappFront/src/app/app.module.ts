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

import { AuthGuard } from './guards/auth.guard';
import { ScheduleDialogComponent } from './schedule-dialog/schedule-dialog.component';
import { VoteReceiptComponent } from './components/vote-receipt/vote-receipt.component';

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
    VoteReceiptComponent
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
    VoteModule,
    NgxEchartsModule.forRoot({
      echarts: () => import('echarts')
    }),
    AppRoutingModule,
  ],
  
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: CsrfInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
    VoteMonitoringService  
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }