import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

export interface AppointmentRequest {
  name: string;
  email: string;
  phone: string;
  dateTime: string;
  notes?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AppointmentService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  scheduleAppointment(appointmentData: AppointmentRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}menu/appointments/schedule/`, appointmentData);
  }
  getAvailableHours(date: string): Observable<any> {
    return this.http.get(`${this.apiUrl}menu/appointments/availability/${date}/`);
  }
}