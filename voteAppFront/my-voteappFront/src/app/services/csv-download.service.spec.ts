import { TestBed } from '@angular/core/testing';

import { CsvDownloadService } from './csv-download.service';

describe('CsvDownloadService', () => {
  let service: CsvDownloadService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CsvDownloadService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
