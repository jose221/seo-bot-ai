import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BodyModalComponent } from './body-modal.component';

describe('BodyModalComponent', () => {
  let component: BodyModalComponent;
  let fixture: ComponentFixture<BodyModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BodyModalComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BodyModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
