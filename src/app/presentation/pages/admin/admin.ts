import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import {Router, RouterLink, RouterLinkActive, RouterOutlet} from '@angular/router';
import {TranslatePipe} from '@ngx-translate/core';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import { TaskNotificationService } from '@/app/infrastructure/services/general/task-notification.service';

@Component({
  selector: 'app-admin',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './admin.html',
  styleUrl: './admin.scss',
})
export class Admin implements OnInit, OnDestroy {
  router = inject(Router);
  authRepository = inject(AuthRepository);
  notificationService = inject(TaskNotificationService);

  ngOnInit(): void {
    this.notificationService.start();
  }

  ngOnDestroy(): void {
    this.notificationService.stop();
  }

  isActive(route: string): boolean {
    return this.router.url.includes(route);
  }
  async logout(){
    this.notificationService.stop();
    this.authRepository.logout();
    await this.router.navigateByUrl('/');
  }

}
