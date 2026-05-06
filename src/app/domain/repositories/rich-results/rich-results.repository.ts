import {
  CreateRichResultsReportRequestModel,
  FilterRichResultsReportsRequestModel,
} from '@/app/domain/models/rich-results/request/rich-results-request.model';
import {
  RichResultsReportDetailResponseModel,
  RichResultsReportListResponseModel,
  RichResultsReportTaskResponseModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';

export abstract class RichResultsRepository {
  abstract create(params: CreateRichResultsReportRequestModel): Promise<RichResultsReportTaskResponseModel>;
  abstract getAll(params?: FilterRichResultsReportsRequestModel): Promise<RichResultsReportListResponseModel>;
  abstract find(id: string, url: string): Promise<RichResultsReportDetailResponseModel>;
  abstract delete(id: string, url: string): Promise<any>;
  abstract deleteByUrl(url: string): Promise<any>;
}
