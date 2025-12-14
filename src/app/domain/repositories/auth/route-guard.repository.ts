import {HttpDefaultModel} from '@/app/domain/models/http/http-default.model';
import {RouteGuardResponseModel} from '@/app/domain/models/auth/response/route-guard-response.model';
import {RouteGuardRequestModel} from '@/app/domain/models/auth/request/route-guard-request.model';

export abstract class RouteGuardRepository {
  abstract get(): Promise<HttpDefaultModel<RouteGuardResponseModel[]>>;
  abstract getOne(id: string): Promise<HttpDefaultModel<RouteGuardResponseModel>>;
  abstract create(params: RouteGuardRequestModel): Promise<HttpDefaultModel<any>>;
  abstract update(id: string, params: RouteGuardRequestModel): Promise<HttpDefaultModel<any>>;
  abstract delete(id: string): Promise<HttpDefaultModel<any>>;
}
