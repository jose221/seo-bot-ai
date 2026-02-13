import { Injectable } from '@angular/core';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {
  AuditResponseModel, CompareAuditResponseModel,
  CreateAuditResponseModel, CreateCompareAuditResponseModel, FindCompareAuditResponseModel,
  SearchAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';
import {
  CreateCompareAuditRequestModel,
  CreateAuditRequestModel,
  FilterAuditRequestModel,
  SearchAuditRequestModel, FilterCompareAuditRequestModel
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
  async compare(params: CreateCompareAuditRequestModel): Promise<CreateCompareAuditResponseModel> {
    return await this.primaryService.compare(params);
  }
  async findComparisons(id: string): Promise<FindCompareAuditResponseModel>{
    return await this.primaryService.findComparisons(id);
  }
  async getComparisons(params?: FilterCompareAuditRequestModel): Promise<CompareAuditResponseModel[]>{
    return await this.primaryService.getComparisons(params);
  }

  async deleteComparisons(id: string): Promise<any> {
    return await this.primaryService.deleteComparisons(id);
  }
}
