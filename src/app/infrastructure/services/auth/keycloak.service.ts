import { inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import Keycloak from 'keycloak-js';
import { environment } from '@/environments/environment';

/**
 * KeycloakService — Adapter de infraestructura para Keycloak.
 *
 * Encapsula toda la interacción con `keycloak-js`:
 *   - Inicialización (init con check-sso / login-required)
 *   - Login / Logout
 *   - Obtención y refresco de token
 *   - Información del usuario autenticado
 *
 * Diseñado como singleton (`providedIn: 'root'`).
 * Seguro en SSR: cada operación verifica `isPlatformBrowser` antes de tocar el SDK.
 */
@Injectable({
  providedIn: 'root'
})
export class KeycloakService {
  private keycloak: Keycloak | null = null;
  private readonly platformId = inject(PLATFORM_ID);
  private _initialized = false;

  private hasAuthCallbackParams(): boolean {
    if (!this.isBrowser) return false;
    const url = window.location.href;
    return url.includes('code=') || url.includes('state=') || url.includes('error=');
  }

  /** Devuelve `true` si estamos en el navegador */
  private get isBrowser(): boolean {
    return isPlatformBrowser(this.platformId);
  }

  /**
   * Inicializa Keycloak con la configuración del environment.
   * Usa `check-sso` para verificar sesión activa sin forzar redirect.
   *
   * @returns `true` si el usuario ya está autenticado.
   */
  async init(): Promise<boolean> {
    if (!this.isBrowser) return false;

    const hasAuthCallback = this.hasAuthCallbackParams();

    if (this._initialized && this.keycloak && !hasAuthCallback) {
      return this.keycloak.authenticated ?? false;
    }

    const kcConfig = environment.keycloak;

    // Si venimos del callback de login, recreamos la instancia para evitar
    // quedarnos con un estado "no autenticado" cacheado.
    if (!this.keycloak || hasAuthCallback) {
      this.keycloak = new Keycloak({
        url: kcConfig.url,
        realm: kcConfig.realm,
        clientId: kcConfig.clientId,
      });
      this._initialized = false;
    }

    try {
      const authenticated = await this.keycloak.init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: this.isBrowser
          ? `${window.location.origin}/assets/silent-check-sso.html`
          : undefined,
        pkceMethod: 'S256',
        checkLoginIframe: false,
      });

      this._initialized = true;

      // Auto-refresh del token antes de que expire
      this.keycloak.onTokenExpired = () => {
        this.refreshToken();
      };

      return authenticated;
    } catch (error) {
      console.error('[KeycloakService] init failed', error);
      this._initialized = false;
      return false;
    }
  }

  /**
   * Redirige al usuario al formulario de login de Keycloak.
   * @param redirectUri URL a la que Keycloak redirigirá después del login.
   */
  login(redirectUri?: string): void {
    if (!this.isBrowser || !this.keycloak) return;

    const uri = redirectUri ?? environment.keycloak.redirectUri;
    this.keycloak.login({ redirectUri: uri });
  }

  /**
   * Cierra la sesión en Keycloak y redirige al usuario.
   * @param redirectUri URL a la que Keycloak redirigirá después del logout.
   */
  logout(redirectUri?: string): void {
    if (!this.isBrowser || !this.keycloak) return;

    const uri = redirectUri ?? environment.keycloak.postLogoutRedirectUri;
    this.keycloak.logout({ redirectUri: uri });
  }

  /**
   * Devuelve el access token actual.
   * Si el token está por expirar (menos de 30s), intenta refrescarlo primero.
   */
  async getToken(): Promise<string | null> {
    if (!this.isBrowser || !this.keycloak) return null;

    try {
      await this.keycloak.updateToken(30);
      return this.keycloak.token ?? null;
    } catch {
      console.warn('[KeycloakService] token refresh failed');
      return this.keycloak.token ?? null;
    }
  }

  /** Devuelve el token actual de forma sincrónica (sin refresh). */
  getTokenSync(): string | null {
    if (!this.isBrowser || !this.keycloak) return null;
    return this.keycloak.token ?? null;
  }

  /** Devuelve `true` si el usuario está autenticado. */
  isAuthenticated(): boolean {
    if (!this.isBrowser || !this.keycloak) return false;
    return this.keycloak.authenticated ?? false;
  }

  /** Devuelve el perfil de usuario decodificado del token. */
  getUserProfile(): Record<string, unknown> | null {
    if (!this.isBrowser || !this.keycloak?.tokenParsed) return null;
    return this.keycloak.tokenParsed as Record<string, unknown>;
  }

  /** Verifica si el usuario tiene un rol de realm específico. */
  hasRealmRole(role: string): boolean {
    if (!this.keycloak) return false;
    return this.keycloak.hasRealmRole(role);
  }

  /** Verifica si el usuario tiene un rol de recurso específico. */
  hasResourceRole(role: string, resource?: string): boolean {
    if (!this.keycloak) return false;
    return this.keycloak.hasResourceRole(role, resource);
  }

  /** Intenta refrescar el token. */
  private async refreshToken(): Promise<void> {
    if (!this.keycloak) return;
    try {
      await this.keycloak.updateToken(70);
    } catch (error) {
      console.error('[KeycloakService] token refresh failed', error);
    }
  }
}
