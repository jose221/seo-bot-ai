import { Component, inject } from '@angular/core';
import {Router, RouterLink, RouterLinkActive, RouterOutlet} from '@angular/router';
import {TranslatePipe} from '@ngx-translate/core';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';

@Component({
  selector: 'app-admin',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './admin.html',
  styleUrl: './admin.scss',
})
export class Admin {
  router = inject(Router);
  authRepository = inject(AuthRepository);
  isActive(route: string): boolean {
    return this.router.url.includes(route);
  }
  async logout(){
    this.authRepository.logout();
    await this.router.navigateByUrl('/');
  }

}
