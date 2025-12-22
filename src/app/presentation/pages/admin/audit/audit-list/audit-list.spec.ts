import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AuditList } from './audit-list';

describe('AuditList', () => {
  let component: AuditList;
  let fixture: ComponentFixture<AuditList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuditList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AuditList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
