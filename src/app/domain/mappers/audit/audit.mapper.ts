import {CompareAuditRequestModel, FilterAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';
import {CompareAuditRequestDto, FilterAuditRequestDto} from '@/app/infrastructure/dto/request/audit-request.dto';
import {CreateAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';
import {CreateAuditRequestDto} from '@/app/infrastructure/dto/request/audit-request.dto';
import { AppMapper } from "../app.mapper";
import {
  AuditResponseDto,
  CompareAuditResponseDto,
  CreateAuditResponseDto
} from '@/app/infrastructure/dto/response/audit-response.dto';
import {
  AuditResponseModel,
  CompareAuditResponseModel,
  CreateAuditResponseModel
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

  // --------- mapResponse Create(sobrecargas)
  mapResponseCreate(dto: CreateAuditResponseDto): CreateAuditResponseModel;
  mapResponseCreate(model: CreateAuditResponseModel): CreateAuditResponseDto;
  mapResponseCreate(input: CreateAuditResponseDto | CreateAuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapResponse Create(sobrecargas)
  mapResponseCompare(dto: CompareAuditResponseDto): CompareAuditResponseModel;
  mapResponseCompare(model: CompareAuditResponseModel): CompareAuditResponseDto;
  mapResponseCompare(input: CompareAuditResponseDto | CompareAuditResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapCreate (sobrecargas)
  mapCreate(dto: CreateAuditRequestDto): CreateAuditRequestModel;
  mapCreate(model: CreateAuditRequestModel): CreateAuditRequestDto;
  mapCreate(input: CreateAuditRequestDto | CreateAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapCompare (sobrecargas)
  mapCompare(dto: CompareAuditRequestDto): CompareAuditRequestModel;
  mapCompare(model: CompareAuditRequestModel): CompareAuditRequestDto;
  mapCompare(input: CompareAuditRequestDto | CompareAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapFilter (sobrecargas)
  mapFilter(dto: FilterAuditRequestDto): FilterAuditRequestModel;
  mapFilter(model: FilterAuditRequestModel): FilterAuditRequestDto;
  mapFilter(input: FilterAuditRequestDto | FilterAuditRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
