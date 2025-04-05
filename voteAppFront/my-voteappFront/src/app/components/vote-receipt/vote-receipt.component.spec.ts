import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VoteReceiptComponent } from './vote-receipt.component';

describe('VoteReceiptComponent', () => {
  let component: VoteReceiptComponent;
  let fixture: ComponentFixture<VoteReceiptComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VoteReceiptComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VoteReceiptComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
