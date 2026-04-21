import { inject, PLATFORM_ID } from '@angular/core';
import { CanActivateFn } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';

export const authGuard: CanActivateFn = async (): Promise<boolean> => {
  const authRepository = inject(AuthRepository);
  const platformId = inject(PLATFORM_ID);

  // En SSR, permitir el acceso (la validación real se hará en el cliente)
  if (!isPlatformBrowser(platformId)) {
    return true;
  }

  console.info('[authGuard] validating protected route', { path: window.location.pathname });

  // check-sso: detecta sesión activa de Keycloak sin forzar redirect
  const signedIn = await authRepository.completeSignIn();
  if (signedIn) {
    console.info('[authGuard] Keycloak session detected');
  }

  const isValid = await authRepository.verifyToken();

  if (!isValid) {
    console.error('[authGuard] verifyToken returned false, redirecting to /');
    window.location.href = '/';
    return false;
  }

  const isAuthenticated = authRepository.isAuthenticated();

  if (!isAuthenticated) {
    console.error('[authGuard] token not present, redirecting to /');
    window.location.href = '/';
    return false;
  }

  return true;
};
