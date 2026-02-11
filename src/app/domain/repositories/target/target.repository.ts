import {
  CreateTargetRequestModel,
  FilterTargetRequestModel,
  SearchTargetRequestModel
} from '@/app/domain/models/target/request/target-request.model';
import {
  SearchTargetResponseModel,
  TargetResponseModel
} from '@/app/domain/models/target/response/target-response.model';

export abstract class TargetRepository {
  abstract create(params: CreateTargetRequestModel): Promise<any>;
  abstract delete(id: string): Promise<any>;
  abstract get(params?: FilterTargetRequestModel): Promise<TargetResponseModel[]>;
  abstract find(id: number): Promise<TargetResponseModel>;
  abstract search(params?: SearchTargetRequestModel): Promise<SearchTargetResponseModel[]>;
}
