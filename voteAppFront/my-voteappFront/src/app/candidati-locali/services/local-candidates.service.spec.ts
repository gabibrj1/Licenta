import { TestBed } from '@angular/core/testing';

import { LocalCandidatesService } from './local-candidates.service';

describe('LocalCandidatesService', () => {
  let service: LocalCandidatesService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LocalCandidatesService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
