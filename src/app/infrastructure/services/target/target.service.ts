import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {TargetMapper} from '@/app/domain/mappers/target/target.mapper';
import {
  CreateTargetRequestModel,
  FilterTargetRequestModel,
  SearchTargetRequestModel
} from '@/app/domain/models/target/request/target-request.model';
import {
  SearchTargetResponseModel,
  TargetResponseModel
} from '@/app/domain/models/target/response/target-response.model';
import {SearchTargetResponseDto, TargetResponseDto} from '@/app/infrastructure/dto/response/target-response.dto';
import {environment} from '@/environments/environment';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {HttpItemsModel} from '@/app/infrastructure/dto/http/http-default.model';
import {BaseService} from '@/app/infrastructure/services/base/base.service';


@Injectable({
  providedIn: 'root'
})
export class TargetService extends BaseService{
  itemMapper = new TargetMapper();
  constructor(private httpService: HttpService) {
    super();
  }

  async create(params: CreateTargetRequestModel): Promise<any> {
    return await this.httpService.post<any>(`${environment.endpoints.target.path}`, this.itemMapper.mapCreate(params), {}, this.getToken);
  }

  async delete(id: number): Promise<any> {
    return await this.httpService.delete<any>(`${environment.endpoints.target.path}/${id}`, {}, this.getToken);
  }

  async get(params?: FilterTargetRequestModel): Promise<TargetResponseModel[]> {
    const response = await this.httpService.get<HttpItemsModel<TargetResponseDto[]>>(`${environment.endpoints.target.path}`, params, {}, this.getToken);
    return response.items.map((item: TargetResponseDto) => this.itemMapper.mapResponse(item));
  }

  async search(params?: SearchTargetRequestModel): Promise<SearchTargetResponseModel[]> {
    const response = await this.httpService.get<HttpItemsModel<SearchTargetResponseDto[]>>(`${environment.endpoints.target.search}`, params ? this.itemMapper.mapSearch(params) : {}, {}, this.getToken);
    return response.items.map((item: SearchTargetResponseDto) => this.itemMapper.mapResponseSearch(item));
  }

  async find(id: number): Promise<TargetResponseModel> {
    const response = await this.httpService.get<TargetResponseDto>(`${environment.endpoints.target.path}/${id}`, {},{}, this.getToken);
    return this.itemMapper.mapResponse(response);
  }
}
