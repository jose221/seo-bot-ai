import { Injectable, signal } from '@angular/core';

export type ToastVariant = 'success' | 'danger' | 'warning' | 'info';

export interface ToastItem {
  id: number;
  title: string;
  message: string;
  variant: ToastVariant;
}

@Injectable({
  providedIn: 'root',
})
export class ToastService {
  readonly items = signal<ToastItem[]>([]);
  private nextId = 1;

  success(message: string, title: string = 'Éxito', durationMs: number = 3500): void {
    this.show({ title, message, variant: 'success' }, durationMs);
  }

  error(message: string, title: string = 'Error', durationMs: number = 4500): void {
    this.show({ title, message, variant: 'danger' }, durationMs);
  }

  remove(id: number): void {
    this.items.update((current) => current.filter((item) => item.id !== id));
  }

  private show(
    toast: Omit<ToastItem, 'id'>,
    durationMs: number,
  ): void {
    const id = this.nextId++;
    this.items.update((current) => [...current, { ...toast, id }]);

    if (durationMs > 0) {
      window.setTimeout(() => this.remove(id), durationMs);
    }
  }
}
