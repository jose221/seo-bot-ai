import { Injectable } from '@angular/core';
import { BaseService } from '@/app/infrastructure/services/base/base.service';
import { HttpService } from '@/app/infrastructure/services/general/http.service';
import { environment } from '@/environments/environment';
import { RichResultsMapper } from '@/app/domain/mappers/rich-results/rich-results.mapper';
import {
  CreateRichResultsReportRequestModel,
  FilterRichResultsReportsRequestModel,
} from '@/app/domain/models/rich-results/request/rich-results-request.model';
import {
  RichResultsReportDetailResponseModel,
  RichResultsReportListResponseModel,
  RichResultsReportTaskResponseModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';
import {
  RichResultsReportDetailResponseDto,
  RichResultsReportListResponseDto,
  RichResultsReportTaskResponseDto,
} from '@/app/infrastructure/dto/response/rich-results-response.dto';

@Injectable({ providedIn: 'root' })
export class RichResultsService extends BaseService {
  private readonly mapper = new RichResultsMapper();

  private get endpoint(): string {
    return (environment.endpoints as any).richResults.path as string;
  }

  constructor(private httpService: HttpService) {
    super();
  }

  async create(params: CreateRichResultsReportRequestModel): Promise<RichResultsReportTaskResponseModel> {
    const response = await this.httpService.post<RichResultsReportTaskResponseDto>(
      `${this.endpoint}/report-page`,
      this.mapper.mapCreate(params),
      {},
      this.getToken,
    );
    return this.mapper.mapResponseTask(response);
  }

  async getAll(params?: FilterRichResultsReportsRequestModel): Promise<RichResultsReportListResponseModel> {
    const response = await this.httpService.get<RichResultsReportListResponseDto>(
      `${this.endpoint}/get_reports`,
      params ? this.mapper.mapFilter(params) : {},
      {},
    );
    return this.mapper.mapResponseList(response);
  }

  async find(id: string, url: string): Promise<RichResultsReportDetailResponseModel> {
    const response = await this.httpService.get<RichResultsReportDetailResponseDto>(
      `${this.endpoint}/get_reports/${id}`,
      { url },
      {},
    );
    return this.mapper.mapResponseDetail(response);
  }

  async delete(id: string, url: string): Promise<any> {
    return this.httpService.delete(
      `${this.endpoint}/reports/${id}?url=${encodeURIComponent(url)}`,
      {},
      this.getToken,
    );
  }

  async deleteByUrl(url: string): Promise<any> {
    return this.httpService.delete(`${this.endpoint}/reports?url=${encodeURIComponent(url)}`, {}, this.getToken);
  }
}
