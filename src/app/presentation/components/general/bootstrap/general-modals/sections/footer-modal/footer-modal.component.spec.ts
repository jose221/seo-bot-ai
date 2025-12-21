import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FooterModalComponent } from './footer-modal.component';

describe('FooterModalComponent', () => {
  let component: FooterModalComponent;
  let fixture: ComponentFixture<FooterModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FooterModalComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FooterModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
