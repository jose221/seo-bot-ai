import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';

export const authGuard: CanActivateFn = () => {
  const authRepository = inject(AuthRepository);
  const router = inject(Router);

  if (authRepository.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/']);
};

