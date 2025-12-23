import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CompareAuditForm } from './compare-audit-form';

describe('CompareAuditForm', () => {
  let component: CompareAuditForm;
  let fixture: ComponentFixture<CompareAuditForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CompareAuditForm]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CompareAuditForm);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
