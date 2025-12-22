import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DefaultModal } from './default-modal';

describe('DefaultModal', () => {
  let component: DefaultModal;
  let fixture: ComponentFixture<DefaultModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DefaultModal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DefaultModal);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
