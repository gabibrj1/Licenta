import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { VoteappFrontComponent } from './voteapp-front/voteapp-front.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ReactiveFormsModule } from '@angular/forms';
// Angular Material
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { CsrfInterceptor } from './interceptors/csrf.interceptor';
import { RegisterComponent } from './register/register.component';
import { AuthComponent } from './auth/auth.component';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { HomeComponent } from './home/home.component';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { SpinnerModule } from '@coreui/angular';
import { HeaderComponent } from './header/header.component';
import { GdprDialogComponent } from './gdpr-dialog/gdpr-dialog.component';
import { MatDialogModule } from '@angular/material/dialog';


@NgModule({
  declarations: [
    AppComponent,
    VoteappFrontComponent,
    VerifyEmailComponent,
    RegisterComponent,
    AuthComponent,
    HomeComponent,
    HeaderComponent,
    GdprDialogComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
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
    FontAwesomeModule,
    SpinnerModule,
    MatDialogModule
    
    
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: CsrfInterceptor, multi: true }, // Înregistrarea interceptorului
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
