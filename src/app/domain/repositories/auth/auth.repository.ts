import {AuthLoginRequestModel, AuthRegisterRequestModel} from '@/app/domain/models/auth/request/auth-request.model';
import {AuthLoginResponseModel, AuthRegisterResponseModel} from '@/app/domain/models/auth/response/auth-response.model';

export abstract class AuthRepository {
  abstract isAuthenticated(): boolean;
  /** Verifica que el token sea válido (refresco Keycloak incluido). */
  abstract verifyToken(): Promise<boolean>;
  public abstract getToken(): string;
  /** Redirige al proveedor de identidad (Keycloak) para iniciar sesión. */
  abstract signIn(): void;
  /** Completa el flujo de sign-in: inicializa Keycloak y persiste el token. */
  abstract completeSignIn(): Promise<boolean>;
  abstract login(params: AuthLoginRequestModel): Promise<AuthLoginResponseModel|any>;
  abstract register(params: AuthRegisterRequestModel): Promise<AuthRegisterResponseModel>;
  abstract logout(): void;
  abstract getUser(): AuthRegisterResponseModel;
}
