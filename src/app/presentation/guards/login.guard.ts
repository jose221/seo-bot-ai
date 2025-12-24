import { inject, PLATFORM_ID } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';

export const loginGuard: CanActivateFn = () => {
  const authRepository = inject(AuthRepository);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);

  // En SSR, permitir el acceso (la validación real se hará en el cliente)
  if (!isPlatformBrowser(platformId)) {
    return true;
  }

  // Verificación solo en el navegador
  if (!authRepository.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/admin']);
};
