import { DatePipe, NgClass } from '@angular/common';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { StructuredValidationRepository } from '@/app/domain/repositories/structured-validation/structured-validation.repository';
import { StructuredValidationTaskListItemModel } from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
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

  readonly isLoading = signal(true);
  readonly items = signal<StructuredValidationTaskListItemModel[]>([]);
  readonly autoReload = signal(true);

  private intervalId: ReturnType<typeof setInterval> | null = null;

  async ngOnInit(): Promise<void> {
    await this.load();
    this.intervalId = setInterval(() => {
      if (this.autoReload()) this.load(true);
    }, 10000);
  }

  ngOnDestroy(): void {
    if (this.intervalId) clearInterval(this.intervalId);
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

  getStatusClass(status: string): string {
    const map: Record<string, string> = {
      completed: 'bg-success',
      failed: 'bg-danger',
      in_progress: 'bg-info text-dark',
      pending: 'bg-warning text-dark',
    };
    return map[status] ?? 'bg-secondary';
  }

  async openClone(item: StructuredValidationTaskListItemModel): Promise<void> {
    const detail = await this.repository.find(item.id);
    await this.router.navigate(['/admin/audit/structured-validations/create'], {
      state: {
        rerunData: {
          input_mode: detail.input_mode,
          name: detail.name,
          description: detail.description,
          ai_instruction: detail.ai_instruction,
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
    const confirmation = await this.sweetAlert.fire({
      title: 'Reejecutar tarea',
      text: 'La tarea se volverá a ejecutar con los mismos parámetros.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Reejecutar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmation.isConfirmed) return;
    await this.repository.rerun(item.id);
    await this.load(true);
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
    await this.repository.delete(item.id);
    await this.load(true);
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
