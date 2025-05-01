import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SetariContComponent } from './setari-cont.component';

describe('SetariContComponent', () => {
  let component: SetariContComponent;
  let fixture: ComponentFixture<SetariContComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SetariContComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SetariContComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
