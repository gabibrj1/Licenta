import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CandidatiLocaliComponent } from './candidati-locali.component';

describe('CandidatiLocaliComponent', () => {
  let component: CandidatiLocaliComponent;
  let fixture: ComponentFixture<CandidatiLocaliComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CandidatiLocaliComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CandidatiLocaliComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
