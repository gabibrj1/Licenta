import { TestBed } from '@angular/core/testing';

import { SetariContService } from './setari-cont.service';

describe('SetariContService', () => {
  let service: SetariContService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SetariContService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
