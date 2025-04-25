import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ForumuriComponent } from './forumuri.component';

describe('ForumuriComponent', () => {
  let component: ForumuriComponent;
  let fixture: ComponentFixture<ForumuriComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ForumuriComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ForumuriComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
