import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CompareAuditList } from './compare-audit-list';

describe('CompareAuditList', () => {
  let component: CompareAuditList;
  let fixture: ComponentFixture<CompareAuditList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CompareAuditList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CompareAuditList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
