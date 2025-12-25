import { Routes } from '@angular/router';
import {Login} from '@/app/presentation/pages/auth/login/login';
import {authGuard} from '@/app/presentation/guards/auth.guard';
import {Admin} from '@/app/presentation/pages/admin/admin';
import {TargetList} from '@/app/presentation/pages/admin/target/target-list/target-list';
import {TargetForm} from '@/app/presentation/pages/admin/target/target-form/target-form';
import {AuditList} from '@/app/presentation/pages/admin/audit/audit-list/audit-list';
import {AuditForm} from '@/app/presentation/pages/admin/audit/audit-form/audit-form';
import {CompareAuditForm} from '@/app/presentation/pages/admin/audit/compare-audit-form/compare-audit-form';
import {CompareAuditList} from '@/app/presentation/pages/admin/audit/compare-audit-list/compare-audit-list';
import {loginGuard} from '@/app/presentation/guards/login.guard';
import {MetricsDashboardComponent} from '@/app/presentation/components/metrics-dashboard/metrics-dashboard.component';

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
      {path: 'audit', component: AuditList},
      {path: 'audit/create', component: AuditForm},
      {path: 'audit/comparisons', component: CompareAuditList},
      {path: 'audit/compare', component: CompareAuditForm},
      {path: 'metrics', component: MetricsDashboardComponent},
    ]
  },
  { path: '**', redirectTo: '/admin' }
];
