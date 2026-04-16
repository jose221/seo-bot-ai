import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {TargetMapper} from '@/app/domain/mappers/target/target.mapper';
import {
  CreateTargetRequestModel,
  FilterTargetRequestModel,
  SearchTargetRequestModel,
  UpdateTargetRequestModel
} from '@/app/domain/models/target/request/target-request.model';
import {
  SearchTargetResponseModel,
  TargetHtmlResponseModel,
  TargetResponseModel
} from '@/app/domain/models/target/response/target-response.model';
import {SearchTargetResponseDto, TargetHtmlResponseDto, TargetResponseDto} from '@/app/infrastructure/dto/response/target-response.dto';
import {environment} from '@/environments/environment';
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

  async update(id: string, params: UpdateTargetRequestModel): Promise<any> {
    return await this.httpService.patch<any>(`${environment.endpoints.target.path}/${id}`, this.itemMapper.mapUpdate(params), {}, this.getToken);
  }

  async delete(id: string): Promise<any> {
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

  async find(id: string): Promise<TargetResponseModel> {
    const response = await this.httpService.get<TargetResponseDto>(`${environment.endpoints.target.path}/${id}`, {},{}, this.getToken);
    return this.itemMapper.mapResponse(response);
  }

  async getTags(): Promise<string[]> {
    const response = await this.httpService.get<{ tags: string[]; total: number }>(`${environment.endpoints.target.tags}`, {}, {}, this.getToken);
    return response.tags ?? [];
  }

  async getHtml(url: string): Promise<TargetHtmlResponseModel> {
    const encodedUrl = encodeURIComponent(url);
    const response = await this.httpService.get<TargetHtmlResponseDto>(`${environment.endpoints.target.path}/html/${encodedUrl}`, {}, {});
    return new TargetHtmlResponseModel(response.target_id, response.url, response.html, response.source, response.html_length);
  }
}
