import { Injectable } from '@angular/core';
import {HttpDefaultModel} from '@/app/domain/models/http/http-default.model';
import {RouteGuardRepository} from '@/app/domain/repositories/auth/route-guard.repository';
import {RouteGuardResponseModel} from '@/app/domain/models/auth/response/route-guard-response.model';
import {RouteGuardRequestModel} from '@/app/domain/models/auth/request/route-guard-request.model';
import {ApiRouteGuardService} from '@/app/infrastructure/services/auth/api-route-guard.service';

@Injectable({
  providedIn: 'root'
})
export class ApiRouteGuardImplementationRepository extends RouteGuardRepository {
  constructor(private primaryService: ApiRouteGuardService) {
    super();
  }
  async get(): Promise<HttpDefaultModel<RouteGuardResponseModel[]>> {
    return await this.primaryService.get();
  }

  async getOne(id: string): Promise<HttpDefaultModel<RouteGuardResponseModel>> {
    return await this.primaryService.getOne(id);
  }

  async create(params: RouteGuardRequestModel): Promise<HttpDefaultModel<any>> {
    return await this.primaryService.create(params);
  }
  async update(id: string, params: RouteGuardRequestModel): Promise<HttpDefaultModel<any>> {
    return await this.primaryService.update(id, params);
  }
  async delete(id: string): Promise<HttpDefaultModel<any>> {
    return await this.primaryService.delete(id);
  }
}
