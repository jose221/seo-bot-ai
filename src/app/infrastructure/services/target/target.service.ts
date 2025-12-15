import { Injectable } from '@angular/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {TargetMapper} from '@/app/domain/mappers/target/target.mapper';

@Injectable({
  providedIn: 'root'
})
export class TargetService {
  itemMapper = new TargetMapper();
  constructor(private httpService: HttpService) {
  }
}
