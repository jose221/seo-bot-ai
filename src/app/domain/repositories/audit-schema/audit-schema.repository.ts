import {
  AuditSchemaItemResponseModel,
  AuditSchemaListResponseModel,
  CreateAuditSchemaResponseModel,
  FindAuditSchemaResponseModel,
} from '@/app/domain/models/audit-schema/response/audit-schema-response.model';
import {
  CreateAuditSchemaRequestModel,
  FilterAuditSchemaRequestModel,
} from '@/app/domain/models/audit-schema/request/audit-schema-request.model';

export abstract class AuditSchemaRepository {
  abstract create(params: CreateAuditSchemaRequestModel): Promise<CreateAuditSchemaResponseModel>;
  abstract getAll(params?: FilterAuditSchemaRequestModel): Promise<AuditSchemaListResponseModel>;
  abstract find(id: string): Promise<FindAuditSchemaResponseModel>;
  abstract delete(id: string): Promise<any>;
}

