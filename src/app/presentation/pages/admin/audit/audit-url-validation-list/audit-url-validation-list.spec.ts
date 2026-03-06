import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AuditUrlValidationList } from './audit-url-validation-list';

describe('AuditUrlValidationList', () => {
  let component: AuditUrlValidationList;
  let fixture: ComponentFixture<AuditUrlValidationList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuditUrlValidationList],
    }).compileComponents();

    fixture = TestBed.createComponent(AuditUrlValidationList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

