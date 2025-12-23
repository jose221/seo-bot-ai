import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {AuditMapper} from '@/app/domain/mappers/audit/audit.mapper';
import {
  CompareAuditRequestModel,
  CreateAuditRequestModel,
  FilterAuditRequestModel, SearchAuditRequestModel
} from '@/app/domain/models/audit/request/audit-request.model';
import {
  AuditResponseModel,
  CompareAuditResponseModel,
  CreateAuditResponseModel, SearchAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';
import {
  AuditResponseDto,
  CompareAuditResponseDto,
  CreateAuditResponseDto, SearchAuditResponseDto
} from '@/app/infrastructure/dto/response/audit-response.dto';
import {HttpClientHelper} from '@/app/helper/http-client.helper';
import {environment} from '@/environments/environment';
import {HttpItemsModel} from '@/app/infrastructure/dto/http/http-default.model';
import {BaseService} from '@/app/infrastructure/services/base/base.service';
import {SearchAuditRequestDto} from '@/app/infrastructure/dto/request/audit-request.dto';


@Injectable({
  providedIn: 'root'
})
export class AuditService extends BaseService{
  itemMapper = new AuditMapper();
  constructor(private httpService: HttpService) {
    super();
  }

  async create(params: CreateAuditRequestModel): Promise<CreateAuditResponseModel> {
    const response = await this.httpService.post<CreateAuditResponseDto>(`${environment.endpoints.audit.path}`, this.itemMapper.mapCreate(params), {}, this.getToken)
    return this.itemMapper.mapResponseCreate(response);
  }

  async delete(id: string): Promise<any> {
    return await this.httpService.delete<any>(`${environment.endpoints.audit.path}/${id}`, {}, this.getToken);
  }

  async get(params?: FilterAuditRequestModel): Promise<AuditResponseModel[]> {
    const response = await this.httpService.get<HttpItemsModel<AuditResponseDto[]>>(`${environment.endpoints.audit.path}`, params ? this.itemMapper.mapFilter(params):{}, {}, this.getToken);
    return response.items.map((item: AuditResponseDto) => this.itemMapper.mapResponse(item));
  }

  async find(id: string): Promise<AuditResponseModel> {
    const response = await this.httpService.get<AuditResponseDto>(`${environment.endpoints.audit.path}/${id}`, {},{}, this.getToken);
    return this.itemMapper.mapResponse(response);
  }

  async compare(params: CompareAuditRequestModel): Promise<CompareAuditResponseModel>{
    const response = await this.httpService.post<CompareAuditResponseDto>(`${environment.endpoints.audit.compare}`, this.itemMapper.mapCompare(params), {}, this.getToken)
    return this.itemMapper.mapResponseCompare(response);
  }

  async search(params?: SearchAuditRequestModel): Promise<SearchAuditResponseModel[]>{
    const response = await this.httpService.get<HttpItemsModel<SearchAuditResponseDto[]>>(`${environment.endpoints.audit.search}`, params ? this.itemMapper.mapSearch(params) : {}, {}, this.getToken)
    return response.items.map((item: SearchAuditResponseDto) => this.itemMapper.mapResponseSearch(item));
  }
}
