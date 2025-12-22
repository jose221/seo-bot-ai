import { Routes } from '@angular/router';
import {Login} from '@/app/presentation/pages/auth/login/login';
import {authGuard} from '@/app/presentation/guards/auth.guard';
import {Admin} from '@/app/presentation/pages/admin/admin';
import {TargetList} from '@/app/presentation/pages/admin/target/target-list/target-list';
import {TargetForm} from '@/app/presentation/pages/admin/target/target-form/target-form';
import {AuditList} from '@/app/presentation/pages/admin/audit/audit-list/audit-list';
import {AuditForm} from '@/app/presentation/pages/admin/audit/audit-form/audit-form';

export const routes: Routes = [
  { path: '', component: Login },
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
    ]
  }
];
