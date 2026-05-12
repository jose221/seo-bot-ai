import { DatePipe, NgClass } from '@angular/common';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { StructuredValidationRepository } from '@/app/domain/repositories/structured-validation/structured-validation.repository';
import {
  StructuredValidationTaskControlAction,
  StructuredValidationTaskListItemModel,
} from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
import {
  StructuredValidationTaskChangedEvent,
  TaskNotificationService,
} from '@/app/infrastructure/services/general/task-notification.service';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';

@Component({
  selector: 'app-structured-validation-list',
  standalone: true,
  imports: [RouterLink, DatePipe, NgClass],
  templateUrl: './structured-validation-list.html',
  styleUrl: './structured-validation-list.scss',
})
export class StructuredValidationList implements OnInit, OnDestroy {
  private readonly repository = inject(StructuredValidationRepository);
  private readonly router = inject(Router);
  private readonly sweetAlert = inject(SweetAlertUtil);
  private readonly taskNotificationService = inject(TaskNotificationService);

  readonly isLoading = signal(true);
  readonly items = signal<StructuredValidationTaskListItemModel[]>([]);
  readonly autoReload = signal(true);
  readonly activeActions = signal<Record<string, string>>({});

  private taskChangesSubscription: Subscription | null = null;

  async ngOnInit(): Promise<void> {
    this.taskNotificationService.start();
    await this.load();
    this.taskChangesSubscription = this.taskNotificationService
      .structuredValidationTaskChanges()
      .subscribe((event) => this.applyRealtimeChange(event));
  }

  ngOnDestroy(): void {
    this.taskChangesSubscription?.unsubscribe();
    this.taskChangesSubscription = null;
  }

  async load(silent = false): Promise<void> {
    if (!silent) this.isLoading.set(true);
    try {
      const response = await this.repository.getAll();
      this.items.set(response.items);
    } finally {
      if (!silent) this.isLoading.set(false);
    }
  }

  private applyRealtimeChange(event: StructuredValidationTaskChangedEvent): void {
    if (!this.autoReload()) return;

    const currentItems = [...this.items()];

    if (event.action === 'deleted') {
      this.items.set(currentItems.filter((item) => item.id !== event.task_id));
      return;
    }

    const payload = event.list_item as StructuredValidationTaskListItemModel | undefined;
    if (!payload) return;

    const item = new StructuredValidationTaskListItemModel(
      payload.id,
      payload.task_kind,
      payload.supports_runtime_control,
      payload.input_mode,
      payload.name,
      payload.description,
      payload.status,
      payload.progress_percentage,
      payload.progress_message,
      payload.total_items,
      payload.completed_items,
      payload.successful_items,
      payload.failed_items,
      payload.validate_google,
      payload.validate_schema_org,
      payload.requested_ai_result,
      payload.created_at,
      payload.completed_at,
    );

    const existingIndex = currentItems.findIndex((entry) => entry.id === item.id);
    if (existingIndex >= 0) {
      currentItems[existingIndex] = item;
      this.items.set(currentItems);
      return;
    }

    if (event.action === 'created') {
      this.items.set([item, ...currentItems].slice(0, 20));
    }
  }

  getStatusClass(status: string): string {
    const map: Record<string, string> = {
      cancelled: 'bg-secondary',
      completed: 'bg-success',
      failed: 'bg-danger',
      in_progress: 'bg-info text-dark',
      paused: 'bg-warning text-dark',
      pending: 'bg-warning text-dark',
    };
    return map[status] ?? 'bg-secondary';
  }

  isActionLoading(item: StructuredValidationTaskListItemModel, action: string): boolean {
    return this.activeActions()[item.id] === action;
  }

  private setActionLoading(itemId: string, action: string | null): void {
    const current = { ...this.activeActions() };
    if (action) current[itemId] = action;
    else delete current[itemId];
    this.activeActions.set(current);
  }

  canPause(item: StructuredValidationTaskListItemModel): boolean {
    return item.supports_runtime_control && ['pending', 'in_progress'].includes(item.status);
  }

  canResume(item: StructuredValidationTaskListItemModel): boolean {
    return item.supports_runtime_control && item.status === 'paused';
  }

  canCancel(item: StructuredValidationTaskListItemModel): boolean {
    return item.supports_runtime_control && ['pending', 'in_progress', 'paused'].includes(item.status);
  }

  canRestart(item: StructuredValidationTaskListItemModel): boolean {
    if (item.supports_runtime_control) return ['completed', 'failed', 'cancelled'].includes(item.status);
    return ['completed', 'failed'].includes(item.status);
  }

