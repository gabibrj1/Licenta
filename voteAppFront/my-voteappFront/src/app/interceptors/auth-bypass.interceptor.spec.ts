import { TestBed } from '@angular/core/testing';
import { AuthBypassInterceptor } from './auth-bypass.interceptor';

describe('AuthBypassInterceptor', () => {
  let interceptor: AuthBypassInterceptor;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AuthBypassInterceptor]
    });
    interceptor = TestBed.inject(AuthBypassInterceptor);
  });

  it('should be created', () => {
    expect(interceptor).toBeTruthy();
  });
});