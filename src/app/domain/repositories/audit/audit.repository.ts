import {AuditResponseModel, CreateAuditResponseModel} from '@/app/domain/models/audit/response/audit-response.model';
import {CreateAuditRequestModel, FilterAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';

export abstract class AuditRepository {
  abstract create(params: CreateAuditRequestModel): Promise<CreateAuditResponseModel>;
  abstract delete(id: string): Promise<any>;
  abstract get(params?: FilterAuditRequestModel): Promise<AuditResponseModel[]>;
  abstract find(id: string): Promise<AuditResponseModel>;
}
