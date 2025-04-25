import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ForumNotificationsComponent } from './forum-notifications.component';

describe('ForumNotificationsComponent', () => {
  let component: ForumNotificationsComponent;
  let fixture: ComponentFixture<ForumNotificationsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ForumNotificationsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ForumNotificationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
