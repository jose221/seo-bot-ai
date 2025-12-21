import { Injectable } from '@angular/core';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
import {CreateTargetRequestModel, FilterTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';
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
  async delete(id: number): Promise<any> {
    return await this.primaryService.delete(id);
  }
  async get(params?: FilterTargetRequestModel): Promise<TargetResponseModel[]> {
    return await this.primaryService.get(params);
  }
  async find(id: number): Promise<TargetResponseModel> {
    return await this.primaryService.find(id);
  }
}
