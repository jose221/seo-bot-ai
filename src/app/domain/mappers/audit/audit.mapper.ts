import {
  CreateCompareAuditRequestModel,
  FilterAuditRequestModel, FilterCompareAuditRequestModel,
  SearchAuditRequestModel
} from '@/app/domain/models/audit/request/audit-request.model';
import {
  CreateCompareAuditRequestDto,
  FilterAuditRequestDto, FilterCompareAuditRequestDto,
  SearchAuditRequestDto
} from '@/app/infrastructure/dto/request/audit-request.dto';
import {CreateAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';
import {CreateAuditRequestDto} from '@/app/infrastructure/dto/request/audit-request.dto';
import { AppMapper } from "../app.mapper";
import {
  AuditResponseDto, CompareAuditResponseDto,
  CreateAuditResponseDto, CreateCompareAuditResponseDto, FindCompareAuditResponseDto, SearchAuditResponseDto
} from '@/app/infrastructure/dto/response/audit-response.dto';
import {
  AuditResponseModel, CompareAuditResponseModel,
  CreateAuditResponseModel, CreateCompareAuditResponseModel, FindCompareAuditResponseModel, SearchAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';


export class AuditMapper extends AppMapper {
  constructor() {
    super();
  }

  // --------- mapResponse (sobrecargas)
  mapResponse(dto: AuditResponseDto): AuditResponseModel;
  mapResponse(model: AuditResponseModel): AuditResponseDto;
  mapResponse(input: AuditResponseDto | AuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse find comparisons (sobrecargas)
  mapResponseFindComparisons(dto: FindCompareAuditResponseDto): FindCompareAuditResponseModel;
  mapResponseFindComparisons(model: FindCompareAuditResponseModel): FindCompareAuditResponseDto;
  mapResponseFindComparisons(input: FindCompareAuditResponseDto | FindCompareAuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse Create(sobrecargas)
  mapResponseCreate(dto: CreateAuditResponseDto): CreateAuditResponseModel;
  mapResponseCreate(model: CreateAuditResponseModel): CreateAuditResponseDto;
  mapResponseCreate(input: CreateAuditResponseDto | CreateAuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse Create(sobrecargas)
  mapResponseCreateCompare(dto: CreateCompareAuditResponseDto): CreateCompareAuditResponseModel;
  mapResponseCreateCompare(model: CreateCompareAuditResponseModel): CreateCompareAuditResponseDto;
  mapResponseCreateCompare(input: CreateCompareAuditResponseDto | CreateCompareAuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse comparisons(sobrecargas)
  mapResponseComparisons(dto: CompareAuditResponseDto): CompareAuditResponseModel;
  mapResponseComparisons(model: CompareAuditResponseModel): CompareAuditResponseDto;
  mapResponseComparisons(input: CompareAuditResponseDto | CompareAuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse Search(sobrecargas)
  mapResponseSearch(dto: SearchAuditResponseDto): SearchAuditResponseModel;
  mapResponseSearch(model: SearchAuditResponseModel): SearchAuditResponseDto;
  mapResponseSearch(input: SearchAuditResponseDto | SearchAuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapCreate (sobrecargas)
  mapCreate(dto: CreateAuditRequestDto): CreateAuditRequestModel;
  mapCreate(model: CreateAuditRequestModel): CreateAuditRequestDto;
  mapCreate(input: CreateAuditRequestDto | CreateAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapCompare (sobrecargas)
  mapCreateCompare(dto: CreateCompareAuditRequestDto): CreateCompareAuditRequestModel;
  mapCreateCompare(model: CreateCompareAuditRequestModel): CreateCompareAuditRequestDto;
  mapCreateCompare(input: CreateCompareAuditRequestDto | CreateCompareAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapSearch (sobrecargas)
  mapSearch(dto: SearchAuditRequestDto): SearchAuditRequestModel;
  mapSearch(model: SearchAuditRequestModel): SearchAuditRequestDto;
  mapSearch(input: SearchAuditRequestDto | SearchAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapFilter (sobrecargas)
  mapFilter(dto: FilterAuditRequestDto): FilterAuditRequestModel;
  mapFilter(model: FilterAuditRequestModel): FilterAuditRequestDto;
  mapFilter(input: FilterAuditRequestDto | FilterAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
  // --------- mapFilterComparisons (sobrecargas)
  mapFilterComparisons(dto: FilterCompareAuditRequestDto): FilterCompareAuditRequestModel;
  mapFilterComparisons(model: FilterCompareAuditRequestModel): FilterCompareAuditRequestDto;
  mapFilterComparisons(input: FilterCompareAuditRequestDto | FilterCompareAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
