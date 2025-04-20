// src/app/services/shared.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SharedService {
  private pageLoadedSubject = new BehaviorSubject<boolean>(false);
  public pageLoaded$ = this.pageLoadedSubject.asObservable();

  constructor() { }

  setPageLoaded(value: boolean) {
    this.pageLoadedSubject.next(value);
  }
}