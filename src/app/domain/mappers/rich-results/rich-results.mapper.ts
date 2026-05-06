import { AppMapper } from '../app.mapper';
import {
  CreateRichResultsReportRequestModel,
  FilterRichResultsReportsRequestModel,
} from '@/app/domain/models/rich-results/request/rich-results-request.model';
import {
  RichResultsReportDetailResponseModel,
  RichResultsReportListItemModel,
  RichResultsReportListResponseModel,
  RichResultsReportTaskResponseModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';
import {
  CreateRichResultsReportRequestDto,
  FilterRichResultsReportsRequestDto,
} from '@/app/infrastructure/dto/request/rich-results-request.dto';
import {
  RichResultsReportDetailResponseDto,
  RichResultsReportListItemDto,
  RichResultsReportListResponseDto,
  RichResultsReportTaskResponseDto,
} from '@/app/infrastructure/dto/response/rich-results-response.dto';

export class RichResultsMapper extends AppMapper {
  mapCreate(model: CreateRichResultsReportRequestModel): CreateRichResultsReportRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapFilter(model: FilterRichResultsReportsRequestModel): FilterRichResultsReportsRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapResponseTask(dto: RichResultsReportTaskResponseDto): RichResultsReportTaskResponseModel {
    return this.autoMap<any, any>(dto, { except: [] });
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
