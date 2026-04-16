import { Injectable } from '@angular/core';
import { HttpService } from '@/app/infrastructure/services/general/http.service';
import { BaseService } from '@/app/infrastructure/services/base/base.service';
import { environment } from '@/environments/environment';
import { AuditUrlValidationMapper } from '@/app/domain/mappers/audit-url-validation/audit-url-validation.mapper';
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
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  AuditUrlValidationListResponseDto,
  CreateAuditUrlValidationResponseDto,
  FindAuditUrlValidationResponseDto,
  AuditUrlValidationSchemasResponseDto,
  PublicCommentsResponseDto,
  CreatePublicCommentResponseDto,
} from '@/app/infrastructure/dto/response/audit-url-validation-response.dto';

@Injectable({
  providedIn: 'root',
})
export class AuditUrlValidationService extends BaseService {
  private readonly mapper = new AuditUrlValidationMapper();
  private get endpoint(): string {
    return (environment.endpoints as any).auditUrlValidation.path as string;
  }

  constructor(private httpService: HttpService) {
    super();
  }

  async create(params: CreateAuditUrlValidationRequestModel): Promise<CreateAuditUrlValidationResponseModel> {
    const response = await this.httpService.post<CreateAuditUrlValidationResponseDto>(
      this.endpoint,
      this.mapper.mapCreate(params),
      {},
      this.getToken
    );
    return this.mapper.mapResponseCreate(response);
  }

  async getAll(params?: FilterAuditUrlValidationRequestModel): Promise<AuditUrlValidationListResponseModel> {
    const response = await this.httpService.get<AuditUrlValidationListResponseDto>(
      this.endpoint,
      params ? this.mapper.mapFilter(params) : {},
      {},
      this.getToken
    );
    return this.mapper.mapResponseList(response);
  }

  async find(id: string): Promise<FindAuditUrlValidationResponseModel> {
    const response = await this.httpService.get<FindAuditUrlValidationResponseDto>(
      `${this.endpoint}/${id}`,
      {},
      {},
      this.getToken
    );
    return this.mapper.mapResponseFind(response);
  }

  async delete(id: string): Promise<any> {
    return await this.httpService.delete<any>(
      `${this.endpoint}/${id}`,
      {},
      this.getToken
    );
  }

  async getSchemas(id: string): Promise<AuditUrlValidationSchemasResponseModel> {
    const response = await this.httpService.get<AuditUrlValidationSchemasResponseDto>(
      `${this.endpoint}/${id}/schemas`,
      {},
      {},
      this.getToken
    );
    return this.mapper.mapResponseSchemas(response);
  }

  async getSchemasPublic(id: string): Promise<AuditUrlValidationSchemasResponseModel> {
    const response = await this.httpService.get<AuditUrlValidationSchemasResponseDto>(
      `${this.endpoint}/${id}/schemas/public`,
      {},
      {}
    );
    return this.mapper.mapResponseSchemas(response);
  }

  async getPublicComments(validationId: string, page: number = 1): Promise<PublicCommentsResponseModel> {
    const response = await this.httpService.get<PublicCommentsResponseDto>(
      `${this.endpoint}/${validationId}/schemas/public/comments`,
      { page },
      {}
    );
    return this.mapper.mapResponsePublicComments(response);
  }

  async createPublicComment(schemaItemId: string, validationId: string, params: CreatePublicCommentRequestModel): Promise<CreatePublicCommentResponseModel> {
    const response = await this.httpService.post<CreatePublicCommentResponseDto>(
      `${this.endpoint}/schema/public/${schemaItemId}/comment`,
      this.mapper.mapPublicComment(params),
      { params: { validation_id: validationId } }
    );
    return this.mapper.mapResponseCreatePublicComment(response);
  }

  async answerComment(commentId: string, params: AnswerCommentRequestModel): Promise<any> {
    return await this.httpService.post<any>(
      `${this.endpoint}/schema/comments/${commentId}/answer`,
      this.mapper.mapAnswerComment(params),
      {},
      this.getToken
    );
  }
}

