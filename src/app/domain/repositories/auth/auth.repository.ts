import {AuthLoginRequestModel, AuthRegisterRequestModel} from '@/app/domain/models/auth/request/auth-request.model';
import {AuthLoginResponseModel, AuthRegisterResponseModel} from '@/app/domain/models/auth/response/auth-response.model';

export abstract class AuthRepository {
  abstract login(params: AuthLoginRequestModel): Promise<AuthLoginResponseModel>;
  abstract register(params: AuthRegisterRequestModel): Promise<AuthRegisterResponseModel>;
}
