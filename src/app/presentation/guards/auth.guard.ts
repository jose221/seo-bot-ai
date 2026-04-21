import { inject, PLATFORM_ID } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';

export const authGuard: CanActivateFn = async (_route, state): Promise<boolean | ReturnType<Router['createUrlTree']>> => {
  const authRepository = inject(AuthRepository);
  const platformId = inject(PLATFORM_ID);
  const router = inject(Router);

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
    return router.createUrlTree(['/'], {
      queryParams: { returnUrl: state.url || '/admin' }
    });
  }

  const isAuthenticated = authRepository.isAuthenticated();

  if (!isAuthenticated) {
    console.error('[authGuard] token not present, redirecting to /');
    return router.createUrlTree(['/'], {
      queryParams: { returnUrl: state.url || '/admin' }
    });
  }

  return true;
};
