import {
  AuditUrlValidationListResponseModel,
  CreateAuditUrlValidationResponseModel,
  FindAuditUrlValidationResponseModel,
  AuditUrlValidationSchemasResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  CreateAuditUrlValidationRequestModel,
  FilterAuditUrlValidationRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';

export abstract class AuditUrlValidationRepository {
  abstract create(params: CreateAuditUrlValidationRequestModel): Promise<CreateAuditUrlValidationResponseModel>;
  abstract getAll(params?: FilterAuditUrlValidationRequestModel): Promise<AuditUrlValidationListResponseModel>;
  abstract find(id: string): Promise<FindAuditUrlValidationResponseModel>;
  abstract delete(id: string): Promise<any>;
  abstract getSchemas(id: string): Promise<AuditUrlValidationSchemasResponseModel>;
}

