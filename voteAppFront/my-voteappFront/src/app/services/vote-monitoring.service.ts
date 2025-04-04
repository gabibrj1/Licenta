import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class VoteMonitoringService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { 
    console.log("VoteMonitoringService inițializat");
  }

  /**
   * Trimite o imagine pentru verificarea identității în timpul votului
   */
  verifyVoterIdentity(imageBlob: Blob): Observable<any> {
    console.log("verifyVoterIdentity apelat cu blob size:", imageBlob.size);
    const formData = new FormData();
    formData.append('live_image', imageBlob, 'live_capture.jpg');
    
    const url = `${this.apiUrl}vote/monitoring/`;
    console.log("URL cerere:", url);
    return this.http.post(url, formData);
    }
}