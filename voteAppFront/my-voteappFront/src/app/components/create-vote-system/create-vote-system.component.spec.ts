import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateVoteSystemComponent } from './create-vote-system.component';

describe('CreateVoteSystemComponent', () => {
  let component: CreateVoteSystemComponent;
  let fixture: ComponentFixture<CreateVoteSystemComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CreateVoteSystemComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CreateVoteSystemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
