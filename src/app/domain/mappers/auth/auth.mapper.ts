import { AppMapper } from "../app.mapper";
import {AuthLoginRequestDto, AuthRegisterRequestDto} from '@/app/infrastructure/dto/request/auth-request.dto';
import {AuthLoginRequestModel, AuthRegisterRequestModel} from '@/app/domain/models/auth/request/auth-request.model';
import {AuthLoginResponseDto, AuthRegisterResponseDto} from '@/app/infrastructure/dto/response/auth-response.dto';
import {AuthLoginResponseModel, AuthRegisterResponseModel} from '@/app/domain/models/auth/response/auth-response.model';
import {environment} from '@/environments/environment';


export class AuthLoginMapper extends AppMapper {
  constructor() {
    super();
  }
  // --------- mapRequest (sobrecargas)
  mapRequest(model: AuthLoginRequestModel): AuthLoginRequestDto;
  mapRequest(input: AuthLoginRequestModel) {
    return this.autoMap<any, any>(input, { except: [], include:{
        expires_in_days: environment.settings.auth.expires_in_days,
        token_name:  environment.settings.auth.token_name,
      } });
  }

  // --------- mapResponse (sobrecargas)
  mapResponse(dto: AuthLoginResponseDto): AuthLoginResponseModel;
  mapResponse(model: AuthLoginResponseModel): AuthLoginResponseDto;
  mapResponse(input: AuthLoginResponseDto | AuthLoginResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}

export class AuthRegisterMapper extends AppMapper {
  constructor() {
    super();
  }
  // --------- mapRequest (sobrecargas)
  mapRequest(dto: AuthRegisterRequestDto): AuthRegisterRequestModel;
  mapRequest(model: AuthRegisterRequestModel): AuthRegisterRequestDto;
  mapRequest(input: AuthRegisterRequestDto | AuthRegisterRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse (sobrecargas)
  mapResponse(dto: AuthRegisterResponseDto): AuthRegisterResponseModel;
  mapResponse(model: AuthRegisterResponseModel): AuthRegisterResponseDto;
  mapResponse(input: AuthRegisterResponseDto | AuthRegisterResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
