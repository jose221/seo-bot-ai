import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AuditSchemaList } from './audit-schema-list';

describe('AuditSchemaList', () => {
  let component: AuditSchemaList;
  let fixture: ComponentFixture<AuditSchemaList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuditSchemaList],
    }).compileComponents();

    fixture = TestBed.createComponent(AuditSchemaList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

