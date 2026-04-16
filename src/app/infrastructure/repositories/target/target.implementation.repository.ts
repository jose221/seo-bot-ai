import { Injectable } from '@angular/core';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
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
import {TargetService} from '@/app/infrastructure/services/target/target.service';

@Injectable({
  providedIn: 'root'
})
export class TargetImplementationRepository implements TargetRepository {
  constructor(private primaryService: TargetService) {

  }
  async create(params: CreateTargetRequestModel): Promise<any> {
    return await this.primaryService.create(params);
  }
  async update(id: string, params: UpdateTargetRequestModel): Promise<any> {
    return await this.primaryService.update(id, params);
  }
  async delete(id: string): Promise<any> {
    return await this.primaryService.delete(id);
  }
  async get(params?: FilterTargetRequestModel): Promise<TargetResponseModel[]> {
    return await this.primaryService.get(params);
  }
  async find(id: string): Promise<TargetResponseModel> {
    return await this.primaryService.find(id);
  }
  async search(params?: SearchTargetRequestModel): Promise<SearchTargetResponseModel[]> {
    return await this.primaryService.search(params);
  }
  async getTags(): Promise<string[]> {
    return await this.primaryService.getTags();
  }
  async getHtml(url: string): Promise<TargetHtmlResponseModel> {
    return await this.primaryService.getHtml(url);
  }
}
