import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SetariContService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Get user profile with all settings
  getUserProfile(): Observable<any> {
    return this.http.get(`${this.apiUrl}account/profile/`);
  }

  // Update user profile
  updateUserProfile(data: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}account/profile/`, data);
  }

  // Upload profile image
  uploadProfileImage(formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}account/profile-image/`, formData);
  }

  // Delete profile image
  deleteProfileImage(): Observable<any> {
    return this.http.delete(`${this.apiUrl}account/profile-image/`);
  }

  // Update account settings
  updateAccountSettings(settings: any): Observable<any> {
    return this.http.put(`${this.apiUrl}account/settings/`, settings);
  }

  // Change password
  changePassword(passwordData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}account/change-password/`, passwordData);
  }

  // Delete/deactivate account
  deleteAccount(): Observable<any> {
    return this.http.post(`${this.apiUrl}account/delete-account/`, {});
  }
}