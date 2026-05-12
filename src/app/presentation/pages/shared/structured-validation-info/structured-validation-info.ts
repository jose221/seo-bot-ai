import { DatePipe, NgClass, isPlatformBrowser } from '@angular/common';
import { Component, OnDestroy, OnInit, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MarkdownModule } from 'ngx-markdown';
import { environment } from '@/environments/environment';
import { StructuredValidationRepository } from '@/app/domain/repositories/structured-validation/structured-validation.repository';
import { StructuredValidationTaskDetailRequestModel } from '@/app/domain/models/structured-validation/request/structured-validation-request.model';
import {
  StructuredValidationTaskControlAction,
  StructuredValidationTaskItemModel,
  StructuredValidationTaskResponseModel,
} from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
import { AnswerCommentRequestModel, CreatePublicCommentRequestModel } from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import { PublicCommentItemModel } from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import { RichResultsScreenshotModel, RichResultsValidatorDetailModel } from '@/app/domain/models/rich-results/response/rich-results-response.model';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';

const LS_USERNAME_KEY = 'structured-validation-comment-username';

@Component({
  standalone: true,
  imports: [RouterLink, NgClass, DatePipe, FormsModule, MarkdownModule],
  templateUrl: './structured-validation-info.html',
  styleUrl: './structured-validation-info.scss',
})
export default class StructuredValidationInfo implements OnInit, OnDestroy {
  private readonly repository = inject(StructuredValidationRepository);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly sweetAlert = inject(SweetAlertUtil);
  private readonly platformId = inject(PLATFORM_ID);

  readonly task = signal<StructuredValidationTaskResponseModel | null>(null);
  readonly commentsMap = signal<Map<string, PublicCommentItemModel[]>>(new Map());
  readonly isLoading = signal(true);
  readonly layout = signal<'admin' | 'shared'>('shared');
  readonly search = signal('');
  readonly severity = signal('all');
  readonly onlyIssues = signal(false);
  readonly currentPage = signal(1);
  readonly currentPageSize = signal(10);
  readonly selectedItemKey = signal<string | null>(null);
  readonly commentUsername = signal('');
  readonly commentDrafts = signal<Record<string, string>>({});
  readonly answerDrafts = signal<Record<string, string>>({});
  readonly answerStatuses = signal<Record<string, string>>({});
  readonly activeTaskAction = signal<StructuredValidationTaskControlAction | 'rerun' | null>(null);
  private readonly apiBase = environment.apiUrl.replace(/\/api\/v1\/?$/, '');

  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private photoSwipeInstance: { close: () => void } | null = null;

  readonly filteredItems = computed(() => {
    const query = this.search().trim().toLowerCase();
    return (this.task()?.items ?? []).filter((item) => {
      if (query && !`${item.label} ${item.source_preview ?? ''}`.toLowerCase().includes(query)) return false;
      if (this.severity() !== 'all' && (item.severity ?? 'unknown') !== this.severity()) return false;
      if (this.onlyIssues() && (item.severity === 'ok' || item.report.success)) return false;
      return true;
    });
  });

  readonly summary = computed(() => {
    return this.task()?.summary ?? {
      total: 0,
      ok: 0,
      warning: 0,
      critical: 0,
      error: 0,
      pending: 0,
    };
  });

  readonly selectedItem = computed(() => {
    const selectedKey = this.selectedItemKey();
    if (!selectedKey) return null;
    return (this.task()?.items ?? []).find((item) => item.item_key === selectedKey) ?? null;
  });

  readonly totalPages = computed(() => {
    const task = this.task();
    if (!task) return 1;
    return Math.max(1, Math.ceil(task.total_items / Math.max(task.page_size, 1)));
  });

  readonly paginationLabel = computed(() => {
    const task = this.task();
    if (!task || task.total_items === 0) return 'Sin elementos';
    const start = ((task.page - 1) * task.page_size) + 1;
    const end = Math.min(task.page * task.page_size, task.total_items);
    return `Mostrando ${start}-${end} de ${task.total_items}`;
  });

  async ngOnInit(): Promise<void> {
    this.layout.set(this.route.snapshot.data['layout'] === 'admin' ? 'admin' : 'shared');
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
    this.currentPage.set(this.readQueryNumber('page', 1));
    this.currentPageSize.set(this.readQueryNumber('page_size', 10));
    if (isPlatformBrowser(this.platformId)) {
      this.commentUsername.set(localStorage.getItem(LS_USERNAME_KEY) ?? '');
    }
    await this.load(id);
    await this.loadComments(id);
    this.startPolling(id);
  }

