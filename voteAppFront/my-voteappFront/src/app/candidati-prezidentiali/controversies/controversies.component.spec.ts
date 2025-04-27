import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ControversiesComponent } from './controversies.component';

describe('ControversiesComponent', () => {
  let component: ControversiesComponent;
  let fixture: ComponentFixture<ControversiesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ControversiesComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ControversiesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
