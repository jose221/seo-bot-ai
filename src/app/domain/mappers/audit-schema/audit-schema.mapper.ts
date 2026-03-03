import { AppMapper } from '../app.mapper';
import {
  CreateAuditSchemaRequestModel,
  FilterAuditSchemaRequestModel,
} from '@/app/domain/models/audit-schema/request/audit-schema-request.model';
import {
  CreateAuditSchemaRequestDto,
  FilterAuditSchemaRequestDto,
} from '@/app/infrastructure/dto/request/audit-schema-request.dto';
import {
  AuditSchemaItemResponseModel,
  AuditSchemaListResponseModel,
  CreateAuditSchemaResponseModel,
  FindAuditSchemaResponseModel,
} from '@/app/domain/models/audit-schema/response/audit-schema-response.model';
import {
  AuditSchemaItemResponseDto,
  AuditSchemaListResponseDto,
  CreateAuditSchemaResponseDto,
  FindAuditSchemaResponseDto,
} from '@/app/infrastructure/dto/response/audit-schema-response.dto';

export class AuditSchemaMapper extends AppMapper {
  constructor() {
    super();
  }

  // --------- mapCreate
  mapCreate(model: CreateAuditSchemaRequestModel): CreateAuditSchemaRequestDto;
  mapCreate(dto: CreateAuditSchemaRequestDto): CreateAuditSchemaRequestModel;
  mapCreate(input: CreateAuditSchemaRequestModel | CreateAuditSchemaRequestDto): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapFilter
  mapFilter(model: FilterAuditSchemaRequestModel): FilterAuditSchemaRequestDto;
  mapFilter(dto: FilterAuditSchemaRequestDto): FilterAuditSchemaRequestModel;
  mapFilter(input: FilterAuditSchemaRequestModel | FilterAuditSchemaRequestDto): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponseItem
  mapResponseItem(dto: AuditSchemaItemResponseDto): AuditSchemaItemResponseModel;
  mapResponseItem(model: AuditSchemaItemResponseModel): AuditSchemaItemResponseDto;
  mapResponseItem(input: AuditSchemaItemResponseDto | AuditSchemaItemResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponseCreate
  mapResponseCreate(dto: CreateAuditSchemaResponseDto): CreateAuditSchemaResponseModel;
  mapResponseCreate(model: CreateAuditSchemaResponseModel): CreateAuditSchemaResponseDto;
  mapResponseCreate(input: CreateAuditSchemaResponseDto | CreateAuditSchemaResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponseFind
  mapResponseFind(dto: FindAuditSchemaResponseDto): FindAuditSchemaResponseModel;
  mapResponseFind(model: FindAuditSchemaResponseModel): FindAuditSchemaResponseDto;
  mapResponseFind(input: FindAuditSchemaResponseDto | FindAuditSchemaResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponseList
  mapResponseList(dto: AuditSchemaListResponseDto): AuditSchemaListResponseModel {
    return new AuditSchemaListResponseModel(
      dto.items.map((item) => this.mapResponseItem(item as AuditSchemaItemResponseDto)),
      dto.total,
      dto.page,
      dto.page_size
    );
  }
}

