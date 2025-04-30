import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../src/environments/environment';
import { 
  ElectionCycle, 
  ElectionCycleDetail,
  LocalElectionType,
  LocalPosition,
  LocalElectionRule,
  SignificantCandidate,
  ImportantEvent,
  LegislationChange
} from '../models/local-candidate.model';

@Injectable({
  providedIn: 'root'
})
export class LocalCandidatesService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Obține lista de cicluri electorale locale
  getElectionCycles(): Observable<ElectionCycle[]> {
    return this.http.get<ElectionCycle[]>(`${this.apiUrl}local-candidates/election-cycles/`);
  }

  // Obține detalii despre un ciclu electoral specific
  getElectionCycle(year: number): Observable<ElectionCycleDetail> {
    return this.http.get<ElectionCycleDetail>(`${this.apiUrl}local-candidates/election-cycles/${year}/`);
  }

  // Obține lista tipurilor de alegeri locale
  getElectionTypes(): Observable<LocalElectionType[]> {
    return this.http.get<LocalElectionType[]>(`${this.apiUrl}local-candidates/election-types/`);
  }

  // Obține lista pozițiilor locale
  getPositions(electionTypeId?: number): Observable<LocalPosition[]> {
    let params = new HttpParams();
    if (electionTypeId) {
      params = params.set('election_type', electionTypeId.toString());
    }
    return this.http.get<LocalPosition[]>(`${this.apiUrl}local-candidates/positions/`, { params });
  }

  // Obține regulile electorale
  getRules(electionTypeId?: number, currentOnly: boolean = false): Observable<LocalElectionRule[]> {
    let params = new HttpParams();
    if (electionTypeId) {
      params = params.set('election_type', electionTypeId.toString());
    }
    if (currentOnly) {
      params = params.set('current', 'true');
    }
    return this.http.get<LocalElectionRule[]>(`${this.apiUrl}local-candidates/rules/`, { params });
  }

  // Obține candidații semnificativi
  getSignificantCandidates(positionId?: number, electionCycleId?: number): Observable<SignificantCandidate[]> {
    let params = new HttpParams();
    if (positionId) {
      params = params.set('position', positionId.toString());
    }
    if (electionCycleId) {
      params = params.set('election_cycle', electionCycleId.toString());
    }
    return this.http.get<SignificantCandidate[]>(`${this.apiUrl}local-candidates/significant-candidates/`, { params });
  }

  // Obține detalii despre un candidat semnificativ specific
  getSignificantCandidate(slug: string): Observable<SignificantCandidate> {
    return this.http.get<SignificantCandidate>(`${this.apiUrl}local-candidates/significant-candidates/${slug}/`);
  }

  // Obține evenimente importante
  getImportantEvents(electionCycleId?: number, importance?: number): Observable<ImportantEvent[]> {
    let params = new HttpParams();
    if (electionCycleId) {
      params = params.set('election_cycle', electionCycleId.toString());
    }
    if (importance) {
      params = params.set('importance', importance.toString());
    }
    return this.http.get<ImportantEvent[]>(`${this.apiUrl}local-candidates/important-events/`, { params });
  }

  // Obține modificările legislative
  getLegislationChanges(year?: number): Observable<LegislationChange[]> {
    let params = new HttpParams();
    if (year) {
      params = params.set('year', year.toString());
    }
    return this.http.get<LegislationChange[]>(`${this.apiUrl}local-candidates/legislation-changes/`, { params });
  }
}