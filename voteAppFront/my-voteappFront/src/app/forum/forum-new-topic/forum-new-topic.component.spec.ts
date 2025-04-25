import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ForumNewTopicComponent } from './forum-new-topic.component';

describe('ForumNewTopicComponent', () => {
  let component: ForumNewTopicComponent;
  let fixture: ComponentFixture<ForumNewTopicComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ForumNewTopicComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ForumNewTopicComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