  async openClone(item: StructuredValidationTaskListItemModel): Promise<void> {
    const detail = await this.repository.find(item.id, {
      page: 1,
      page_size: Math.max(item.total_items, 1),
    });
    await this.router.navigate(['/admin/audit/structured-validations/create'], {
      state: {
        rerunData: {
          input_mode: detail.input_mode,
          name: detail.name,
          description: detail.description,
          ai_instruction: detail.ai_instruction,
          browser_mode_code: detail.browser_mode_code,
          raw_urls: detail.input_mode === 'url'
            ? detail.items.map((entry) => entry.source_value).filter(Boolean).join('\n')
            : null,
          html_items: detail.input_mode === 'html'
            ? detail.items.map((entry) => entry.source_value).filter((value): value is string => Boolean(value))
            : [],
          get_ai_result: detail.requested_ai_result,
          auto_extract_html: detail.auto_extract_html,
          validate_google: detail.validate_google,
          validate_schema_org: detail.validate_schema_org,
        },
      },
    });
  }

  async rerun(item: StructuredValidationTaskListItemModel): Promise<void> {
    if (!this.canRestart(item)) return;
    const confirmation = await this.sweetAlert.fire({
      title: item.supports_runtime_control ? 'Reiniciar tarea' : 'Re-ejecutar tarea',
      text: 'La tarea se volverá a ejecutar con los mismos parámetros.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: item.supports_runtime_control ? 'Reiniciar' : 'Re-ejecutar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmation.isConfirmed) return;
    this.setActionLoading(item.id, 'rerun');
    try {
      if (item.supports_runtime_control) await this.repository.controlTask(item.id, 'restart');
      else await this.repository.rerun(item.id);
      await this.load(true);
    } catch (error: any) {
      await this.sweetAlert.error('', error?.response?.data?.detail || 'No se pudo reiniciar la tarea.');
    } finally {
      this.setActionLoading(item.id, null);
    }
  }

  async controlTask(
    item: StructuredValidationTaskListItemModel,
    action: StructuredValidationTaskControlAction,
    options: {
      title: string;
      text: string;
      confirmButtonText: string;
    },
  ): Promise<void> {
    const confirmation = await this.sweetAlert.fire({
      title: options.title,
      text: options.text,
      icon: action === 'cancel' ? 'warning' : 'question',
      showCancelButton: true,
      confirmButtonText: options.confirmButtonText,
      cancelButtonText: 'Cerrar',
    });
    if (!confirmation.isConfirmed) return;
    this.setActionLoading(item.id, action);
    try {
      await this.repository.controlTask(item.id, action);
      await this.load(true);
    } catch (error: any) {
      await this.sweetAlert.error('', error?.response?.data?.detail || 'No se pudo actualizar la tarea.');
    } finally {
      this.setActionLoading(item.id, null);
    }
  }

  async pause(item: StructuredValidationTaskListItemModel): Promise<void> {
    await this.controlTask(item, 'pause', {
      title: 'Pausar tarea',
      text: 'La tarea dejará de tomar nuevos elementos hasta que la reanudes.',
      confirmButtonText: 'Pausar',
    });
  }

  async resume(item: StructuredValidationTaskListItemModel): Promise<void> {
    await this.controlTask(item, 'resume', {
      title: 'Reanudar tarea',
      text: 'La tarea continuará con los elementos pendientes.',
      confirmButtonText: 'Reanudar',
    });
  }

  async cancel(item: StructuredValidationTaskListItemModel): Promise<void> {
    await this.controlTask(item, 'cancel', {
      title: 'Cancelar tarea',
      text: 'Se conservará el avance actual, pero no se procesarán más elementos.',
      confirmButtonText: 'Cancelar tarea',
    });
  }

  async remove(item: StructuredValidationTaskListItemModel): Promise<void> {
    const confirmation = await this.sweetAlert.fire({
      title: 'Eliminar tarea',
      text: 'Esta acción no se puede deshacer.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Eliminar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmation.isConfirmed) return;
    try {
      await this.repository.delete(item.id);
      await this.load(true);
    } catch (error: any) {
      await this.sweetAlert.error('', error?.response?.data?.detail || 'No se pudo eliminar la tarea.');
    }
  }

  formatDate(dateStr: string): string {
    try {
      return new Date(dateStr).toLocaleString('es-MX', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  }

  escapeHtml(value: string): string {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  async showTaskMessage(item: StructuredValidationTaskListItemModel): Promise<void> {
    try {
      const logs = await this.repository.getLogs(item.id);
      const fallback = item.progress_message || item.description || 'No hay mensajes registrados todavía.';
      const content = logs.items.length
        ? logs.items
            .map(
              (log) =>
                `[${this.formatDate(log.created_at)}] ${String(log.level || 'info').toUpperCase()}${log.progress_percentage != null ? ` (${log.progress_percentage}%)` : ''}\n${log.message}`,
            )
            .join('\n\n')
        : fallback;

      await this.sweetAlert.fire({
        title: 'Mensaje de tarea',
        html: `<div style="text-align:left; max-height:60vh; overflow:auto;"><pre style="white-space:pre-wrap; margin:0;">${this.escapeHtml(content)}</pre></div>`,
        width: 800,
        confirmButtonText: 'Cerrar',
      });
    } catch (error) {
      console.error('Error al cargar logs de la tarea estructurada:', error);
      await this.sweetAlert.error('', 'No se pudieron cargar los mensajes de la tarea.');
    }
  }
}
