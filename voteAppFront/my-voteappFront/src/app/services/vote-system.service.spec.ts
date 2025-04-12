import { TestBed } from '@angular/core/testing';

import { VoteSystemService } from './vote-system.service';

describe('VoteSystemService', () => {
  let service: VoteSystemService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(VoteSystemService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
