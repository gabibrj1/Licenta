import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { 
  PresidentialCandidate, 
  CandidateDetail, 
  ElectionYear, 
  ElectionYearDetail,
  HistoricalEvent,
  MediaInfluence,
  Controversy 
} from '../../models/candidate.model';
import { environment } from '../../../../src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PresidentialCandidatesService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Obține lista de candidați
  getCandidates(currentOnly: boolean = false): Observable<PresidentialCandidate[]> {
    let params = new HttpParams();
    if (currentOnly) {
      params = params.set('current', 'true');
    }
    return this.http.get<PresidentialCandidate[]>(`${this.apiUrl}presidential-candidates/candidates/`, { params });
  }

  // Obține detalii despre un candidat specific
  getCandidateBySlug(slug: string): Observable<CandidateDetail> {
    return this.http.get<CandidateDetail>(`${this.apiUrl}presidential-candidates/candidates/${slug}/`);
  }

  getCandidateById(id: number): Observable<CandidateDetail> {
    return this.http.get<CandidateDetail>(`${this.apiUrl}presidential-candidates/candidates/${id}/`);
  }

  // Obține lista anilor electorali
  getElectionYears(): Observable<ElectionYear[]> {
    return this.http.get<ElectionYear[]>(`${this.apiUrl}presidential-candidates/election-years/`);
  }

  // Obține detalii despre un an electoral specific
  getElectionYear(year: number): Observable<ElectionYearDetail> {
    return this.http.get<ElectionYearDetail>(`${this.apiUrl}presidential-candidates/election-years/${year}/`);
  }

  // Obține evenimente istorice
  getHistoricalEvents(): Observable<HistoricalEvent[]> {
    return this.http.get<HistoricalEvent[]>(`${this.apiUrl}presidential-candidates/historical-events/`);
  }

  // Obține influențele media
  getMediaInfluences(type?: string): Observable<MediaInfluence[]> {
    let params = new HttpParams();
    if (type) {
      params = params.set('type', type);
    }
    return this.http.get<MediaInfluence[]>(`${this.apiUrl}presidential-candidates/media-influences/`, { params });
  }

  // Obține controversele
  getControversies(candidateId?: number, electionYear?: number): Observable<Controversy[]> {
    let params = new HttpParams();
    if (candidateId) {
      params = params.set('candidate_id', candidateId.toString());
    }
    if (electionYear) {
      params = params.set('election_year', electionYear.toString());
    }
    
    return this.http.get<Controversy[]>(`${this.apiUrl}presidential-candidates/controversies/`, { params });
  }
}