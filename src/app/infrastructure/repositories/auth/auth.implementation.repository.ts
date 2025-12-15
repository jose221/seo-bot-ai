import { Injectable } from '@angular/core';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {AuthLoginResponseModel, AuthRegisterResponseModel} from '@/app/domain/models/auth/response/auth-response.model';
import {AuthLoginRequestModel, AuthRegisterRequestModel} from '@/app/domain/models/auth/request/auth-request.model';
import {AuthService} from '@/app/infrastructure/services/auth/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthImplementationRepository implements AuthRepository {
  constructor(private primaryService: AuthService) {

  }
  async login(params: AuthLoginRequestModel): Promise<AuthLoginResponseModel> {
    return await this.primaryService.login(params);
  }
  async register(params: AuthRegisterRequestModel): Promise<AuthRegisterResponseModel> {
    return await this.primaryService.register(params);
  }
}
