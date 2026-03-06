import { Injectable } from '@angular/core';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { AuditUrlValidationService } from '@/app/infrastructure/services/audit-url-validation/audit-url-validation.service';
import {
  CreateAuditUrlValidationRequestModel,
  FilterAuditUrlValidationRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import {
  AuditUrlValidationListResponseModel,
  CreateAuditUrlValidationResponseModel,
  FindAuditUrlValidationResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';

@Injectable({
  providedIn: 'root',
})
export class AuditUrlValidationImplementationRepository implements AuditUrlValidationRepository {
  constructor(private primaryService: AuditUrlValidationService) {}

  async create(params: CreateAuditUrlValidationRequestModel): Promise<CreateAuditUrlValidationResponseModel> {
    return await this.primaryService.create(params);
  }

  async getAll(params?: FilterAuditUrlValidationRequestModel): Promise<AuditUrlValidationListResponseModel> {
    return await this.primaryService.getAll(params);
  }

  async find(id: string): Promise<FindAuditUrlValidationResponseModel> {
    return await this.primaryService.find(id);
  }

  async delete(id: string): Promise<any> {
    return await this.primaryService.delete(id);
  }
}

