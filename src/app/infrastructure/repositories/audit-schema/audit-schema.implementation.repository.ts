import { Injectable } from '@angular/core';
import { AuditSchemaRepository } from '@/app/domain/repositories/audit-schema/audit-schema.repository';
import { AuditSchemaService } from '@/app/infrastructure/services/audit-schema/audit-schema.service';
import {
  CreateAuditSchemaRequestModel,
  FilterAuditSchemaRequestModel,
} from '@/app/domain/models/audit-schema/request/audit-schema-request.model';
import {
  AuditSchemaListResponseModel,
  CreateAuditSchemaResponseModel,
  FindAuditSchemaResponseModel,
} from '@/app/domain/models/audit-schema/response/audit-schema-response.model';

@Injectable({
  providedIn: 'root',
})
export class AuditSchemaImplementationRepository implements AuditSchemaRepository {
  constructor(private primaryService: AuditSchemaService) {}

  async create(params: CreateAuditSchemaRequestModel): Promise<CreateAuditSchemaResponseModel> {
    return await this.primaryService.create(params);
  }

  async getAll(params?: FilterAuditSchemaRequestModel): Promise<AuditSchemaListResponseModel> {
    return await this.primaryService.getAll(params);
  }

  async find(id: string): Promise<FindAuditSchemaResponseModel> {
    return await this.primaryService.find(id);
  }

  async delete(id: string): Promise<any> {
    return await this.primaryService.delete(id);
  }
}

