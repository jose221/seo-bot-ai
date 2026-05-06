import { AppMapper } from '../app.mapper';
import {
  CreateRichResultsBatchReportRequestModel,
  CreateRichResultsReportRequestModel,
  FilterRichResultsReportsRequestModel,
  GetRichResultsStatusesRequestModel,
} from '@/app/domain/models/rich-results/request/rich-results-request.model';
import {
  RichResultsReportBatchResponseModel,
  RichResultsReportDetailResponseModel,
  RichResultsReportListItemModel,
  RichResultsReportListResponseModel,
  RichResultsReportStatusSummaryItemModel,
  RichResultsReportStatusSummaryResponseModel,
  RichResultsReportTaskResponseModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';
import {
  CreateRichResultsBatchReportRequestDto,
  CreateRichResultsReportRequestDto,
  FilterRichResultsReportsRequestDto,
  GetRichResultsStatusesRequestDto,
} from '@/app/infrastructure/dto/request/rich-results-request.dto';
import {
  RichResultsReportBatchResponseDto,
  RichResultsReportDetailResponseDto,
  RichResultsReportListItemDto,
  RichResultsReportListResponseDto,
  RichResultsReportStatusSummaryItemDto,
  RichResultsReportStatusSummaryResponseDto,
  RichResultsReportTaskResponseDto,
} from '@/app/infrastructure/dto/response/rich-results-response.dto';

export class RichResultsMapper extends AppMapper {
  mapCreate(model: CreateRichResultsReportRequestModel): CreateRichResultsReportRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapCreateBatch(model: CreateRichResultsBatchReportRequestModel): CreateRichResultsBatchReportRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapStatuses(model: GetRichResultsStatusesRequestModel): GetRichResultsStatusesRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapFilter(model: FilterRichResultsReportsRequestModel): FilterRichResultsReportsRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapResponseTask(dto: RichResultsReportTaskResponseDto): RichResultsReportTaskResponseModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }

  mapResponseBatch(dto: RichResultsReportBatchResponseDto): RichResultsReportBatchResponseModel {
    return new RichResultsReportBatchResponseModel(
      dto.total,
      dto.created_count,
      dto.items.map((item) => this.mapResponseTask(item)),
      dto.message,
    );
  }

  mapResponseStatusItem(dto: RichResultsReportStatusSummaryItemDto): RichResultsReportStatusSummaryItemModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }

  mapResponseStatuses(dto: RichResultsReportStatusSummaryResponseDto): RichResultsReportStatusSummaryResponseModel {
    return new RichResultsReportStatusSummaryResponseModel(
      dto.items.map((item) => this.mapResponseStatusItem(item)),
    );
  }

  mapResponseItem(dto: RichResultsReportListItemDto): RichResultsReportListItemModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }

  mapResponseList(dto: RichResultsReportListResponseDto): RichResultsReportListResponseModel {
    return new RichResultsReportListResponseModel(
      dto.items.map((item) => this.mapResponseItem(item)),
      dto.total,
      dto.page,
      dto.page_size,
    );
  }

  mapResponseDetail(dto: RichResultsReportDetailResponseDto): RichResultsReportDetailResponseModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }
}
