import { Injectable } from '@angular/core';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {AuditResponseModel, CreateAuditResponseModel} from '@/app/domain/models/audit/response/audit-response.model';
import {CreateAuditRequestModel, FilterAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';
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
  async delete(id: number): Promise<any> {
    return await this.primaryService.delete(id);
  }
  async get(params?: FilterAuditRequestModel): Promise<AuditResponseModel[]> {
    return await this.primaryService.get(params);
  }
  async find(id: number): Promise<AuditResponseModel> {
    return await this.primaryService.find(id);
  }
}
