import { Routes } from '@angular/router';
import {Login} from '@/app/presentation/pages/auth/login/login';
import {authGuard} from '@/app/presentation/guards/auth.guard';
import {Admin} from '@/app/presentation/pages/admin/admin';
import {TargetList} from '@/app/presentation/pages/admin/target/target-list/target-list';
import {TargetForm} from '@/app/presentation/pages/admin/target/target-form/target-form';
import {TargetUpdate} from '@/app/presentation/pages/admin/target/target-update/target-update';
import {AuditList} from '@/app/presentation/pages/admin/audit/audit-list/audit-list';
import {AuditForm} from '@/app/presentation/pages/admin/audit/audit-form/audit-form';
import {CompareAuditForm} from '@/app/presentation/pages/admin/audit/compare-audit-form/compare-audit-form';
import {CompareAuditList} from '@/app/presentation/pages/admin/audit/compare-audit-list/compare-audit-list';
import {AuditSchemaList} from '@/app/presentation/pages/admin/audit/audit-schema-list/audit-schema-list';
import {AuditSchemaForm} from '@/app/presentation/pages/admin/audit/audit-schema-form/audit-schema-form';
import {AuditUrlValidationList} from '@/app/presentation/pages/admin/audit/audit-url-validation-list/audit-url-validation-list';
import {AuditUrlValidationForm} from '@/app/presentation/pages/admin/audit/audit-url-validation-form/audit-url-validation-form';
import {loginGuard} from '@/app/presentation/guards/login.guard';
import {MetricsDashboardComponent} from '@/app/presentation/components/metrics-dashboard/metrics-dashboard.component';
import {JsonTools} from '@/app/presentation/pages/admin/json-tools/json-tools';
import {AuditDetail} from '@/app/presentation/pages/admin/audit/audit-detail/audit-detail';
import {CompareAuditDetail} from '@/app/presentation/pages/admin/audit/compare-audit-detail/compare-audit-detail';
import {AuditSchemaDetail} from '@/app/presentation/pages/admin/audit/audit-schema-detail/audit-schema-detail';
import {AuditUrlValidationDetail} from '@/app/presentation/pages/admin/audit/audit-url-validation-detail/audit-url-validation-detail';

export const routes: Routes = [
  { path: '', component: Login, canActivate: [loginGuard] },
  {
    path: 'admin',
    component: Admin,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'target', pathMatch: 'full' },
      {path: 'target', component: TargetList},
      {path: 'target/create', component: TargetForm},
      {path: 'target/update/:id', component: TargetUpdate},
      {path: 'audit', component: AuditList},
      {path: 'audit/create', component: AuditForm},
      {path: 'audit/comparisons', component: CompareAuditList},
      {path: 'audit/comparisons/:id', component: CompareAuditDetail},
      {path: 'audit/compare', component: CompareAuditForm},
      {path: 'audit/schemas', component: AuditSchemaList},
      {path: 'audit/schemas/create', component: AuditSchemaForm},
      {path: 'audit/schemas/:id', component: AuditSchemaDetail},
      {path: 'audit/url-validations', component: AuditUrlValidationList},
      {path: 'audit/url-validations/create', component: AuditUrlValidationForm},
      {path: 'audit/url-validations/:id/info', loadComponent: () => import('@/app/presentation/pages/admin/audit/audit-url-validation-info/audit-url-validation-info')},
      {path: 'audit/url-validations/:id', component: AuditUrlValidationDetail},
      {path: 'audit/:id', component: AuditDetail},
      {path: 'metrics', component: MetricsDashboardComponent},
      {path: 'json-tools', component: JsonTools},
    ]
  },
  {path: 'shared/audit/url-validations/:id/info', loadComponent: () => import('@/app/presentation/pages/shared/audit-url-validation-info/audit-url-validation-info')},
  { path: '**', redirectTo: '/admin' }
];
