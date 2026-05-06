import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';

import { ToastService } from '@/app/helper/toast.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="toast-container position-fixed top-0 end-0 p-3">
      <div
        *ngFor="let item of toastService.items()"
        class="toast show border-0 shadow-sm mb-2"
        [ngClass]="toastClass(item.variant)"
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
      >
        <div class="toast-header" [ngClass]="headerClass(item.variant)">
          <strong class="me-auto">{{ item.title }}</strong>
          <button
            type="button"
            class="btn-close"
            aria-label="Close"
            (click)="toastService.remove(item.id)"
          ></button>
        </div>
        <div class="toast-body">{{ item.message }}</div>
      </div>
    </div>
  `,
})
export class AppToast {
  readonly toastService = inject(ToastService);

  toastClass(variant: string): string {
    return {
      success: 'text-bg-success',
      danger: 'text-bg-danger',
      warning: 'text-bg-warning text-dark',
      info: 'text-bg-info text-dark',
    }[variant] ?? 'text-bg-secondary';
  }

  headerClass(variant: string): string {
    return {
      success: 'bg-success-subtle text-success-emphasis',
      danger: 'bg-danger-subtle text-danger-emphasis',
      warning: 'bg-warning-subtle text-warning-emphasis',
      info: 'bg-info-subtle text-info-emphasis',
    }[variant] ?? 'bg-body-tertiary';
  }
}
