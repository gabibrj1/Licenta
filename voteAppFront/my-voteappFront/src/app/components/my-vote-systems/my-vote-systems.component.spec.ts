import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MyVoteSystemsComponent } from './my-vote-systems.component';

describe('MyVoteSystemsComponent', () => {
  let component: MyVoteSystemsComponent;
  let fixture: ComponentFixture<MyVoteSystemsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MyVoteSystemsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MyVoteSystemsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
