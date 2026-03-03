import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AuditSchemaForm } from './audit-schema-form';

describe('AuditSchemaForm', () => {
  let component: AuditSchemaForm;
  let fixture: ComponentFixture<AuditSchemaForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuditSchemaForm],
    }).compileComponents();

    fixture = TestBed.createComponent(AuditSchemaForm);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

