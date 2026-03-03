import { Injectable } from '@angular/core';
import { HttpService } from '@/app/infrastructure/services/general/http.service';
import { BaseService } from '@/app/infrastructure/services/base/base.service';
import { environment } from '@/environments/environment';
import { AuditSchemaMapper } from '@/app/domain/mappers/audit-schema/audit-schema.mapper';
import {
  CreateAuditSchemaRequestModel,
  FilterAuditSchemaRequestModel,
} from '@/app/domain/models/audit-schema/request/audit-schema-request.model';
import {
  AuditSchemaListResponseModel,
  CreateAuditSchemaResponseModel,
  FindAuditSchemaResponseModel,
} from '@/app/domain/models/audit-schema/response/audit-schema-response.model';
import {
  AuditSchemaListResponseDto,
  CreateAuditSchemaResponseDto,
  FindAuditSchemaResponseDto,
} from '@/app/infrastructure/dto/response/audit-schema-response.dto';

@Injectable({
  providedIn: 'root',
})
export class AuditSchemaService extends BaseService {
  private readonly mapper = new AuditSchemaMapper();
  private get endpoint(): string {
    return (environment.endpoints as any).auditSchema.path as string;
  }

  constructor(private httpService: HttpService) {
    super();
  }

  async create(params: CreateAuditSchemaRequestModel): Promise<CreateAuditSchemaResponseModel> {
    const response = await this.httpService.post<CreateAuditSchemaResponseDto>(
      this.endpoint,
      this.mapper.mapCreate(params),
      {},
      this.getToken
    );
    return this.mapper.mapResponseCreate(response);
  }

  async getAll(params?: FilterAuditSchemaRequestModel): Promise<AuditSchemaListResponseModel> {
    const response = await this.httpService.get<AuditSchemaListResponseDto>(
      this.endpoint,
      params ? this.mapper.mapFilter(params) : {},
      {},
      this.getToken
    );
    return this.mapper.mapResponseList(response);
  }

  async find(id: string): Promise<FindAuditSchemaResponseModel> {
    const response = await this.httpService.get<FindAuditSchemaResponseDto>(
      `${this.endpoint}/${id}`,
      {},
      {},
      this.getToken
    );
    return this.mapper.mapResponseFind(response);
  }

  async delete(id: string): Promise<any> {
    return await this.httpService.delete<any>(
      `${this.endpoint}/${id}`,
      {},
      this.getToken
    );
  }
}

