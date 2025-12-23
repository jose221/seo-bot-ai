import { Injectable } from '@angular/core';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {
  AuditResponseModel, CompareAuditResponseModel,
  CreateAuditResponseModel,
  SearchAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';
import {
  CompareAuditRequestModel,
  CreateAuditRequestModel,
  FilterAuditRequestModel,
  SearchAuditRequestModel
} from '@/app/domain/models/audit/request/audit-request.model';
import {AuditService} from '@/app/infrastructure/services/audit/audit.service';

@Injectable({
  providedIn: 'root'
})
export class AuditImplementationRepository implements AuditRepository {
  constructor(private primaryService: AuditService) {

  }
  async create(params: CreateAuditRequestModel): Promise<CreateAuditResponseModel> {
    return await this.primaryService.create(params);
  }
  async delete(id: string): Promise<any> {
    return await this.primaryService.delete(id);
  }
  async get(params?: FilterAuditRequestModel): Promise<AuditResponseModel[]> {
    return await this.primaryService.get(params);
  }
  async find(id: string): Promise<AuditResponseModel> {
    return await this.primaryService.find(id);
  }
  async search(params?: SearchAuditRequestModel): Promise<SearchAuditResponseModel[]> {
    return await this.primaryService.search(params);
  }
  async compare(params: CompareAuditRequestModel): Promise<CompareAuditResponseModel> {
    return await this.primaryService.compare(params);
  }
}
