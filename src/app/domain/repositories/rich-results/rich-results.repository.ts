import {
  CreateRichResultsBatchReportRequestModel,
  CreateRichResultsReportRequestModel,
  FilterRichResultsReportsRequestModel,
  GetRichResultsStatusesRequestModel,
} from '@/app/domain/models/rich-results/request/rich-results-request.model';
import {
  RichResultsReportBatchResponseModel,
  RichResultsReportDetailResponseModel,
  RichResultsReportListResponseModel,
  RichResultsReportStatusSummaryResponseModel,
  RichResultsReportTaskResponseModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';
import { TaskLogListResponseModel } from '@/app/domain/models/task-log/response/task-log-response.model';

export abstract class RichResultsRepository {
  abstract create(params: CreateRichResultsReportRequestModel): Promise<RichResultsReportTaskResponseModel>;
  abstract createBatch(
    params: CreateRichResultsBatchReportRequestModel,
  ): Promise<RichResultsReportBatchResponseModel>;
  abstract getStatuses(
    params: GetRichResultsStatusesRequestModel,
  ): Promise<RichResultsReportStatusSummaryResponseModel>;
  abstract getAll(params?: FilterRichResultsReportsRequestModel): Promise<RichResultsReportListResponseModel>;
  abstract find(id: string, url: string): Promise<RichResultsReportDetailResponseModel>;
  abstract getLogs(id: string, url: string): Promise<TaskLogListResponseModel>;
  abstract delete(id: string, url: string): Promise<any>;
  abstract deleteByUrl(url: string): Promise<any>;
}
