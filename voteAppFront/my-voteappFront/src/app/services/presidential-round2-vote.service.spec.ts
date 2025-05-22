import { TestBed } from '@angular/core/testing';

import { PresidentialRound2VoteService } from './presidential-round2-vote.service';

describe('PresidentialRound2VoteService', () => {
  let service: PresidentialRound2VoteService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PresidentialRound2VoteService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
