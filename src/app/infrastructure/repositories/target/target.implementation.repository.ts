import { Injectable } from '@angular/core';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';

@Injectable({
  providedIn: 'root'
})
export class TargetImplementationRepository implements TargetRepository {
  constructor() {

  }
}
