import { AppMapper } from '../app.mapper';
import {
  CreateAuditUrlValidationRequestModel,
  FilterAuditUrlValidationRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import {
  CreateAuditUrlValidationRequestDto,
  FilterAuditUrlValidationRequestDto,
} from '@/app/infrastructure/dto/request/audit-url-validation-request.dto';
import {
  AuditUrlValidationItemResponseModel,
  AuditUrlValidationListResponseModel,
  CreateAuditUrlValidationResponseModel,
  FindAuditUrlValidationResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  AuditUrlValidationItemResponseDto,
  AuditUrlValidationListResponseDto,
  CreateAuditUrlValidationResponseDto,
  FindAuditUrlValidationResponseDto,
} from '@/app/infrastructure/dto/response/audit-url-validation-response.dto';

export class AuditUrlValidationMapper extends AppMapper {
  constructor() {
    super();
  }

  mapCreate(model: CreateAuditUrlValidationRequestModel): CreateAuditUrlValidationRequestDto;
  mapCreate(dto: CreateAuditUrlValidationRequestDto): CreateAuditUrlValidationRequestModel;
  mapCreate(input: CreateAuditUrlValidationRequestModel | CreateAuditUrlValidationRequestDto): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapFilter(model: FilterAuditUrlValidationRequestModel): FilterAuditUrlValidationRequestDto;
  mapFilter(dto: FilterAuditUrlValidationRequestDto): FilterAuditUrlValidationRequestModel;
  mapFilter(input: FilterAuditUrlValidationRequestModel | FilterAuditUrlValidationRequestDto): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseItem(dto: AuditUrlValidationItemResponseDto): AuditUrlValidationItemResponseModel;
  mapResponseItem(model: AuditUrlValidationItemResponseModel): AuditUrlValidationItemResponseDto;
  mapResponseItem(input: AuditUrlValidationItemResponseDto | AuditUrlValidationItemResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseCreate(dto: CreateAuditUrlValidationResponseDto): CreateAuditUrlValidationResponseModel;
  mapResponseCreate(model: CreateAuditUrlValidationResponseModel): CreateAuditUrlValidationResponseDto;
  mapResponseCreate(input: CreateAuditUrlValidationResponseDto | CreateAuditUrlValidationResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseFind(dto: FindAuditUrlValidationResponseDto): FindAuditUrlValidationResponseModel;
  mapResponseFind(model: FindAuditUrlValidationResponseModel): FindAuditUrlValidationResponseDto;
  mapResponseFind(input: FindAuditUrlValidationResponseDto | FindAuditUrlValidationResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseList(dto: AuditUrlValidationListResponseDto): AuditUrlValidationListResponseModel {
    return new AuditUrlValidationListResponseModel(
      dto.items.map((item) => this.mapResponseItem(item as AuditUrlValidationItemResponseDto)),
      dto.total,
      dto.page,
      dto.page_size
    );
  }
}

