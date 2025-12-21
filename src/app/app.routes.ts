import { Routes } from '@angular/router';
import {Login} from '@/app/presentation/pages/auth/login/login';
import {authGuard} from '@/app/presentation/guards/auth.guard';
import {Admin} from '@/app/presentation/pages/admin/admin';
import {Target} from '@/app/presentation/pages/admin/target/target';

export const routes: Routes = [
  { path: '', component: Login },
  {
    path: 'admin',
    component: Admin,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'target', pathMatch: 'full' },
      {path: 'target', component: Target},
    ]
  }
];
