import {
  AuditUrlValidationListResponseModel,
  CreateAuditUrlValidationResponseModel,
  FindAuditUrlValidationResponseModel,
  AuditUrlValidationSchemasResponseModel,
  PublicCommentsResponseModel,
  CreatePublicCommentResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  CreateAuditUrlValidationRequestModel,
  FilterAuditUrlValidationRequestModel,
  CreatePublicCommentRequestModel,
  AnswerCommentRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';

export abstract class AuditUrlValidationRepository {
  abstract create(params: CreateAuditUrlValidationRequestModel): Promise<CreateAuditUrlValidationResponseModel>;
  abstract getAll(params?: FilterAuditUrlValidationRequestModel): Promise<AuditUrlValidationListResponseModel>;
  abstract find(id: string): Promise<FindAuditUrlValidationResponseModel>;
  abstract delete(id: string): Promise<any>;
  abstract getSchemas(id: string): Promise<AuditUrlValidationSchemasResponseModel>;
  abstract getSchemasPublic(id: string): Promise<AuditUrlValidationSchemasResponseModel>;
  abstract getPublicComments(validationId: string, page?: number): Promise<PublicCommentsResponseModel>;
  abstract createPublicComment(schemaItemId: string, validationId: string, params: CreatePublicCommentRequestModel): Promise<CreatePublicCommentResponseModel>;
  abstract answerComment(commentId: string, params: AnswerCommentRequestModel): Promise<any>;
}

