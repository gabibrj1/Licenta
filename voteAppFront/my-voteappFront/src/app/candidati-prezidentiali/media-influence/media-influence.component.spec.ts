import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MediaInfluenceComponent } from './media-influence.component';

describe('MediaInfluenceComponent', () => {
  let component: MediaInfluenceComponent;
  let fixture: ComponentFixture<MediaInfluenceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MediaInfluenceComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MediaInfluenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
