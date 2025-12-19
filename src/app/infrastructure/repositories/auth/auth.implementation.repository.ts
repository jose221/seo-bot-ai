import { Injectable } from '@angular/core';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {AuthLoginResponseModel, AuthRegisterResponseModel} from '@/app/domain/models/auth/response/auth-response.model';
import {AuthLoginRequestModel, AuthRegisterRequestModel} from '@/app/domain/models/auth/request/auth-request.model';
import {AuthService} from '@/app/infrastructure/services/auth/auth.service';
import {CookieService} from '@/app/infrastructure/services/general/cookie.service';
import {environment} from '@/environments/environment';
import {LocalstorageService} from '@/app/infrastructure/services/general/localstorage.service';

@Injectable({
  providedIn: 'root'
})
export class AuthImplementationRepository implements AuthRepository {
  private accessTokenKey: string = "auth.access_token"
  private userKey: string = "auth.user"
  constructor(private primaryService: AuthService,
              private cookieService: CookieService,
              private localstorageService: LocalstorageService) {

  }
  async login(params: AuthLoginRequestModel): Promise<AuthLoginResponseModel> {
    const response= await this.primaryService.login(params)
    if(response?.access_token){
      this.cookieService.set(this.accessTokenKey, response?.access_token, environment.settings.auth.expires_in_days)
      this.localstorageService.set(this.userKey, {
        user_id: response.user_id,
        user_email: response.user_email,
        user_name: response.user_name,
        tenant_id: response.tenant_id,
        project_id: response.project_id,
        scope: response.scope
      }, environment.settings.auth.expires_in_days)
    }
    return response;
  }
  async register(params: AuthRegisterRequestModel): Promise<AuthRegisterResponseModel> {
    return await this.primaryService.register(params);
  }
  logout(): void{
    this.cookieService.remove(this.accessTokenKey)
    this.localstorageService.remove(this.userKey)
  }
  getUser(): AuthRegisterResponseModel{
    return this.localstorageService.get(this.userKey) as AuthRegisterResponseModel
  }

  isAuthenticated(): boolean {
    return this.cookieService.get(this.accessTokenKey) !== null;
  }
  getToken(): string {
    return this.cookieService.get(this.accessTokenKey) as string;
  }
}
