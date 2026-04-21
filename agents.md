# Angular Hexagonal Architecture — Agent Guide

> **Purpose**: This document describes how the seo-bot-ai Angular project is structured following **Hexagonal Architecture (Ports & Adapters)** combined with **Clean Architecture** principles, including the **Keycloak SSO authentication** integration.

---

## 1. Architecture Overview

```
src/app/
├── domain/            ← Business logic (pure, no framework dependencies)
│   ├── models/        ← Business entities (request/response)
│   ├── repositories/  ← Abstract classes (Ports — interfaces)
│   └── mappers/       ← Data transformation between layers
├── infrastructure/    ← Technical implementation (Adapters)
│   ├── dto/           ← Data Transfer Objects (API contracts)
│   ├── repositories/  ← Concrete repository implementations
│   ├── services/      ← HTTP services, external integrations
│   └── http/          ← HTTP interceptors, headers
├── presentation/      ← UI layer (Angular components)
│   ├── pages/         ← Route-level page components
│   ├── components/    ← Reusable general components
│   ├── shared/        ← Abstract base classes for pages/page-components
│   ├── guards/        ← Route guards
│   └── utils/         ← UI utilities (alerts, charts, modals, validation)
├── helper/            ← Cross-cutting utilities (HTTP, pagination, PDF, DOM)
├── pipes/             ← Angular pipes (date formatting, translations, HTML, etc.)
├── app.routes.ts      ← Client-side routing
├── app.routes.server.ts ← SSR render mode configuration
├── app.config.ts      ← DI providers (Port → Adapter bindings)
└── app.config.server.ts ← Server-specific config
```

**Path alias**: `@/*` → `./src/*` (defined in `tsconfig.json`).

---

## 2. Authentication & Keycloak SSO

### 2.1 Overview

Authentication is handled via **Keycloak** (OpenID Connect / OAuth 2.0) using the `keycloak-js` library. The architecture cleanly separates the Keycloak SDK from the rest of the app through the hexagonal pattern:

```
Presentation (Login, Guards)
        │
        ▼
AuthRepository (domain — abstract Port)
        │
        ▼
AuthImplementationRepository (infrastructure — Adapter)
        │
        ├─► KeycloakService   (Keycloak SDK wrapper)
        ├─► CookieService     (token persistence)
        └─► LocalstorageService (user profile cache)
```

### 2.2 Key Files

| File | Layer | Responsibility |
|------|-------|----------------|
| `domain/repositories/auth/auth.repository.ts` | Domain | Abstract contract (Port) |
| `infrastructure/services/auth/keycloak.service.ts` | Infrastructure | Keycloak SDK adapter |
| `infrastructure/repositories/auth/auth.implementation.repository.ts` | Infrastructure | Concrete implementation (Adapter) |
| `presentation/guards/auth.guard.ts` | Presentation | Protects admin routes |
| `presentation/guards/login.guard.ts` | Presentation | Redirects authenticated users |
| `presentation/pages/auth/login/login.ts` | Presentation | SSO login page |
| `public/silent-check-sso.html` | Static | Required for silent check-sso flow |

### 2.3 AuthRepository (Domain Port)

```typescript
export abstract class AuthRepository {
  abstract isAuthenticated(): boolean;
  abstract verifyToken(): Promise<boolean>;      // refresh + validate token
  abstract getToken(): string;
  abstract signIn(): void;                        // redirect to Keycloak login
  abstract completeSignIn(): Promise<boolean>;    // init + persist token
  abstract login(params): Promise<any>;           // legacy form login
  abstract register(params): Promise<any>;
  abstract logout(): void;
  abstract getUser(): any;
}
```

### 2.4 KeycloakService (Infrastructure Adapter)

Wraps `keycloak-js` as a singleton. SSR-safe (all operations check `isPlatformBrowser`).

```typescript
// Initialize Keycloak (check-sso — no forced redirect)
await keycloakService.init(): Promise<boolean>

// Redirect to Keycloak login form
keycloakService.login(redirectUri?: string): void

// Logout and redirect
keycloakService.logout(redirectUri?: string): void

// Get fresh token (auto-refresh if <30s to expire)
await keycloakService.getToken(): Promise<string | null>

// Synchronous token access (no refresh)
keycloakService.getTokenSync(): string | null

// Authentication state
keycloakService.isAuthenticated(): boolean

// Decoded token payload (user profile)
keycloakService.getUserProfile(): Record<string, unknown> | null

// Role checks
keycloakService.hasRealmRole(role: string): boolean
keycloakService.hasResourceRole(role: string, resource?: string): boolean
```

### 2.5 AuthImplementationRepository (Infrastructure Adapter)

Implements `AuthRepository`. Coordinates `KeycloakService`, `CookieService`, and `LocalstorageService`.

**Key methods:**

| Method | Description |
|--------|-------------|
| `signIn()` | Delegates to `keycloakService.login()` |
| `completeSignIn()` | Calls `keycloakService.init()`, persists token + profile if authenticated |
| `verifyToken()` | Refreshes Keycloak token, updates cookie, returns validity |
| `isAuthenticated()` | Checks Keycloak state first, falls back to cookie |
| `getToken()` | Returns Keycloak token if available, falls back to cookie |
| `logout()` | Clears cookie + localStorage, calls `keycloakService.logout()` |

### 2.6 Authentication Flow

