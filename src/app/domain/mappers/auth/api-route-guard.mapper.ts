import { AppMapper } from "../app.mapper";
import {RouteGuardRequestDto} from '@/app/infrastructure/dto/request/route-guard-request.dto';
import {RouteGuardRequestModel} from '@/app/domain/models/auth/request/route-guard-request.model';
import {RouteGuardResponseDto} from '@/app/infrastructure/dto/response/route-guard-response.dto';
import {RouteGuardResponseModel} from '@/app/domain/models/auth/response/route-guard-response.model';


export class ApiRouteGuardMapper extends AppMapper {
  constructor() {
    super();
  }
  // --------- mapRequest (sobrecargas)
  mapRequest(dto: RouteGuardRequestDto): RouteGuardRequestModel;
  mapRequest(model: RouteGuardRequestModel): RouteGuardRequestDto;
  mapRequest(input: RouteGuardRequestDto | RouteGuardRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse (sobrecargas)
  mapResponse(dto: RouteGuardResponseDto): RouteGuardResponseModel;
  mapResponse(model: RouteGuardResponseModel): RouteGuardResponseDto;
  mapResponse(input: RouteGuardResponseDto | RouteGuardResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
