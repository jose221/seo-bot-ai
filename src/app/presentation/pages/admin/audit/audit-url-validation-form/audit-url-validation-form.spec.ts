import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AuditUrlValidationForm } from './audit-url-validation-form';

describe('AuditUrlValidationForm', () => {
  let component: AuditUrlValidationForm;
  let fixture: ComponentFixture<AuditUrlValidationForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuditUrlValidationForm],
    }).compileComponents();

    fixture = TestBed.createComponent(AuditUrlValidationForm);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