```
User visits /                     User visits /admin
       │                                  │
       ▼                                  ▼
  loginGuard                         authGuard
       │                                  │
  isAuthenticated?          completeSignIn() ──► Keycloak check-sso
       │                                  │
  YES → /admin              verifyToken() ──► refresh token
  NO  → show Login                       │
       │                            isAuthenticated?
       ▼                                  │
  Login page (ngOnInit)            YES → allow
  completeSignIn()                 NO  → redirect /
  authenticated? → /admin
  NO → show SSO button
       │
       ▼
  signIn() → Keycloak login form
       │
  Keycloak redirects back to app
       │
       ▼
  Login page (ngOnInit again)
  completeSignIn() returns true
  → navigate /admin
```

### 2.7 Silent Check SSO

`public/silent-check-sso.html` must be served as a static asset. Keycloak loads it in a hidden iframe to silently detect an existing session without page redirects.

```html
<!-- public/silent-check-sso.html -->
<script>parent.postMessage(location.href, location.origin);</script>
```

The URL is configured in `KeycloakService.init()`:
```typescript
silentCheckSsoRedirectUri: `${window.location.origin}/assets/silent-check-sso.html`
```

> ⚠️ When using Angular SSR with `dist/browser/`, ensure `silent-check-sso.html` is present in the served assets root.

### 2.8 Keycloak Configuration (Environment)

```typescript
// src/environments/environment.ts
keycloak: {
  url: 'https://auth-keycloak.herandro.com.mx',  // Keycloak server URL
  realm: 'herandro',                               // Realm name
  clientId: 'seo-bot-ai-web',                     // Public client ID
  redirectUri: 'http://localhost:4200/admin',      // Post-login redirect
  postLogoutRedirectUri: 'http://localhost:4200/', // Post-logout redirect
}
```

> 📝 The Keycloak client must be configured as **public** (no secret) with the `redirectUri` registered as a valid redirect URI in the Keycloak admin console.

---

## 3. Domain Layer

### 3.1 Models (`domain/models/{module}/`)

Business entities separated into:
- **`request/`** — Models for create, update, and filter operations.
- **`response/`** — Models representing the data returned from the API.

**Convention**: Models are **classes** (not interfaces).

### 3.2 Repositories (`domain/repositories/{module}/`)

**Abstract classes** acting as **Ports**. The presentation layer **only** injects these, never the implementation.

```typescript
export abstract class XxxRepository {
  abstract create(params: CreateXxxRequestModel): Promise<any>;
  abstract update(id: number, params: UpdateXxxRequestModel): Promise<any>;
  abstract delete(id: number): Promise<any>;
  abstract get(params?: FilterXxxRequestModel): Promise<XxxResponseModel[]>;
  abstract find(id: number): Promise<XxxResponseModel>;
}
```

### 3.3 Mappers (`domain/mappers/{module}/`)

Transform data between **Domain Models ↔ DTOs**. Extend `AppMapper` which provides:
- `autoMap<T, U>()` — automatic property mapping
- `pipeFrom<T>()` / `pipeTo<T>()` — selective property copying
- `pipeData<T, U>()` — constructor-based mapping

---

## 4. Infrastructure Layer

### 4.1 Services (`infrastructure/services/`)

```
infrastructure/services/
├── auth/
│   ├── auth.service.ts          → HTTP auth calls (login, register)
│   └── keycloak.service.ts      → Keycloak SDK wrapper (SSO)
├── base/
│   └── base.service.ts          → Token injection via AuthRepository
├── general/
│   ├── http.service.ts          → Axios-based HTTP client
│   ├── cookie.service.ts        → Cookie management
│   └── localstorage.service.ts  → LocalStorage management
├── monitoring/
│   └── prometheus.service.ts    → Prometheus metrics
└── {module}/
    └── {module}.service.ts      → Module-specific HTTP calls
```

### 4.2 Implementation Repositories (`infrastructure/repositories/{module}/`)

Concrete Adapters implementing domain repository contracts. Delegate to corresponding services.

```typescript
@Injectable({ providedIn: 'root' })
export class XxxImplementationRepository implements XxxRepository {
  constructor(private primaryService: XxxService) {}
}
```

---

## 5. Presentation Layer

### 5.1 Guards (`presentation/guards/`)

| Guard | Purpose |
|-------|---------|
| `auth.guard.ts` | Protects `/admin/**` — runs Keycloak check-sso + verifyToken |
| `login.guard.ts` | On `/` — redirects authenticated users to `/admin` |

Both guards are SSR-safe: they return `true` immediately on the server and only perform Keycloak checks in the browser.

### 5.2 Route Configuration (`app.routes.ts`)

```typescript
{ path: '', component: Login, canActivate: [loginGuard] },
{ path: 'admin', component: Admin, canActivate: [authGuard], children: [...] },
```

---

## 6. DI Bindings (`app.config.ts`)

Port → Adapter bindings are declared in `app.config.ts`:

```typescript
{ provide: AuthRepository, useClass: AuthImplementationRepository }
```

`KeycloakService` is `providedIn: 'root'` and requires no explicit binding.

---

## 7. Adding a New Module

1. **Domain**: Create `models/`, `repositories/`, `mappers/` under `domain/{module}/`
2. **Infrastructure**: Create `dto/`, `services/`, `repositories/` under `infrastructure/{module}/`
3. **Presentation**: Create page/component under `presentation/pages/`
4. **Register**: Add `{ provide: XxxRepository, useClass: XxxImplementationRepository }` in `app.config.ts`
5. **Route**: Add route in `app.routes.ts` with `canActivate: [authGuard]` if protected
