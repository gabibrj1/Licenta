import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CandidatiPrezidentialiComponent } from './candidati-prezidentiali.component';

describe('CandidatiPrezidentialiComponent', () => {
  let component: CandidatiPrezidentialiComponent;
  let fixture: ComponentFixture<CandidatiPrezidentialiComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CandidatiPrezidentialiComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CandidatiPrezidentialiComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
