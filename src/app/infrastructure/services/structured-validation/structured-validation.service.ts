import { Injectable } from '@angular/core';
import { BaseService } from '@/app/infrastructure/services/base/base.service';
import { HttpService } from '@/app/infrastructure/services/general/http.service';
import { environment } from '@/environments/environment';
import { StructuredValidationMapper } from '@/app/domain/mappers/structured-validation/structured-validation.mapper';
import {
  CreatePublicCommentRequestModel,
  AnswerCommentRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import {
  CreatePublicCommentResponseModel,
  PublicCommentsResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  FilterStructuredValidationTasksRequestModel,
  StructuredValidationTaskDetailRequestModel,
  StructuredValidationCreateRequestModel,
} from '@/app/domain/models/structured-validation/request/structured-validation-request.model';
import {
  StructuredValidationBrowserModeOptionModel,
  StructuredValidationTaskControlAction,
  StructuredValidationRerunResponseModel,
  StructuredValidationTaskCreateResponseModel,
  StructuredValidationTaskListResponseModel,
  StructuredValidationTaskResponseModel,
} from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
import { TaskLogListResponseModel, TaskLogEntryResponseModel } from '@/app/domain/models/task-log/response/task-log-response.model';
import {
  FilterStructuredValidationTasksRequestDto,
  StructuredValidationTaskDetailRequestDto,
  StructuredValidationCreateRequestDto,
} from '@/app/infrastructure/dto/request/structured-validation-request.dto';
import {
  StructuredValidationBrowserModeOptionDto,
  StructuredValidationRerunResponseDto,
  StructuredValidationTaskCreateResponseDto,
  StructuredValidationTaskListResponseDto,
  StructuredValidationTaskResponseDto,
} from '@/app/infrastructure/dto/response/structured-validation-response.dto';
import {
  CreatePublicCommentResponseDto,
  PublicCommentsResponseDto,
} from '@/app/infrastructure/dto/response/audit-url-validation-response.dto';
import { TaskLogListResponseDto } from '@/app/infrastructure/dto/response/task-log-response.dto';

@Injectable({ providedIn: 'root' })
export class StructuredValidationService extends BaseService {
  private readonly mapper = new StructuredValidationMapper();

  private get endpoint(): string {
    const structuredValidation = (
      environment.endpoints as {
        structuredValidation?: { path?: string };
      }
    ).structuredValidation;

    if (!structuredValidation?.path) {
      throw new Error('Missing environment.endpoints.structuredValidation.path');
    }

    return structuredValidation.path;
  }

  constructor(private httpService: HttpService) {
    super();
  }

  async create(params: StructuredValidationCreateRequestModel): Promise<StructuredValidationTaskCreateResponseModel> {
    const response = await this.httpService.post<StructuredValidationTaskCreateResponseDto>(
      this.endpoint,
      this.mapper.mapCreate(params as StructuredValidationCreateRequestDto),
      {},
      this.getToken,
    );
    return this.mapper.mapResponseTaskCreate(response);
  }

  async getAll(params?: FilterStructuredValidationTasksRequestModel): Promise<StructuredValidationTaskListResponseModel> {
    const response = await this.httpService.get<StructuredValidationTaskListResponseDto>(
      this.endpoint,
      params ? this.mapper.mapFilter(params as FilterStructuredValidationTasksRequestDto) : {},
      {},
      this.getToken,
    );
    return this.mapper.mapResponseList(response);
  }

  async getBrowserModes(): Promise<StructuredValidationBrowserModeOptionModel[]> {
    const response = await this.httpService.get<StructuredValidationBrowserModeOptionDto[]>(
      `${this.endpoint}/browser-modes`,
      {},
      {},
      this.getToken,
    );
    return this.mapper.mapBrowserModes(response);
  }

  async find(id: string, params?: StructuredValidationTaskDetailRequestModel): Promise<StructuredValidationTaskResponseModel> {
    const response = await this.httpService.get<StructuredValidationTaskResponseDto>(
      `${this.endpoint}/${id}`,
      params ? this.mapper.mapDetailFilter(params as StructuredValidationTaskDetailRequestDto) : {},
      {},
      this.getToken,
    );
    return this.mapper.mapResponseTask(response);
  }

  async findPublic(id: string, params?: StructuredValidationTaskDetailRequestModel): Promise<StructuredValidationTaskResponseModel> {
    const response = await this.httpService.get<StructuredValidationTaskResponseDto>(
      `${this.endpoint}/${id}/public`,
      params ? this.mapper.mapDetailFilter(params as StructuredValidationTaskDetailRequestDto) : {},
      {},
    );
    return this.mapper.mapResponseTask(response);
  }

  async getLogs(id: string): Promise<TaskLogListResponseModel> {
    const response = await this.httpService.get<TaskLogListResponseDto>(
      `${this.endpoint}/${id}/logs`,
      {},
      {},
      this.getToken,
    );
    return new TaskLogListResponseModel(
      response.task_type,
      response.task_id,
      response.items.map(
        (item) => new TaskLogEntryResponseModel(
          item.id,
          item.level,
          item.message,
          item.progress_percentage,
          item.created_at,
        ),
      ),
    );
  }

  async controlTask(
    id: string,
    action: StructuredValidationTaskControlAction,
  ): Promise<StructuredValidationTaskResponseModel> {
    const response = await this.httpService.post<StructuredValidationTaskResponseDto>(
      `${this.endpoint}/${id}/actions`,
      { action },
      {},
      this.getToken,
    );
    return this.mapper.mapResponseTask(response);
  }

  async rerun(id: string): Promise<StructuredValidationRerunResponseModel> {
    const response = await this.httpService.post<StructuredValidationRerunResponseDto>(
      `${this.endpoint}/${id}/rerun`,
      {},
      {},
      this.getToken,
    );
    return this.mapper.mapResponseRerun(response);
  }

  async delete(id: string): Promise<any> {
    return this.httpService.delete(`${this.endpoint}/${id}`, {}, this.getToken);
  }

  async getPublicComments(taskId: string, page: number = 1): Promise<PublicCommentsResponseModel> {
    const response = await this.httpService.get<PublicCommentsResponseDto>(
      `${this.endpoint}/${taskId}/comments`,
      { page },
      {},
    );
    return this.mapper.mapResponsePublicComments(response);
  }

  async createPublicComment(
    itemKey: string,
    taskId: string,
    params: CreatePublicCommentRequestModel,
  ): Promise<CreatePublicCommentResponseModel> {
    const response = await this.httpService.post<CreatePublicCommentResponseDto>(
      `${this.endpoint}/public/${encodeURIComponent(itemKey)}/comment`,
      this.mapper.mapPublicComment(params),
      { params: { task_id: taskId } },
    );
    return this.mapper.mapResponseCreatePublicComment(response);
  }

  async answerComment(commentId: string, params: AnswerCommentRequestModel): Promise<any> {
    return this.httpService.patch(
      `${this.endpoint}/comments/${commentId}/answer`,
      this.mapper.mapAnswerComment(params),
      {},
      this.getToken,
    );
  }
}
