import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {AuditMapper} from '@/app/domain/mappers/audit/audit.mapper';
import {CreateAuditRequestModel,FilterAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';
import {AuditResponseModel, CreateAuditResponseModel} from '@/app/domain/models/audit/response/audit-response.model';
import {AuditResponseDto, CreateAuditResponseDto} from '@/app/infrastructure/dto/response/audit-response.dto';
import {HttpClientHelper} from '@/app/helper/http-client.helper';
import {environment} from '@/environments/environment';
import {HttpItemsModel} from '@/app/infrastructure/dto/http/http-default.model';


@Injectable({
  providedIn: 'root'
})
export class AuditService {
  itemMapper = new AuditMapper();
  constructor(private httpService: HttpService) {
  }

  async create(params: CreateAuditRequestModel): Promise<CreateAuditResponseModel> {
    const response = await this.httpService.post<CreateAuditResponseDto>(`${environment.endpoints.audit.path}`, this.itemMapper.mapCreate(params))
    return this.itemMapper.mapResponseCreate(response);
  }

  async delete(id: number): Promise<any> {
    return await this.httpService.delete<any>(`${environment.endpoints.audit.path}/${id}`);
  }

  async get(params?: FilterAuditRequestModel): Promise<AuditResponseModel[]> {
    const response = await this.httpService.get<HttpItemsModel<AuditResponseDto[]>>(`${environment.endpoints.audit.path}`, params ? this.itemMapper.mapFilter(params):{});
    return response.items.map((item: AuditResponseDto) => this.itemMapper.mapResponse(item));
  }

  async find(id: number): Promise<AuditResponseModel> {
    const response = await this.httpService.get<AuditResponseDto>(`${environment.endpoints.audit.path}/${id}`);
    return this.itemMapper.mapResponse(response);
  }
}
