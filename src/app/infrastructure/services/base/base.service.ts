import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {inject, Injectable} from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class BaseService {
  private authRepository = inject(AuthRepository);

  public get getToken(): string {
    return this.authRepository.getToken();
  }
}
