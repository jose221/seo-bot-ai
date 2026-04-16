import {
  FilterTargetRequestModel,
  SearchTargetRequestModel,
  UpdateTargetRequestModel
} from '@/app/domain/models/target/request/target-request.model';
import {FilterTargetRequestDto, SearchTargetRequestDto, UpdateTargetRequestDto} from '@/app/infrastructure/dto/request/target-request.dto';
import {CreateTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {CreateTargetRequestDto} from '@/app/infrastructure/dto/request/target-request.dto';
import { AppMapper } from "../app.mapper";
import {TargetRequestDto} from '@/app/infrastructure/dto/request/target-request.dto';
import {SearchTargetResponseDto, TargetResponseDto} from '@/app/infrastructure/dto/response/target-response.dto';
import {
  SearchTargetResponseModel,
  TargetResponseModel
} from '@/app/domain/models/target/response/target-response.model';


export class TargetMapper extends AppMapper {
  constructor() {
    super();
  }

  mapResponse(dto: TargetResponseDto): TargetResponseModel;
  mapResponse(model: TargetResponseModel): TargetResponseDto;
  mapResponse(input: TargetResponseDto | TargetResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseSearch(dto: SearchTargetResponseDto): SearchTargetResponseModel;
  mapResponseSearch(model: SearchTargetResponseModel): SearchTargetResponseDto;
  mapResponseSearch(input: SearchTargetResponseDto | SearchTargetResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapCreate(dto: CreateTargetRequestDto): CreateTargetRequestModel;
  mapCreate(model: CreateTargetRequestModel): CreateTargetRequestDto;
  mapCreate(input: CreateTargetRequestDto | CreateTargetRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapUpdate(model: UpdateTargetRequestModel): UpdateTargetRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapSearch(dto: SearchTargetRequestDto): SearchTargetRequestModel;
  mapSearch(model: SearchTargetRequestModel): SearchTargetRequestDto;
  mapSearch(input: SearchTargetRequestDto | SearchTargetRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapFilter(dto: FilterTargetRequestDto): FilterTargetRequestModel;
  mapFilter(model: FilterTargetRequestModel): FilterTargetRequestDto;
  mapFilter(input: FilterTargetRequestDto | FilterTargetRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
