import {
  CreateTargetRequestModel,
  FilterTargetRequestModel,
  SearchTargetRequestModel,
  UpdateTargetRequestModel
} from '@/app/domain/models/target/request/target-request.model';
import {
  SearchTargetResponseModel,
  TargetHtmlResponseModel,
  TargetResponseModel
} from '@/app/domain/models/target/response/target-response.model';

export abstract class TargetRepository {
  abstract create(params: CreateTargetRequestModel): Promise<any>;
  abstract update(id: string, params: UpdateTargetRequestModel): Promise<any>;
  abstract delete(id: string): Promise<any>;
  abstract get(params?: FilterTargetRequestModel): Promise<TargetResponseModel[]>;
  abstract find(id: string): Promise<TargetResponseModel>;
  abstract search(params?: SearchTargetRequestModel): Promise<SearchTargetResponseModel[]>;
  abstract getTags(): Promise<string[]>;
  abstract getHtml(url: string): Promise<TargetHtmlResponseModel>;
}