  ngOnDestroy(): void {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.photoSwipeInstance?.close();
  }

  private startPolling(id: string): void {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = setInterval(async () => {
      const task = this.task();
      if (!task || !['pending', 'in_progress', 'paused'].includes(task.status)) return;
      await this.load(id, true);
    }, 10000);
  }

  async load(id: string, silent = false): Promise<void> {
    if (!silent) this.isLoading.set(true);
    try {
      const params = new StructuredValidationTaskDetailRequestModel(this.currentPage(), this.currentPageSize());
      const task = this.layout() === 'admin'
        ? await this.repository.find(id, params)
        : await this.repository.findPublic(id, params);
      this.currentPage.set(task.page);
      this.currentPageSize.set(task.page_size);
      this.task.set(task);
      const selectedKey = this.selectedItemKey();
      if (selectedKey && !task.items.some((item) => item.item_key === selectedKey)) {
        this.selectedItemKey.set(null);
      }
    } finally {
      if (!silent) this.isLoading.set(false);
    }
  }

  private readQueryNumber(key: string, fallback: number): number {
    const rawValue = this.route.snapshot.queryParamMap.get(key);
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed) || parsed < 1) return fallback;
    return Math.trunc(parsed);
  }

  private async updatePaginationQueryParams(): Promise<void> {
    await this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        page: this.currentPage(),
        page_size: this.currentPageSize(),
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  async goToPage(page: number): Promise<void> {
    const taskId = this.task()?.id ?? this.route.snapshot.paramMap.get('id');
    if (!taskId) return;
    const normalizedPage = Math.max(1, Math.min(page, this.totalPages()));
    if (normalizedPage === this.currentPage()) return;
    this.currentPage.set(normalizedPage);
    await this.updatePaginationQueryParams();
    await this.load(taskId);
  }

  async updatePageSize(rawValue: number | string): Promise<void> {
    const taskId = this.task()?.id ?? this.route.snapshot.paramMap.get('id');
    if (!taskId) return;
    const parsedValue = Number(rawValue);
    const normalizedPageSize = Number.isFinite(parsedValue) && parsedValue > 0 ? Math.trunc(parsedValue) : 10;
    if (normalizedPageSize === this.currentPageSize() && this.currentPage() === 1) return;
    this.currentPageSize.set(normalizedPageSize);
    this.currentPage.set(1);
    await this.updatePaginationQueryParams();
    await this.load(taskId);
  }

  async loadComments(id: string): Promise<void> {
    const response = await this.repository.getPublicComments(id);
    const map = new Map<string, PublicCommentItemModel[]>();
    for (const comment of response.items) {
      const key = comment.schema_item_url;
      const list = map.get(key) ?? [];
      list.push(comment);
      map.set(key, list);
    }
    this.commentsMap.set(map);
  }

  getSeverityClass(severity: string | null): string {
    const map: Record<string, string> = {
      critical: 'sv-badge sv-badge--danger',
      error: 'sv-badge sv-badge--danger',
      warning: 'sv-badge sv-badge--warning',
      ok: 'sv-badge sv-badge--success',
      info: 'sv-badge sv-badge--info',
    };
    return map[severity ?? ''] ?? 'sv-badge sv-badge--neutral';
  }

  getStatusClass(status: string): string {
    const map: Record<string, string> = {
      completed: 'sv-badge sv-badge--success',
      cancelled: 'sv-badge sv-badge--neutral',
      failed: 'sv-badge sv-badge--danger',
      in_progress: 'sv-badge sv-badge--info',
      paused: 'sv-badge sv-badge--warning',
      pending: 'sv-badge sv-badge--warning',
    };
    return map[status] ?? 'sv-badge sv-badge--neutral';
  }

  getItemCardClass(severity: string | null, success: boolean): string {
    if (severity === 'critical' || severity === 'error') return 'structured-item-card structured-item-card--danger';
    if (severity === 'warning') return 'structured-item-card structured-item-card--warning';
    if (success) return 'structured-item-card structured-item-card--success';
    return 'structured-item-card structured-item-card--neutral';
  }

  getValidatorStateClass(success: boolean | null, executed: boolean, hasWarning: boolean, hasError: boolean): string {
    if (!executed) return 'sv-badge sv-badge--neutral';
    if (hasError) return 'sv-badge sv-badge--danger';
    if (hasWarning || success === false) return 'sv-badge sv-badge--warning';
    return 'sv-badge sv-badge--success';
  }

  getValidatorCardClass(success: boolean | null, executed: boolean, hasWarning: boolean, hasError: boolean): string {
    if (!executed) return 'validator-panel validator-panel--neutral';
    if (hasError) return 'validator-panel validator-panel--danger';
    if (hasWarning || success === false) return 'validator-panel validator-panel--warning';
    return 'validator-panel validator-panel--success';
  }

  getValidatorWarningCount(validator: RichResultsValidatorDetailModel): number {
    return validator.findings_summary.by_severity['warning'] || 0;
  }

  getValidatorErrorCount(validator: RichResultsValidatorDetailModel): number {
    return (validator.findings_summary.by_severity['critical'] || 0) + (validator.findings_summary.by_severity['error'] || 0);
  }

  getItemWarningCount(item: StructuredValidationTaskItemModel): number {
    return this.getValidatorWarningCount(item.report.google_validation) + this.getValidatorWarningCount(item.report.schema_org_validation);
  }

  getItemErrorCount(item: StructuredValidationTaskItemModel): number {
    return this.getValidatorErrorCount(item.report.google_validation) + this.getValidatorErrorCount(item.report.schema_org_validation);
  }

  getItemFindingsCount(item: StructuredValidationTaskItemModel): number {
    return item.report.google_validation.findings_summary.total + item.report.schema_org_validation.findings_summary.total;
  }

  getItemSourceText(item: StructuredValidationTaskItemModel): string {
    return item.source_preview || item.source_value || 'Sin origen disponible';
  }

  getItemSourceUrl(item: StructuredValidationTaskItemModel): string | null {
    return item.input_type === 'url' && item.source_value ? item.source_value : null;
  }

  openItemDetails(item: StructuredValidationTaskItemModel): void {
    this.selectedItemKey.set(item.item_key);
  }

  closeItemDetails(): void {
    this.selectedItemKey.set(null);
  }

  getValidatorStatusLabel(validator: RichResultsValidatorDetailModel): string {
    const warningCount = this.getValidatorWarningCount(validator);
    const errorCount = this.getValidatorErrorCount(validator);
    if (!validator.executed) return 'No ejecutado';
    if (errorCount > 0 || validator.error_message) return 'Error';
    if (warningCount > 0 || validator.success === false) return 'Warning';
    return 'OK';
  }

  getValidatorListForItem(item: StructuredValidationTaskItemModel): RichResultsValidatorDetailModel[] {
    return [item.report.google_validation, item.report.schema_org_validation];
  }

  getValidatorsWithResultUrl(item: StructuredValidationTaskItemModel): RichResultsValidatorDetailModel[] {
    return this.getValidatorListForItem(item).filter((validator) => validator.executed && !!validator.result_url);
  }

  getValidatorButtonLabel(validator: RichResultsValidatorDetailModel): string {
    if (validator.validator === 'google') return 'Google validator';
    if (validator.validator === 'schema_org') return 'Schema validator';
    return validator.label;
  }

  getSeverityLabel(severity: string | null): string {
    if (severity === 'critical') return 'Crítico';
    if (severity === 'error') return 'Error';
    if (severity === 'warning') return 'Warning';
    if (severity === 'ok') return 'OK';
    return 'Pendiente';
  }

  getReadableStatus(status: string): string {
    if (status === 'cancelled') return 'Cancelada';
    if (status === 'completed') return 'Completada';
    if (status === 'failed') return 'Fallida';
    if (status === 'in_progress') return 'En progreso';
    if (status === 'paused') return 'Pausada';
    if (status === 'pending') return 'Pendiente';
    return status;
  }

  isTaskActionLoading(action: StructuredValidationTaskControlAction | 'rerun'): boolean {
    return this.activeTaskAction() === action;
  }

  canPauseTask(): boolean {
    const task = this.task();
    return !!task?.supports_runtime_control && ['pending', 'in_progress'].includes(task.status);
  }

  canResumeTask(): boolean {
    const task = this.task();
    return !!task?.supports_runtime_control && task.status === 'paused';
  }

  canCancelTask(): boolean {
    const task = this.task();
    return !!task?.supports_runtime_control && ['pending', 'in_progress', 'paused'].includes(task.status);
  }

  canRestartTask(): boolean {
    const task = this.task();
    if (!task) return false;
    if (task.supports_runtime_control) return ['completed', 'failed', 'cancelled'].includes(task.status);
    return ['completed', 'failed'].includes(task.status);
  }

  getScreenshotPreviewUrl(assetUrl: string): string {
    if (!assetUrl) return '';
    if (/^https?:\/\//i.test(assetUrl)) return assetUrl;
    const normalizedPath = assetUrl.startsWith('/') ? assetUrl : `/${assetUrl}`;
    return `${this.apiBase}${normalizedPath}`;
  }

  getScreenshotApiPath(assetUrl: string): string {
    if (!assetUrl) return '/';
    if (/^https?:\/\//i.test(assetUrl)) {
      try {
        const parsed = new URL(assetUrl);
        return `${parsed.pathname}${parsed.search}`;
      } catch {
        return assetUrl;
      }
    }
    return assetUrl.startsWith('/') ? assetUrl : `/${assetUrl}`;
  }

  async openScreenshotGallery(screenshots: RichResultsScreenshotModel[], index: number): Promise<void> {
    if (!isPlatformBrowser(this.platformId) || screenshots.length === 0) return;

    const PhotoSwipe = (await import('photoswipe')).default;
    const dataSource = await Promise.all(screenshots.map((shot) => this.buildPhotoSwipeSlide(shot)));

    this.photoSwipeInstance?.close();
    const gallery = new PhotoSwipe({
      dataSource,
      index,
      bgOpacity: 0.92,
      showHideAnimationType: 'zoom',
      secondaryZoomLevel: 1.75,
      initialZoomLevel: 'fit',
      paddingFn: () => ({ top: 32, bottom: 32, left: 32, right: 32 }),
    });

    gallery.on('destroy', () => {
      if (this.photoSwipeInstance === gallery) this.photoSwipeInstance = null;
    });

    this.photoSwipeInstance = gallery;
    gallery.init();
  }

  private async buildPhotoSwipeSlide(shot: RichResultsScreenshotModel): Promise<{ src: string; width: number; height: number; alt: string }> {
    const src = this.getScreenshotPreviewUrl(shot.url);
    const dimensions = await this.getImageDimensions(src);
    return {
      src,
      width: dimensions.width,
      height: dimensions.height,
      alt: 'Screenshot de validación',
    };
  }

  private getImageDimensions(src: string): Promise<{ width: number; height: number }> {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve({ width: img.naturalWidth || 1600, height: img.naturalHeight || 900 });
      img.onerror = () => resolve({ width: 1600, height: 900 });
      img.src = src;
    });
  }

  commentsFor(itemKey: string): PublicCommentItemModel[] {
    return this.commentsMap().get(itemKey) ?? [];
  }

  async submitComment(itemKey: string): Promise<void> {
    const username = this.commentUsername().trim();
    const comment = (this.commentDrafts()[itemKey] ?? '').trim();
    const taskId = this.task()?.id;
    if (!username || !comment || !taskId) return;
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem(LS_USERNAME_KEY, username);
    }
    const created = await this.repository.createPublicComment(
      itemKey,
      taskId,
      new CreatePublicCommentRequestModel(username, comment),
    );
    const map = new Map(this.commentsMap());
    map.set(itemKey, [created as any, ...(map.get(itemKey) ?? [])]);
    this.commentsMap.set(map);
    this.commentDrafts.set({ ...this.commentDrafts(), [itemKey]: '' });
  }

  async answerComment(comment: PublicCommentItemModel): Promise<void> {
    const answer = (this.answerDrafts()[comment.id] ?? '').trim();
    const status = this.answerStatuses()[comment.id] ?? 'done';
    if (!answer) return;
    await this.repository.answerComment(comment.id, new AnswerCommentRequestModel(answer, status));
    const map = new Map(this.commentsMap());
    for (const [key, values] of map.entries()) {
      const idx = values.findIndex((item) => item.id === comment.id);
      if (idx >= 0) {
        values[idx] = { ...values[idx], answer, status, answered_at: new Date().toISOString() };
        map.set(key, [...values]);
      }
    }
    this.commentsMap.set(map);
  }

  async triggerTaskAction(
    action: StructuredValidationTaskControlAction,
    options: {
      title: string;
      text: string;
      confirmButtonText: string;
    },
  ): Promise<void> {
    const taskId = this.task()?.id;
    if (!taskId) return;
    const confirmation = await this.sweetAlert.fire({
      title: options.title,
      text: options.text,
      icon: action === 'cancel' ? 'warning' : 'question',
      showCancelButton: true,
      confirmButtonText: options.confirmButtonText,
      cancelButtonText: 'Cerrar',
    });
    if (!confirmation.isConfirmed) return;

    this.activeTaskAction.set(action);
    try {
      const updatedTask = await this.repository.controlTask(taskId, action);
      this.task.set(updatedTask);
    } catch (error: any) {
      await this.sweetAlert.error('', error?.response?.data?.detail || 'No se pudo actualizar la tarea.');
    } finally {
      this.activeTaskAction.set(null);
    }
  }

  async rerunSameTask(): Promise<void> {
    const task = this.task();
    if (!task) return;
    const confirmation = await this.sweetAlert.fire({
      title: task.supports_runtime_control ? 'Reiniciar tarea' : 'Re-ejecutar tarea',
      text: 'La tarea se volverá a ejecutar con los mismos parámetros.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: task.supports_runtime_control ? 'Reiniciar' : 'Re-ejecutar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmation.isConfirmed) return;

    this.activeTaskAction.set('rerun');
    try {
      if (task.supports_runtime_control) {
        this.task.set(await this.repository.controlTask(task.id, 'restart'));
      } else {
        await this.repository.rerun(task.id);
        await this.load(task.id, true);
      }
    } catch (error: any) {
      await this.sweetAlert.error('', error?.response?.data?.detail || 'No se pudo reiniciar la tarea.');
    } finally {
      this.activeTaskAction.set(null);
    }
  }

  async pauseTask(): Promise<void> {
    await this.triggerTaskAction('pause', {
      title: 'Pausar tarea',
      text: 'La tarea dejará de tomar nuevos elementos hasta que la reanudes.',
      confirmButtonText: 'Pausar',
    });
  }

  async resumeTask(): Promise<void> {
    await this.triggerTaskAction('resume', {
      title: 'Reanudar tarea',
      text: 'La tarea continuará procesando los elementos pendientes.',
      confirmButtonText: 'Reanudar',
    });
  }

  async cancelTask(): Promise<void> {
    await this.triggerTaskAction('cancel', {
      title: 'Cancelar tarea',
      text: 'Se conservará el avance actual, pero no se procesarán más elementos.',
      confirmButtonText: 'Cancelar tarea',
    });
  }

  async cloneTask(): Promise<void> {
    const task = this.task();
    if (!task) return;
    const fullTask = await this.repository.find(task.id, {
      page: 1,
      page_size: Math.max(task.total_items, 1),
    });
    await this.router.navigate(['/admin/audit/structured-validations/create'], {
      state: {
        rerunData: {
          input_mode: fullTask.input_mode,
          name: fullTask.name,
          description: fullTask.description,
          ai_instruction: fullTask.ai_instruction,
          browser_mode_code: fullTask.browser_mode_code,
          raw_urls: fullTask.input_mode === 'url'
            ? fullTask.items.map((entry) => entry.source_value).filter(Boolean).join('\n')
            : null,
          html_items: fullTask.input_mode === 'html'
            ? fullTask.items.map((entry) => entry.source_value).filter((value): value is string => Boolean(value))
            : [],
          get_ai_result: fullTask.requested_ai_result,
          auto_extract_html: fullTask.auto_extract_html,
          validate_google: fullTask.validate_google,
          validate_schema_org: fullTask.validate_schema_org,
        },
      },
    });
  }

  async copySharedUrl(): Promise<void> {
    const taskId = this.task()?.id;
    if (!taskId) return;
    await navigator.clipboard.writeText(`${environment.appUrl}/shared/audit/structured-validations/${taskId}/info`);
    await this.sweetAlert.fire({
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 2400,
      icon: 'success',
      title: 'URL pública copiada',
    });
  }

  setCommentDraft(itemKey: string, value: string): void {
    this.commentDrafts.set({ ...this.commentDrafts(), [itemKey]: value });
  }

  setAnswerDraft(commentId: string, value: string): void {
    this.answerDrafts.set({ ...this.answerDrafts(), [commentId]: value });
  }

  setAnswerStatus(commentId: string, value: string): void {
    this.answerStatuses.set({ ...this.answerStatuses(), [commentId]: value });
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

  async showTaskMessage(): Promise<void> {
    const taskId = this.task()?.id;
    if (!taskId) return;

    try {
      const logs = await this.repository.getLogs(taskId);
      const fallback = this.task()?.progress_message || this.task()?.message || 'No hay mensajes registrados todavía.';
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
      console.error('Error loading structured validation logs:', error);
      await this.sweetAlert.error('', 'No se pudieron cargar los mensajes de la tarea.');
    }
  }
}
