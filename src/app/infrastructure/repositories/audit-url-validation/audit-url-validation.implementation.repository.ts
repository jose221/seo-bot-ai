import { Injectable } from '@angular/core';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { AuditUrlValidationService } from '@/app/infrastructure/services/audit-url-validation/audit-url-validation.service';
import {
  CreateAuditUrlValidationRequestModel,
  FilterAuditUrlValidationRequestModel,
  CreatePublicCommentRequestModel,
  AnswerCommentRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import {
  AuditUrlValidationListResponseModel,
  CreateAuditUrlValidationResponseModel,
  FindAuditUrlValidationResponseModel,
  AuditUrlValidationSchemasResponseModel,
  PublicCommentsResponseModel,
  CreatePublicCommentResponseModel,
  RerunValidationResponseModel,
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

  async getSchemas(id: string): Promise<AuditUrlValidationSchemasResponseModel> {
    return await this.primaryService.getSchemas(id);
  }

  async getSchemasPublic(id: string): Promise<AuditUrlValidationSchemasResponseModel> {
    return await this.primaryService.getSchemasPublic(id);
  }

  async getPublicComments(validationId: string, page?: number): Promise<PublicCommentsResponseModel> {
    return await this.primaryService.getPublicComments(validationId, page);
  }

  async createPublicComment(schemaItemId: string, validationId: string, params: CreatePublicCommentRequestModel): Promise<CreatePublicCommentResponseModel> {
    return await this.primaryService.createPublicComment(schemaItemId, validationId, params);
  }

  async answerComment(commentId: string, params: AnswerCommentRequestModel): Promise<any> {
    return await this.primaryService.answerComment(commentId, params);
  }

  async rerunValidation(validationId: string): Promise<RerunValidationResponseModel> {
    return await this.primaryService.rerunValidation(validationId);
  }

  async rerunValidationUrl(validationId: string, url: string): Promise<RerunValidationResponseModel> {
    return await this.primaryService.rerunValidationUrl(validationId, url);
  }
}

