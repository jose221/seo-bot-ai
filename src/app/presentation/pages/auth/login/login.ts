import {Component, inject, OnInit, signal} from '@angular/core';
import {TranslateModule} from '@ngx-translate/core';
import {LanguageSelector} from '@/app/presentation/components/general/language-selector/language-selector';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {Router} from '@angular/router';

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

  async ngOnInit() {
    if (typeof window !== 'undefined') {
      // Mostrar y limpiar cualquier diagnóstico previo de auth
      const storedAuthError = sessionStorage.getItem('auth:lastError');
      if (storedAuthError) {
        console.error('[login] last auth diagnostic:', JSON.parse(storedAuthError));
        sessionStorage.removeItem('auth:lastError');
      }
    }

    this.loading.set(true);
    try {
      // Intentar completar sign-in silencioso (Keycloak check-sso)
      const isAuthenticated = await this.authRepository.completeSignIn();
      if (isAuthenticated) {
        await this.router.navigateByUrl('/admin');
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
    this.authRepository.signIn();
  }
}
