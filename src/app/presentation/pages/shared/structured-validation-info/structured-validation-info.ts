import { DatePipe, NgClass, isPlatformBrowser } from '@angular/common';
import { Component, OnDestroy, OnInit, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MarkdownModule } from 'ngx-markdown';
import { environment } from '@/environments/environment';
import { StructuredValidationRepository } from '@/app/domain/repositories/structured-validation/structured-validation.repository';
import { StructuredValidationTaskItemModel, StructuredValidationTaskResponseModel } from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
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
  readonly openComments = signal<string | null>(null);
  readonly commentUsername = signal('');
  readonly commentDrafts = signal<Record<string, string>>({});
  readonly answerDrafts = signal<Record<string, string>>({});
  readonly answerStatuses = signal<Record<string, string>>({});
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
    const items = this.task()?.items ?? [];
    const counts = {
      total: items.length,
      ok: 0,
      warning: 0,
      critical: 0,
      pending: 0,
    };

    for (const item of items) {
      if (['pending', 'in_progress'].includes(this.task()?.status ?? '') && !item.report.google_validation.executed && !item.report.schema_org_validation.executed && !item.success) {
        counts.pending += 1;
        continue;
      }
      if (item.severity === 'critical' || item.severity === 'error') counts.critical += 1;
      else if (item.severity === 'warning') counts.warning += 1;
      else if (item.severity === 'ok') counts.ok += 1;
      else counts.pending += 1;
    }

    return counts;
  });

  async ngOnInit(): Promise<void> {
    this.layout.set(this.route.snapshot.data['layout'] === 'admin' ? 'admin' : 'shared');
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
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
      if (!task || !['pending', 'in_progress'].includes(task.status)) return;
      await this.load(id, true);
    }, 10000);
  }

  async load(id: string, silent = false): Promise<void> {
    if (!silent) this.isLoading.set(true);
    try {
      const task = this.layout() === 'admin'
        ? await this.repository.find(id)
        : await this.repository.findPublic(id);
      this.task.set(task);
    } finally {
      if (!silent) this.isLoading.set(false);
    }
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
      failed: 'sv-badge sv-badge--danger',
      in_progress: 'sv-badge sv-badge--info',
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

  getSeverityLabel(severity: string | null): string {
    if (severity === 'critical') return 'Crítico';
    if (severity === 'error') return 'Error';
    if (severity === 'warning') return 'Warning';
    if (severity === 'ok') return 'OK';
    return 'Pendiente';
  }

  getReadableStatus(status: string): string {
    if (status === 'completed') return 'Completada';
    if (status === 'failed') return 'Fallida';
    if (status === 'in_progress') return 'En progreso';
    if (status === 'pending') return 'Pendiente';
    return status;
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

  toggleComments(itemKey: string): void {
    this.openComments.set(this.openComments() === itemKey ? null : itemKey);
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

  async rerunSameTask(): Promise<void> {
    const taskId = this.task()?.id;
    if (!taskId) return;
    await this.repository.rerun(taskId);
    await this.load(taskId, true);
  }

  async cloneTask(): Promise<void> {
    const task = this.task();
    if (!task) return;
    await this.router.navigate(['/admin/audit/structured-validations/create'], {
      state: {
        rerunData: {
          input_mode: task.input_mode,
          name: task.name,
          description: task.description,
          ai_instruction: task.ai_instruction,
          raw_urls: task.input_mode === 'url'
            ? task.items.map((entry) => entry.source_value).filter(Boolean).join('\n')
            : null,
          html_items: task.input_mode === 'html'
            ? task.items.map((entry) => entry.source_value).filter((value): value is string => Boolean(value))
            : [],
          get_ai_result: task.requested_ai_result,
          auto_extract_html: task.auto_extract_html,
          validate_google: task.validate_google,
          validate_schema_org: task.validate_schema_org,
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
