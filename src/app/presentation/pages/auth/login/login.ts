import {Component, inject, OnInit, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {TranslateModule} from '@ngx-translate/core';
import {LanguageSelector} from '@/app/presentation/components/general/language-selector/language-selector';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {ActivatedRoute, Router} from '@angular/router';
import {environment} from '@/environments/environment';

@Component({
  selector: 'app-login',
  imports: [
    TranslateModule,
    LanguageSelector,
  ],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login implements OnInit {
  protected readonly error = signal('');
  protected readonly loading = signal(false);
  private readonly authRepository = inject(AuthRepository);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly platformId = inject(PLATFORM_ID);

  private getSafeReturnUrl(): string {
    const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') ?? '/admin';
    return returnUrl.startsWith('/admin') ? returnUrl : '/admin';
  }

  async ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) return;

    const storedAuthError = sessionStorage.getItem('auth:lastError');
    if (storedAuthError) {
      //console.error('[login] last auth diagnostic:', JSON.parse(storedAuthError));
      //sessionStorage.removeItem('auth:lastError');
    }

    this.loading.set(true);
    try {
      const timeout = new Promise<boolean>(resolve => setTimeout(() => resolve(false), 5000));
      const isAuthenticated = await Promise.race([
        this.authRepository.completeSignIn(),
        timeout
      ]);
      if (isAuthenticated) {
        await this.router.navigateByUrl(this.getSafeReturnUrl());
      }
    } catch (e: Error | any) {
      this.error.set(`${e?.response?.statusText ?? e?.name ?? 'Error'} ${e?.message ?? ''}`.trim());
    } finally {
      this.loading.set(false);
    }
  }

  /** Redirige al usuario al formulario de login de Keycloak (SSO). */
  signIn() {
    this.error.set('');
    const returnUrl = this.getSafeReturnUrl();
    const redirectUri = `${window.location.origin}${returnUrl}`;
    console.info('[login] Redirecting to Keycloak', {
      requestedRedirectUri: redirectUri,
      configuredRedirectUri: environment.keycloak.redirectUri,
      returnUrl,
    });
    this.authRepository.signIn(redirectUri);
  }
}
