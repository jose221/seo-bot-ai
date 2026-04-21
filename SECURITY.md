# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of this project seriously. If you find a security vulnerability, please do **NOT** open a public issue.

### How to report
Send an email to **[your-email@domain.com]** with the details of the vulnerability.

### What to expect
* **Acknowledgment:** Response within 48 hours.
* **Status Updates:** Weekly progress updates.
* **Disclosure:** A patch release and security advisory will be published once the issue is resolved.

### Disclosure Policy
Please practice **responsible disclosure** — give us reasonable time to fix the issue before making it public.

---

## Authentication & Authorization — Keycloak SSO

### Overview

Authentication is delegated to **Keycloak** (OpenID Connect / OAuth 2.0). The frontend does **not** handle passwords directly. Credentials are managed exclusively by the Keycloak identity provider.

### Authentication Flow

1. User clicks "Sign in with SSO" on the login page.
2. The app calls `KeycloakService.login()`, which redirects to the Keycloak login form.
3. After successful authentication, Keycloak redirects back to the configured `redirectUri` with an authorization code.
4. `keycloak-js` completes the PKCE flow and obtains an access token.
5. The token is stored in a cookie (`auth.access_token`) and the decoded profile in `localStorage`.
6. On every protected route visit, `authGuard` calls `completeSignIn()` (silent check-sso) and `verifyToken()` (token refresh) before allowing access.

### Security Measures

| Measure | Details |
|---------|---------|
| **PKCE** | `pkceMethod: 'S256'` — prevents authorization code interception attacks |
| **Silent SSO** | Uses hidden iframe with `silent-check-sso.html` — no full redirects for session detection |
| **Token auto-refresh** | `onTokenExpired` triggers automatic renewal via `updateToken(70)` |
| **SSR safety** | All Keycloak operations check `isPlatformBrowser` — no SDK calls on the server |
| **No iframe login** | `checkLoginIframe: false` — avoids CSRF risks from the login iframe |
| **Token storage** | Access token stored in a cookie with configurable expiry (`expires_in_days`) |
| **Error diagnostics** | Auth errors are stored in `sessionStorage['auth:lastError']` for debugging (cleared on login page load) |

### Keycloak Client Requirements

Configure the Keycloak client with these settings:

- **Client type**: Public (no client secret)
- **Valid redirect URIs**: `http://localhost:4200/*` (dev), `https://seo-bot-ai.herandro.com.mx/*` (prod)
- **Web origins**: `+` (same as redirect URIs) to enable CORS
- **Standard flow**: Enabled
- **Direct access grants**: Disabled (no password grant)
- **PKCE enforced**: Enabled (recommended in Keycloak realm settings)

### Token Handling

```
Access token  → cookie `auth.access_token` (HttpOnly not applicable for JS cookies — see note)
User profile  → localStorage `auth.user`
```

> **Note**: The access token cookie is accessible via JavaScript (`document.cookie`) since it needs to be read by the Angular app. For additional protection, consider implementing a backend-for-frontend (BFF) pattern where tokens are stored server-side and a session cookie is used.

### Logout

Calling `authRepository.logout()`:
1. Removes the token cookie and localStorage entry.
2. Calls `keycloakService.logout()` which invalidates the Keycloak session and redirects to `postLogoutRedirectUri`.

### Role-Based Access Control (RBAC)

`KeycloakService` exposes role-checking methods:

```typescript
keycloakService.hasRealmRole('admin')                     // realm-level role
keycloakService.hasResourceRole('editor', 'my-client')    // resource-level role
```

Use these in guards or components to enforce fine-grained access control.

### Environment Configuration

Keycloak URLs and client IDs are configured per environment:

```typescript
// environment.ts (development)
keycloak: {
  url: 'https://auth-keycloak.herandro.com.mx',
  realm: 'herandro',
  clientId: 'seo-bot-ai-web',
  redirectUri: 'http://localhost:4200/admin',
  postLogoutRedirectUri: 'http://localhost:4200/',
}

// environment.prod.ts (production)
keycloak: {
  url: 'https://auth-keycloak.herandro.com.mx',
  realm: 'herandro',
  clientId: 'seo-bot-ai-web',
  redirectUri: 'https://seo-bot-ai.herandro.com.mx/admin',
  postLogoutRedirectUri: 'https://seo-bot-ai.herandro.com.mx/',
}
```

> ⚠️ Never commit real production secrets (client secrets, passwords) to source control. For confidential Keycloak clients, use environment variables injected at runtime.
