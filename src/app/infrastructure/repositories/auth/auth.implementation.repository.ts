import { inject, Injectable, PLATFORM_ID } from '@angular/core';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {AuthLoginResponseModel, AuthRegisterResponseModel} from '@/app/domain/models/auth/response/auth-response.model';
import {AuthLoginRequestModel, AuthRegisterRequestModel} from '@/app/domain/models/auth/request/auth-request.model';
import {AuthService} from '@/app/infrastructure/services/auth/auth.service';
import {CookieService} from '@/app/infrastructure/services/general/cookie.service';
import {environment} from '@/environments/environment';
import {LocalstorageService} from '@/app/infrastructure/services/general/localstorage.service';
import {KeycloakService} from '@/app/infrastructure/services/auth/keycloak.service';
import {isPlatformBrowser} from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class AuthImplementationRepository implements AuthRepository {
  private readonly accessTokenKey = 'auth.access_token';
  private readonly userKey = 'auth.user';
  private readonly platformId = inject(PLATFORM_ID);
  private readonly keycloakService = inject(KeycloakService);

  constructor(
    private primaryService: AuthService,
    private cookieService: CookieService,
    private localstorageService: LocalstorageService
  ) {}

  /** Persiste detalles del último error de auth para diagnóstico en la pantalla de login. */
  private storeAuthDebug(reason: string, details?: unknown): void {
    if (!isPlatformBrowser(this.platformId)) return;
    const payload = { reason, details, at: new Date().toISOString() };
    sessionStorage.setItem('auth:lastError', JSON.stringify(payload));
    console.error('[auth]', payload);
  }

  /** Redirige al usuario al formulario de login de Keycloak. */
  signIn(): void {
    if (!isPlatformBrowser(this.platformId)) return;
    this.keycloakService.login();
  }

  /**
   * Inicializa Keycloak (check-sso) y, si el usuario está autenticado,
   * persiste el token en cookie y el perfil en localStorage.
   */
  async completeSignIn(): Promise<boolean> {
    if (!isPlatformBrowser(this.platformId)) return false;

    try {
      const authenticated = await this.keycloakService.init();

      if (!authenticated) {
        this.storeAuthDebug('Keycloak init did not authenticate user');
        return false;
      }

      const accessToken = await this.keycloakService.getToken();

      if (!accessToken) {
        this.storeAuthDebug('Keycloak authenticated but no access token was returned');
        return false;
      }

      this.cookieService.set(this.accessTokenKey, accessToken, environment.settings.auth.expires_in_days);

      const userProfile = this.keycloakService.getUserProfile();
      this.localstorageService.set(
        this.userKey,
        userProfile ?? {},
        environment.settings.auth.expires_in_days
      );

      console.info('[auth] Keycloak sign-in completed', {
        isAuthenticated: authenticated,
        hasAccessToken: !!accessToken,
        hasUserData: !!userProfile
      });

      return true;
    } catch (error) {
      this.storeAuthDebug('Error while processing Keycloak sign-in', error);
      return false;
    }
  }

  async login(params: AuthLoginRequestModel): Promise<AuthLoginResponseModel> {
    const response = await this.primaryService.login(params);
    if (response?.access_token) {
      this.cookieService.set(this.accessTokenKey, response.access_token, environment.settings.auth.expires_in_days);
      this.localstorageService.set(this.userKey, {
        user_id: response.user_id,
        user_email: response.user_email,
        user_name: response.user_name,
        tenant_id: response.tenant_id,
        project_id: response.project_id,
        scope: response.scope
      }, environment.settings.auth.expires_in_days);
    }
    return response;
  }

  async register(params: AuthRegisterRequestModel): Promise<AuthRegisterResponseModel> {
    return await this.primaryService.register(params);
  }

  logout(): void {
    this.cookieService.remove(this.accessTokenKey);
    this.localstorageService.remove(this.userKey);
    this.keycloakService.logout();
  }

  getUser(): AuthRegisterResponseModel {
    return this.localstorageService.get(this.userKey) as AuthRegisterResponseModel;
  }

  isAuthenticated(): boolean {
    if (this.keycloakService.isAuthenticated()) return true;
    return this.cookieService.get(this.accessTokenKey) !== null;
  }

  getToken(): string {
    // Preferir token Keycloak (siempre actualizado), fallback a cookie
    const kcToken = this.keycloakService.getTokenSync();
    if (kcToken) return kcToken;
    return this.cookieService.get(this.accessTokenKey) as string;
  }

  /**
   * Verifica que el token sea válido intentando un refresco desde Keycloak.
   * Actualiza la cookie si obtiene un token fresco.
   */
  async verifyToken(): Promise<boolean> {
    try {
      const freshToken = await this.keycloakService.getToken();
      if (freshToken) {
        this.cookieService.set(this.accessTokenKey, freshToken, environment.settings.auth.expires_in_days);
        return true;
      }

      // Fallback: verificar si hay token almacenado en cookie
      const storedToken = this.cookieService.get(this.accessTokenKey);
      if (!storedToken) {
        this.storeAuthDebug('No token found in Keycloak or cookie');
        return false;
      }

      return true;
    } catch (e) {
      this.storeAuthDebug('Token verification failed', e);
      return false;
    }
  }
}
