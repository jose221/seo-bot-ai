import { Injectable } from '@angular/core';
import { StructuredValidationRepository } from '@/app/domain/repositories/structured-validation/structured-validation.repository';
import { StructuredValidationService } from '@/app/infrastructure/services/structured-validation/structured-validation.service';
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
  StructuredValidationCreateRequestModel,
} from '@/app/domain/models/structured-validation/request/structured-validation-request.model';
import {
  StructuredValidationTaskControlAction,
  StructuredValidationRerunResponseModel,
  StructuredValidationTaskCreateResponseModel,
  StructuredValidationTaskListResponseModel,
  StructuredValidationTaskResponseModel,
} from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
import { TaskLogListResponseModel } from '@/app/domain/models/task-log/response/task-log-response.model';

@Injectable({ providedIn: 'root' })
export class StructuredValidationImplementationRepository implements StructuredValidationRepository {
  constructor(private primaryService: StructuredValidationService) {}

  create(params: StructuredValidationCreateRequestModel): Promise<StructuredValidationTaskCreateResponseModel> {
    return this.primaryService.create(params);
  }

  getAll(params?: FilterStructuredValidationTasksRequestModel): Promise<StructuredValidationTaskListResponseModel> {
    return this.primaryService.getAll(params);
  }

  find(id: string): Promise<StructuredValidationTaskResponseModel> {
    return this.primaryService.find(id);
  }

  findPublic(id: string): Promise<StructuredValidationTaskResponseModel> {
    return this.primaryService.findPublic(id);
  }

  getLogs(id: string): Promise<TaskLogListResponseModel> {
    return this.primaryService.getLogs(id);
  }

  controlTask(id: string, action: StructuredValidationTaskControlAction): Promise<StructuredValidationTaskResponseModel> {
    return this.primaryService.controlTask(id, action);
  }

  rerun(id: string): Promise<StructuredValidationRerunResponseModel> {
    return this.primaryService.rerun(id);
  }

  delete(id: string): Promise<any> {
    return this.primaryService.delete(id);
  }

  getPublicComments(taskId: string, page?: number): Promise<PublicCommentsResponseModel> {
    return this.primaryService.getPublicComments(taskId, page);
  }

  createPublicComment(
    itemKey: string,
    taskId: string,
    params: CreatePublicCommentRequestModel,
  ): Promise<CreatePublicCommentResponseModel> {
    return this.primaryService.createPublicComment(itemKey, taskId, params);
  }

  answerComment(commentId: string, params: AnswerCommentRequestModel): Promise<any> {
    return this.primaryService.answerComment(commentId, params);
  }
}
