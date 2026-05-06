import { Injectable } from '@angular/core';
import { RichResultsRepository } from '@/app/domain/repositories/rich-results/rich-results.repository';
import { RichResultsService } from '@/app/infrastructure/services/rich-results/rich-results.service';
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

@Injectable({ providedIn: 'root' })
export class RichResultsImplementationRepository implements RichResultsRepository {
  constructor(private primaryService: RichResultsService) {}

  async create(params: CreateRichResultsReportRequestModel): Promise<RichResultsReportTaskResponseModel> {
    return this.primaryService.create(params);
  }

  async createBatch(
    params: CreateRichResultsBatchReportRequestModel,
  ): Promise<RichResultsReportBatchResponseModel> {
    return this.primaryService.createBatch(params);
  }

  async getStatuses(
    params: GetRichResultsStatusesRequestModel,
  ): Promise<RichResultsReportStatusSummaryResponseModel> {
    return this.primaryService.getStatuses(params);
  }

  async getAll(params?: FilterRichResultsReportsRequestModel): Promise<RichResultsReportListResponseModel> {
    return this.primaryService.getAll(params);
  }

  async find(id: string, url: string): Promise<RichResultsReportDetailResponseModel> {
    return this.primaryService.find(id, url);
  }

  async delete(id: string, url: string): Promise<any> {
    return this.primaryService.delete(id, url);
  }

  async deleteByUrl(url: string): Promise<any> {
    return this.primaryService.deleteByUrl(url);
  }
}
