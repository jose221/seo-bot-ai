import {FilterTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {FilterTargetRequestDto} from '@/app/infrastructure/dto/request/target-request.dto';
import {CreateTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {CreateTargetRequestDto} from '@/app/infrastructure/dto/request/target-request.dto';
import { AppMapper } from "../app.mapper";
import {TargetRequestDto} from '@/app/infrastructure/dto/request/target-request.dto';
import {TargetResponseDto} from '@/app/infrastructure/dto/response/target-response.dto';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';


export class TargetMapper extends AppMapper {
  constructor() {
    super();
  }

  // --------- mapResponse (sobrecargas)
  mapResponse(dto: TargetResponseDto): TargetResponseModel;
  mapResponse(model: TargetResponseModel): TargetResponseDto;
  mapResponse(input: TargetResponseDto | TargetResponseModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapCreate (sobrecargas)
  mapCreate(dto: CreateTargetRequestDto): CreateTargetRequestModel;
  mapCreate(model: CreateTargetRequestModel): CreateTargetRequestDto;
  mapCreate(input: CreateTargetRequestDto | CreateTargetRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }

  // --------- mapFilter (sobrecargas)
  mapFilter(dto: FilterTargetRequestDto): FilterTargetRequestModel;
  mapFilter(model: FilterTargetRequestModel): FilterTargetRequestDto;
  mapFilter(input: FilterTargetRequestDto | FilterTargetRequestModel) {
    return this.autoMap<any, any>(input, { except: [] });
  }
}
