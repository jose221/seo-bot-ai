import { inject, PLATFORM_ID } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';

export const loginGuard: CanActivateFn = async (): Promise<boolean | any> => {
  const authRepository = inject(AuthRepository);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);

  // En SSR, permitir el acceso (la validación real se hará en el cliente)
  if (!isPlatformBrowser(platformId)) {
    return true;
  }

  // Si ya hay sesión activa, redirigir al área protegida
  if (authRepository.isAuthenticated()) {
    return router.createUrlTree(['/admin']);
  }

  return true;
};
