import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {TargetMapper} from '@/app/domain/mappers/target/target.mapper';
import {CreateTargetRequestModel,FilterTargetRequestModel,UpdateTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';
import {TargetResponseDto} from '@/app/infrastructure/dto/response/target-response.dto';
import {HttpClientHelper} from '@/app/helper/http-client.helper';


@Injectable({
  providedIn: 'root'
})
export class TargetService {
  itemMapper = new TargetMapper();
  constructor(private httpService: HttpService) {
  }

  async create(params: CreateTargetRequestModel): Promise<any> {
    return await this.httpService.post<any>('', this.itemMapper.mapCreate(params));
  }

  async update(params: UpdateTargetRequestModel): Promise<any> {
    return await this.httpService.put<any>('', this.itemMapper.mapUpdate(params));
  }

  async delete(id: number): Promise<any> {
    return await this.httpService.delete<any>('/' + id);
  }

  async get(params?: FilterTargetRequestModel): Promise<TargetResponseModel[]> {
    let nParams = params ? HttpClientHelper.objectToQueryString(params ? this.itemMapper.mapFilter(params) : '') : '';
    const response = await this.httpService.get<TargetResponseDto[]>('?' + nParams);
    return response.map(item => this.itemMapper.mapResponse(item));
  }

  async find(id: number): Promise<TargetResponseModel> {
    const response = await this.httpService.get<TargetResponseDto>('/' + id);
    return this.itemMapper.mapResponse(response);
  }
}
