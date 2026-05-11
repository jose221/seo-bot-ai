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
  StructuredValidationTaskControlAction,
  StructuredValidationRerunResponseModel,
  StructuredValidationTaskCreateResponseModel,
  StructuredValidationTaskListResponseModel,
  StructuredValidationTaskResponseModel,
} from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
import { TaskLogListResponseModel } from '@/app/domain/models/task-log/response/task-log-response.model';

export abstract class StructuredValidationRepository {
  abstract create(
    params: StructuredValidationCreateRequestModel,
  ): Promise<StructuredValidationTaskCreateResponseModel>;
  abstract getAll(
    params?: FilterStructuredValidationTasksRequestModel,
  ): Promise<StructuredValidationTaskListResponseModel>;
  abstract find(id: string, params?: StructuredValidationTaskDetailRequestModel): Promise<StructuredValidationTaskResponseModel>;
  abstract findPublic(id: string, params?: StructuredValidationTaskDetailRequestModel): Promise<StructuredValidationTaskResponseModel>;
  abstract getLogs(id: string): Promise<TaskLogListResponseModel>;
  abstract controlTask(id: string, action: StructuredValidationTaskControlAction): Promise<StructuredValidationTaskResponseModel>;
  abstract rerun(id: string): Promise<StructuredValidationRerunResponseModel>;
  abstract delete(id: string): Promise<any>;
  abstract getPublicComments(taskId: string, page?: number): Promise<PublicCommentsResponseModel>;
  abstract createPublicComment(
    itemKey: string,
    taskId: string,
    params: CreatePublicCommentRequestModel,
  ): Promise<CreatePublicCommentResponseModel>;
  abstract answerComment(commentId: string, params: AnswerCommentRequestModel): Promise<any>;
}
