import { environment } from '@/environments/environment';
import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {AuthLoginMapper, AuthRegisterMapper} from '@/app/domain/mappers/auth/auth.mapper';
import {AuthLoginRequestModel, AuthRegisterRequestModel} from '@/app/domain/models/auth/request/auth-request.model';
import {AuthLoginResponseModel, AuthRegisterResponseModel} from '@/app/domain/models/auth/response/auth-response.model';
import {AuthLoginResponseDto, AuthRegisterResponseDto} from '@/app/infrastructure/dto/response/auth-response.dto';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  itemLoginMapper =  new AuthLoginMapper();
  itemRegisterMapper =  new AuthRegisterMapper();
  constructor(private httpService: HttpService) {
  }
  async login(params: AuthLoginRequestModel): Promise<AuthLoginResponseModel> {
    let  response = await this.httpService.post<AuthLoginResponseDto>(environment.endpoints.auth.login, this.itemLoginMapper.mapRequest(params));
    return this.itemLoginMapper.mapResponse(response);
  }
  async register(params: AuthRegisterRequestModel): Promise<AuthRegisterResponseModel> {
    let  response = await this.httpService.post<AuthRegisterResponseDto>(environment.endpoints.auth.login, this.itemRegisterMapper.mapRequest(params));
    return this.itemRegisterMapper.mapResponse(response);
  }
}
