import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AuditForm } from './audit-form';

describe('AuditForm', () => {
  let component: AuditForm;
  let fixture: ComponentFixture<AuditForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuditForm]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AuditForm);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
