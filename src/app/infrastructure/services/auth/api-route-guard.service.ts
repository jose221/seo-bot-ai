import { environment } from '@/environments/environment';
import { Injectable } from '@angular/core';
import {HttpDefaultModel} from '@/app/domain/models/http/http-default.model';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {RouteGuardResponseModel} from '@/app/domain/models/auth/response/route-guard-response.model';
import {RouteGuardRequestModel} from '@/app/domain/models/auth/request/route-guard-request.model';
import {RouteGuardResponseDto} from '@/app/infrastructure/dto/response/route-guard-response.dto';
import {ApiRouteGuardMapper} from '@/app/domain/mappers/auth/api-route-guard.mapper';

@Injectable({
  providedIn: 'root'
})
export class ApiRouteGuardService {
  itemMapper =  new ApiRouteGuardMapper();
  constructor(private httpService: HttpService) {
  }
  async get(): Promise<HttpDefaultModel<RouteGuardResponseModel[]>> {
    let  response = await this.httpService.get<HttpDefaultModel<RouteGuardResponseDto[]>>(environment.endpoints.auth.route_guard.get);
    response.data.map((element: RouteGuardResponseDto) => {
      return this.itemMapper.mapResponse(element);
    })
    return response;
  }

  async getOne(id: string): Promise<HttpDefaultModel<RouteGuardResponseModel>> {
    let response = await this.httpService.get<HttpDefaultModel<RouteGuardResponseDto>>(`${environment.endpoints.auth.route_guard.get_one}/${id}`);
    response.data = this.itemMapper.mapResponse(response.data);
    return response;
  }

  async create(params: RouteGuardRequestModel): Promise<HttpDefaultModel<any>> {

    return await this.httpService.post<HttpDefaultModel<any>>(environment.endpoints.auth.route_guard.create, this.itemMapper.mapRequest(params));
  }
  async update(id: string, params: RouteGuardRequestModel): Promise<HttpDefaultModel<any>> {
    return await this.httpService.put<HttpDefaultModel<any>>(`${environment.endpoints.auth.route_guard.update}/${id}`, this.itemMapper.mapRequest(params));
  }
  async delete(id: string): Promise<HttpDefaultModel<any>> {
    return await this.httpService.delete<HttpDefaultModel<any>>(`${environment.endpoints.auth.route_guard.delete}/${id}`);
  }
}
