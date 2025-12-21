import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {TargetMapper} from '@/app/domain/mappers/target/target.mapper';
import {CreateTargetRequestModel,FilterTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';
import {TargetResponseDto} from '@/app/infrastructure/dto/response/target-response.dto';
import {environment} from '@/environments/environment';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {HttpItemsModel} from '@/app/infrastructure/dto/http/http-default.model';


@Injectable({
  providedIn: 'root'
})
export class TargetService {
  itemMapper = new TargetMapper();
  constructor(private httpService: HttpService, private authRepository: AuthRepository) {
  }

  get getToken(): string {
    return this.authRepository.getToken();
  }

  async create(params: CreateTargetRequestModel): Promise<any> {
    return await this.httpService.post<any>(`${environment.endpoints.target.path}`, this.itemMapper.mapCreate(params), {}, this.getToken);
  }

  async delete(id: number): Promise<any> {
    return await this.httpService.delete<any>(`${environment.endpoints.target.path}${id}`, {}, this.getToken);
  }

  async get(params?: FilterTargetRequestModel): Promise<TargetResponseModel[]> {
    const response = await this.httpService.get<HttpItemsModel<TargetResponseDto[]>>(`${environment.endpoints.target.path}`, params, {}, this.getToken);
    return response.items.map((item: TargetResponseDto) => this.itemMapper.mapResponse(item));
  }

  async find(id: number): Promise<TargetResponseModel> {
    const response = await this.httpService.get<TargetResponseDto>(`${environment.endpoints.target.path}/${id}`, {},{}, this.getToken);
    return this.itemMapper.mapResponse(response);
  }
}
