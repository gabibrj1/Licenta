import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MisiuneComponent } from './misiune.component';

describe('MisiuneComponent', () => {
  let component: MisiuneComponent;
  let fixture: ComponentFixture<MisiuneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MisiuneComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MisiuneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
