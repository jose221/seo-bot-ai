import {
  AuditResponseModel, CompareAuditResponseModel,
  CreateAuditResponseModel, CreateCompareAuditResponseModel, FindCompareAuditResponseModel,
  SearchAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';
import {
  CreateAuditRequestModel, CreateCompareAuditRequestModel,
  FilterAuditRequestModel, FilterCompareAuditRequestModel,
  SearchAuditRequestModel
} from '@/app/domain/models/audit/request/audit-request.model';

export abstract class AuditRepository {
  abstract create(params: CreateAuditRequestModel): Promise<CreateAuditResponseModel>;
  abstract delete(id: string): Promise<any>;
  abstract get(params?: FilterAuditRequestModel): Promise<AuditResponseModel[]>;
  abstract find(id: string): Promise<AuditResponseModel>;
  abstract search(params?: SearchAuditRequestModel): Promise<SearchAuditResponseModel[]>;
  abstract compare(params: CreateCompareAuditRequestModel): Promise<CreateCompareAuditResponseModel>;
  abstract findComparisons(id: string): Promise<FindCompareAuditResponseModel>;
  abstract getComparisons(params?: FilterCompareAuditRequestModel): Promise<CompareAuditResponseModel[]>;

}
