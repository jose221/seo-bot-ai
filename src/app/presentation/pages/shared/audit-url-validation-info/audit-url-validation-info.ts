import { Component, inject, signal, OnInit, OnDestroy, computed, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { TaskNotificationService } from '@/app/infrastructure/services/general/task-notification.service';
import { AuthRepository } from '@/app/domain/repositories/auth/auth.repository';
import { TargetRepository } from '@/app/domain/repositories/target/target.repository';
import { RichResultsRepository } from '@/app/domain/repositories/rich-results/rich-results.repository';
import { StructuredValidationRepository } from '@/app/domain/repositories/structured-validation/structured-validation.repository';
import {
  AuditUrlValidationSchemasResponseModel,
  AuditUrlValidationSchemaItemModel,
  PublicCommentItemModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  CreatePublicCommentRequestModel,
  AnswerCommentRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import {
  CreateRichResultsBatchReportRequestModel,
  CreateRichResultsReportRequestModel,
} from '@/app/domain/models/rich-results/request/rich-results-request.model';
import { StructuredValidationCreateRequestModel } from '@/app/domain/models/structured-validation/request/structured-validation-request.model';
import {
  RichResultsAnalysisFindingModel,
  RichResultsAnalysisSummaryModel,
  RichResultsReportDetailResponseModel,
  RichResultsReportListItemModel,
  RichResultsReportStatusSummaryItemModel,
  RichResultsReportTaskResponseModel,
  RichResultsValidatorDetailModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';
import { TranslateModule } from '@ngx-translate/core';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { MarkdownModule } from 'ngx-markdown';
import { FormsModule } from '@angular/forms';
import { environment } from '@/environments/environment';

const LS_USERNAME_KEY = 'public_validator_username';
type AuditUrlValidationInfoLayout = 'admin' | 'shared';
type TrackedRichResultsTask = {
  url: string;
  status: string;
};

@Component({
  selector: 'app-public-audit-url-validation-info',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TranslateModule,
    MarkdownModule,
    FormsModule
  ],
  templateUrl: './audit-url-validation-info.html',
  styleUrl: './audit-url-validation-info.scss'
})
export default class PublicAuditUrlValidationInfoComponent implements OnInit, OnDestroy {
  private readonly _route = inject(ActivatedRoute);
  private readonly _router = inject(Router);
  private readonly _repository = inject(AuditUrlValidationRepository);
  private readonly _taskNotificationService = inject(TaskNotificationService);
  private readonly _authRepository = inject(AuthRepository);
  private readonly _targetRepository = inject(TargetRepository);
  private readonly _richResultsRepository = inject(RichResultsRepository);
  private readonly _structuredValidationRepository = inject(StructuredValidationRepository);
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);
  private readonly _platformId = inject(PLATFORM_ID);

  isLoading = signal<boolean>(true);
  data = signal<AuditUrlValidationSchemasResponseModel | null>(null);
  validationId = signal<string | null>(null);
  showFilters = signal<boolean>(true);
  layout = signal<AuditUrlValidationInfoLayout>('shared');

  // Filters
  searchTerm = signal<string>('');
  severityFilter = signal<string>('');
  typeFilter = signal<string>('');
  onlyWithErrors = signal<boolean>(false);
  richResultsHistoryFilter = signal<string>('all');

  // Accordion
  expandedCards = signal<Set<number>>(new Set([0]));

  // Modal expand
  modalSchema = signal<AuditUrlValidationSchemaItemModel | null>(null);
  modalTab = signal<'schema' | 'report'>('schema');

  // Auth
  isLoggedIn = signal<boolean>(false);

  isAdminView = computed(() => this.layout() === 'admin');

  // Comments
  commentsMap = signal<Map<string, PublicCommentItemModel[]>>(new Map());
  commentsLoadingSet = signal<Set<string>>(new Set());
  openCommentSection = signal<string | null>(null);
  commentUsername = signal<string>('');
  commentText = signal<string>('');
  commentSubmitting = signal<boolean>(false);

  // Answer comment (admin only)
  answerCommentTarget = signal<PublicCommentItemModel | null>(null);
  answerText = signal<string>('');
  answerStatus = signal<string>('done');
  answerSubmitting = signal<boolean>(false);

  // Rerun
  rerunLoading = signal<boolean>(false);
  rerunUrlTarget = signal<string | null>(null);

  // HTML fetch
  htmlLoading = signal<boolean>(false);
  richResultsMap = signal<Map<string, RichResultsReportListItemModel[]>>(new Map());
  richResultsLoadingSet = signal<Set<string>>(new Set());
  richResultsCreatingSet = signal<Set<string>>(new Set());
  richResultsDeletingSet = signal<Set<string>>(new Set());
  richResultsExpandedSet = signal<Set<string>>(new Set());
  richResultsDetailMap = signal<Map<string, RichResultsReportDetailResponseModel>>(new Map());
  richResultsStatusMap = signal<Map<string, RichResultsReportStatusSummaryItemModel>>(new Map());
  selectedRichResultsUrls = signal<Set<string>>(new Set());
  richResultsBatchSubmitting = signal<boolean>(false);
  autoReload = signal<boolean>(true);
  richResultsBatchAnalyzeWithAi = signal<boolean>(true);
  richResultsBatchAutoExtractHtml = signal<boolean>(false);
  richResultsBatchValidateGoogle = signal<boolean>(true);
  richResultsBatchValidateSchemaOrg = signal<boolean>(true);
  richResultsSingleAnalyzeWithAi = signal<boolean>(true);
  richResultsSingleAutoExtractHtml = signal<boolean>(false);
  richResultsSingleValidateGoogle = signal<boolean>(true);
  richResultsSingleValidateSchemaOrg = signal<boolean>(true);
  private richResultsPollTimer: ReturnType<typeof setInterval> | null = null;
  private readonly richResultsApiBase = environment.apiUrl.replace(/\/api\/v1\/?$/, '');
  private readonly trackedRichResultsTasks = new Map<string, TrackedRichResultsTask>();

  availableTypes = computed(() => {
    const schemas = this.data()?.schemas ?? [];
    const types = new Set<string>();
    schemas.forEach(s => {
      s.schema_types_found?.forEach(t => types.add(t));
    });
    return Array.from(types).sort();
  });

  filteredSchemas = computed(() => {
    const schemas = this.data()?.schemas ?? [];
    const term = this.searchTerm().toLowerCase();
    const severity = this.severityFilter().toLowerCase();
    const type = this.typeFilter();
    const hasErrors = this.onlyWithErrors();

    return schemas.filter(s => {
      const matchTerm = !term || s.url.toLowerCase().includes(term);
      const matchSeverity = !severity || s.severity?.toLowerCase() === severity;
      const matchType = !type || s.schema_types_found?.includes(type);
      const matchErrors = !hasErrors || (s.error || (s.validation_errors && !s.validation_errors.is_valid));

      return matchTerm && matchSeverity && matchType && matchErrors;
    });
  });

  stats = computed(() => {
    const schemas = this.data()?.schemas ?? [];
    const total = schemas.length;
    const ok = schemas.filter(s => s.severity?.toLowerCase() === 'ok').length;
    const warnings = schemas.filter(s => s.severity?.toLowerCase() === 'warning').length;
    const critical = schemas.filter(s => s.severity?.toLowerCase() === 'critical').length;
    const withErrors = schemas.filter(s => s.error || (s.validation_errors && !s.validation_errors.is_valid)).length;
    return { total, ok, warnings, critical, withErrors };
  });

  hasActiveFilters = computed(() => {
    return this.searchTerm() !== ''
      || this.severityFilter() !== ''
      || this.typeFilter() !== ''
      || this.onlyWithErrors();
  });

  richResultsBatchCount = computed(() => this.selectedRichResultsUrls().size);
  richResultsBatchProgress = computed(() => {
    const selectedUrls = Array.from(this.selectedRichResultsUrls());
    if (!selectedUrls.length) return 0;

    const statusMap = this.richResultsStatusMap();
    const totalProgress = selectedUrls.reduce(
      (sum, url) => sum + (statusMap.get(url)?.progress_percentage ?? 0),
      0,
    );
    return Math.round(totalProgress / selectedUrls.length);
  });

  commentSummary = computed(() => {
    const schemas = this.data()?.schemas ?? [];
    const commentMap = this.commentsMap();
    let totalComments = 0;
    let pendingComments = 0;

    const items = schemas
      .map((schema) => {
        const comments = commentMap.get(schema.url) ?? [];
        if (!comments.length) return null;

        const pendingCount = comments.filter((comment) => comment.status === 'pending').length;
        totalComments += comments.length;
        pendingComments += pendingCount;

        return {
          url: schema.url,
          severity: schema.severity,
          totalCount: comments.length,
          pendingCount
        };
      })
      .filter((item): item is { url: string; severity: string | null; totalCount: number; pendingCount: number } => !!item)
      .sort((a, b) => {
        if (b.pendingCount !== a.pendingCount) return b.pendingCount - a.pendingCount;
        return b.totalCount - a.totalCount;
      });

    return {
      totalComments,
      pendingComments,
      items
    };
  });

  shareReportUrl = computed(() => {
    const validationId = this.validationId() ?? this.data()?.validation_id ?? '';
    if (!validationId) return '';

    const appUrl = environment.appUrl.replace(/\/+$/, '');
    return `${appUrl}/shared/audit/url-validations/${validationId}/info`;
  });

  toggleCard(index: number): void {
    const current = new Set(this.expandedCards());
    if (current.has(index)) {
      current.delete(index);
    } else {
      current.add(index);
      const schema = this.filteredSchemas()[index];
      if (schema?.url) {
        void this.ensureRichResultsLoaded(schema.url);
      }
    }
    this.expandedCards.set(current);
  }

  isCardExpanded(index: number): boolean {
    return this.expandedCards().has(index);
  }

  resetFilters(): void {
    this.searchTerm.set('');
    this.severityFilter.set('');
    this.typeFilter.set('');
    this.onlyWithErrors.set(false);
  }

  ngOnInit(): void {
    const layout = this._route.snapshot.data['layout'];
    if (layout === 'admin' || layout === 'shared') {
      this.layout.set(layout);
    }

    const id = this._route.snapshot.paramMap.get('id');
    if (id) {
      this.validationId.set(id);
      this.loadSchemas(id);
      this.loadPublicComments(id);
    }
    if (isPlatformBrowser(this._platformId)) {
      const saved = localStorage.getItem(LS_USERNAME_KEY);
      if (saved) this.commentUsername.set(saved);
      this.isLoggedIn.set(this._authRepository.isAuthenticated());
      this._taskNotificationService.prepareNotifications();
      this.startRichResultsPolling();
    }
  }

  ngOnDestroy(): void {
    if (this.richResultsPollTimer) {
      clearInterval(this.richResultsPollTimer);
      this.richResultsPollTimer = null;
    }
  }

  async loadSchemas(id: string) {
    try {
      this.isLoading.set(true);
      const response = await this._repository.getSchemasPublic(id);
      this.data.set(response);
      await this.loadRichResultsStatuses(response.schemas.map((schema) => schema.url));
    } catch (error) {
      console.error('Error loading schemas:', error);
      await this._sweetAlertUtil.error('general.messages.error', 'No se pudieron cargar los esquemas de la validación.');
    } finally {
      this.isLoading.set(false);
    }
  }

  async loadPublicComments(validationId: string) {
    try {
      const response = await this._repository.getPublicComments(validationId);
      const map = new Map<string, PublicCommentItemModel[]>();
      for (const comment of response.items) {
        const key = comment.schema_item_url;
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(comment);
      }
      this.commentsMap.set(map);
    } catch (error) {
      console.error('Error loading comments:', error);
    }
  }

  getCommentsForSchema(schemaItemId: string): PublicCommentItemModel[] {
    return this.commentsMap().get(schemaItemId) ?? [];
  }

  toggleCommentSection(schemaItemId: string): void {
    if (this.openCommentSection() === schemaItemId) {
      this.openCommentSection.set(null);
    } else {
      this.openCommentSection.set(schemaItemId);
    }
  }

  isCommentSectionOpen(schemaItemId: string): boolean {
    return this.openCommentSection() === schemaItemId;
  }

  getSchemaDomId(url: string): string {
    return `schema-card-${encodeURIComponent(url).replace(/%/g, '')}`;
  }

  scrollToSchema(url: string): void {
    if (!isPlatformBrowser(this._platformId)) return;

    const focusSchemaCard = () => {
      const index = this.filteredSchemas().findIndex((schema) => schema.url === url);
      if (index < 0) return false;

      if (!this.isCardExpanded(index)) {
        this.toggleCard(index);
      }
      this.openCommentSection.set(url);

      const element = document.getElementById(this.getSchemaDomId(url));
      if (!element) return false;

      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      element.classList.add('schema-card--highlight');
      setTimeout(() => {
        element.classList.remove('schema-card--highlight');
      }, 1800);
      return true;
    };

    if (focusSchemaCard()) return;

    if (this.hasActiveFilters()) {
      this.resetFilters();
      setTimeout(() => {
        focusSchemaCard();
      }, 80);
    }
  }

  async submitComment(schemaItemId: string): Promise<void> {
    const username = this.commentUsername().trim();
    const comment = this.commentText().trim();
    if (!username || !comment) {
      await this._sweetAlertUtil.error('', 'Por favor ingresa tu nombre de usuario y el comentario.');
      return;
    }
    if (isPlatformBrowser(this._platformId)) {
      localStorage.setItem(LS_USERNAME_KEY, username);
    }
    try {
      this.commentSubmitting.set(true);
      const newComment = await this._repository.createPublicComment(
        schemaItemId,
        this.validationId() ?? '',
        new CreatePublicCommentRequestModel(username, comment)
      );
      const map = new Map(this.commentsMap());
      if (!map.has(schemaItemId)) map.set(schemaItemId, []);
      map.get(schemaItemId)!.unshift(newComment as any);
      this.commentsMap.set(map);
      this.commentText.set('');
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        icon: 'success',
        title: 'Comentario enviado'
      });
    } catch (error) {
      console.error('Error submitting comment:', error);
      await this._sweetAlertUtil.error('', 'No se pudo enviar el comentario. Intenta nuevamente.');
    } finally {
      this.commentSubmitting.set(false);
    }
  }

  openAnswerModal(comment: PublicCommentItemModel): void {
    this.answerCommentTarget.set(comment);
    this.answerText.set(comment.answer ?? '');
    this.answerStatus.set('done');
    if (isPlatformBrowser(this._platformId)) {
      const modalEl = document.getElementById('answerCommentModal');
      if (modalEl) {
        const { Modal } = (window as any).bootstrap;
        Modal.getOrCreateInstance(modalEl).show();
      }
    }
  }

  async submitAnswer(): Promise<void> {
    const comment = this.answerCommentTarget();
    const answer = this.answerText().trim();
    if (!comment || !answer) {
      await this._sweetAlertUtil.error('', 'Por favor ingresa una respuesta.');
      return;
    }
    try {
      this.answerSubmitting.set(true);
      await this._repository.answerComment(
        comment.id,
        new AnswerCommentRequestModel(answer, this.answerStatus())
      );
      // Actualizar el mapa de comentarios localmente
      const map = new Map(this.commentsMap());
      for (const [key, comments] of map.entries()) {
        const idx = comments.findIndex(c => c.id === comment.id);
        if (idx >= 0) {
          comments[idx] = { ...comments[idx], answer, status: this.answerStatus(), answered_at: new Date().toISOString() };
          map.set(key, [...comments]);
          break;
        }
      }
      this.commentsMap.set(map);
      if (isPlatformBrowser(this._platformId)) {
        const modalEl = document.getElementById('answerCommentModal');
        if (modalEl) {
          const { Modal } = (window as any).bootstrap;
          Modal.getOrCreateInstance(modalEl).hide();
        }
      }
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        icon: 'success',
        title: 'Respuesta enviada'
      });
    } catch (error) {
      console.error('Error submitting answer:', error);
      await this._sweetAlertUtil.error('', 'No se pudo enviar la respuesta. Intenta nuevamente.');
    } finally {
      this.answerSubmitting.set(false);
    }
  }

  // Modal expand
  openModal(schema: AuditUrlValidationSchemaItemModel, tab: 'schema' | 'report'): void {
    this.modalSchema.set(schema);
    this.modalTab.set(tab);
    if (isPlatformBrowser(this._platformId)) {
      const modalEl = document.getElementById('expandModal');
      if (modalEl) {
        const { Modal } = (window as any).bootstrap;
        const modal = Modal.getOrCreateInstance(modalEl);
        modal.show();
      }
    }
  }

  setModalTab(tab: 'schema' | 'report'): void {
    this.modalTab.set(tab);
  }

  async copyToClipboard(text: any) {
    const json = typeof text === 'string' ? text : JSON.stringify(text, null, 2);
    try {
      await navigator.clipboard.writeText(json);
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        icon: 'success',
        title: 'Esquema copiado al portapapeles'
      });
    } catch (err) {
      console.error('Error al copiar:', err);
      this._sweetAlertUtil.error('Error', 'No se pudo copiar al portapapeles');
    }
  }

  async shareReport(): Promise<void> {
    const shareUrl = this.shareReportUrl();
    if (!shareUrl) {
      await this._sweetAlertUtil.error('', 'No se pudo generar la URL para compartir.');
      return;
    }

    try {
      await navigator.clipboard.writeText(shareUrl);
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        icon: 'success',
        title: 'URL compartible copiada al portapapeles'
      });
    } catch (error) {
      console.error('Error al copiar URL compartible:', error);
      await this._sweetAlertUtil.error('', 'No se pudo copiar la URL para compartir.');
    }
  }

  getSeverityClass(severity: string | null): string {
    if (!severity) return 'sv-secondary';
    const map: Record<string, string> = {
      critical: 'sv-danger',
      high: 'sv-warning',
      warning: 'sv-warning',
      medium: 'sv-info',
      low: 'sv-success',
      ok: 'sv-success'
    };
    return map[severity.toLowerCase()] ?? 'sv-secondary';
  }

  formatJson(json: any): string {
    return JSON.stringify(json, null, 2);
  }

  openValidator(url: string, tool: 'schema' | 'google') {
    let validatorUrl = '';
    if (tool === 'schema') {
      validatorUrl = `https://validator.schema.org/#url=${encodeURIComponent(url)}`;
    } else {
      validatorUrl = `https://search.google.com/test/rich-results?url=${encodeURIComponent(url)}`;
    }
    window.open(validatorUrl, '_blank');
  }

  openValidatorWithCode(code: any, tool: 'schema' | 'google') {
    const json = typeof code === 'string' ? code : JSON.stringify(code, null, 2);
    this.copyToClipboard(json);
    let validatorUrl = tool === 'schema' ? 'https://validator.schema.org/' : 'https://search.google.com/test/rich-results';
    this._sweetAlertUtil.fire({
      icon: 'info',
      title: 'Validador externo',
      text: 'Se ha copiado el código al portapapeles. Pégalo en el validador que se abrirá a continuación.'
    });
    setTimeout(() => {
      window.open(validatorUrl, '_blank');
    }, 2000);
  }

  formatDate(dateStr: string): string {
    try {
      return new Date(dateStr).toLocaleString('es-MX', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }

  isUrlSelectedForRichResultsBatch(url: string): boolean {
    return this.selectedRichResultsUrls().has(url);
  }

  toggleRichResultsBatchUrl(url: string): void {
    const next = new Set(this.selectedRichResultsUrls());
    if (next.has(url)) next.delete(url);
    else next.add(url);
    this.selectedRichResultsUrls.set(next);
  }

  addFilteredUrlsToRichResultsBatch(): void {
    const visibleUrls = this.filteredSchemas().map((schema) => schema.url);
    const next = new Set(this.selectedRichResultsUrls());
    for (const url of visibleUrls) next.add(url);
    this.selectedRichResultsUrls.set(next);
  }

  clearRichResultsBatch(): void {
    this.selectedRichResultsUrls.set(new Set());
  }

  getScreenshotPreviewUrl(assetUrl: string): string {
    if (!assetUrl) return '';
    if (/^https?:\/\//i.test(assetUrl)) return assetUrl;
    const normalizedPath = assetUrl.startsWith('/') ? assetUrl : `/${assetUrl}`;
    return `${this.richResultsApiBase}${normalizedPath}`;
  }

  getScreenshotApiBase(assetUrl: string): string {
    if (/^https?:\/\//i.test(assetUrl)) {
      try {
        return new URL(assetUrl).origin;
      } catch {
        return this.richResultsApiBase;
      }
    }
    return this.richResultsApiBase;
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

  getRichResultsState(url: string): string {
    return this.richResultsStatusMap().get(url)?.state ?? 'none';
  }

  getRichResultsStateLabel(url: string): string {
    const state = this.getRichResultsState(url);
    if (state === 'ok') return 'Validación OK';
    if (state === 'warning') return 'Validación warning';
    if (state === 'error') return 'Validación error';
    if (state === 'pending') return 'Validación pendiente';
    return 'Sin reporte de validación';
  }

  getRichResultsStateBadgeClass(url: string): string {
    const state = this.getRichResultsState(url);
    if (state === 'ok') return 'sv-success';
    if (state === 'warning') return 'sv-warning';
    if (state === 'error') return 'sv-danger';
    if (state === 'pending') return 'sv-info';
    return 'sv-secondary';
  }

  getRichResultsStateProgress(url: string): number {
    return Math.max(0, Math.min(100, this.richResultsStatusMap().get(url)?.progress_percentage ?? 0));
  }

  getFilteredRichResults(url: string): RichResultsReportListItemModel[] {
    const selectedFilter = this.richResultsHistoryFilter();
    const reports = this.getRichResults(url);

    if (selectedFilter === 'all') return reports;
    return reports.filter((report) => this.getRichResultsHistoryState(report) === selectedFilter);
  }

  getRichResultsHistoryState(report: RichResultsReportListItemModel): string {
    const status = (report.status || '').toLowerCase();
    const criticalCount = this.getRichResultsFindingCount(report.findings_summary, 'critical');
    const errorCount = this.getRichResultsFindingCount(report.findings_summary, 'error');
    const warningCount = this.getRichResultsFindingCount(report.findings_summary, 'warning');

    if (status === 'pending' || status === 'in_progress') return 'pending';
    if (status === 'failed' || report.error_message || criticalCount > 0 || errorCount > 0) return 'error';
    if (report.blocked_by_google || warningCount > 0) return 'warning';
    if (report.success) return 'ok';
    return 'warning';
  }

  getRichResultsHistoryStateLabel(report: RichResultsReportListItemModel): string {
    const state = this.getRichResultsHistoryState(report);
    if (state === 'ok') return 'OK';
    if (state === 'warning') return 'Warning';
    if (state === 'error') return 'Error';
    if (state === 'pending') return 'Pendiente';
    return 'Sin clasificar';
  }

  getRichResultsHistoryStateClass(report: RichResultsReportListItemModel): string {
    const state = this.getRichResultsHistoryState(report);
    if (state === 'ok') return 'sv-success';
    if (state === 'warning') return 'sv-warning';
    if (state === 'error') return 'sv-danger';
    if (state === 'pending') return 'sv-info';
    return 'sv-secondary';
  }

  getRichResultsReportProgress(report: RichResultsReportListItemModel): number {
    return Math.max(0, Math.min(100, report.progress_percentage ?? 0));
  }

  toggleAutoReload(): void {
    this.autoReload.update((value) => !value);
  }

  getRichResultsReportMessage(report: RichResultsReportListItemModel): string {
    return report.progress_message || report.message || report.error_message || 'Sin mensaje disponible.';
  }

  getRichResultsFindingCount(
    summary: RichResultsAnalysisSummaryModel | null | undefined,
    severity: string,
  ): number {
    return Math.max(0, summary?.by_severity?.[severity] ?? 0);
  }

  getRichResultsFindingBadgeClass(severity: string): string {
    if (severity === 'critical' || severity === 'error') return 'sv-danger';
    if (severity === 'warning') return 'sv-warning';
    if (severity === 'info') return 'sv-info';
    return 'sv-secondary';
  }

  getRichResultsFindingSeverityLabel(severity: string): string {
    if (severity === 'critical') return 'Críticos';
    if (severity === 'error') return 'Errores';
    if (severity === 'warning') return 'Warnings';
    if (severity === 'info') return 'Info';
    return severity || 'Hallazgos';
  }

  trackRichResultsFinding(finding: RichResultsAnalysisFindingModel, index: number): string {
    return `${finding.key}-${finding.selector}-${finding.message}-${finding.document_url || index}`;
  }

  getRichResultsValidatorSegments(
    detail: RichResultsReportDetailResponseModel,
  ): RichResultsValidatorDetailModel[] {
    return [detail.google_validation, detail.schema_org_validation].filter((segment) => segment.enabled);
  }

  trackRichResultsValidatorSegment(segment: RichResultsValidatorDetailModel, index: number): string {
    return `${segment.validator}-${index}`;
  }

  getRichResultsValidatorStateClass(segment: RichResultsValidatorDetailModel): string {
    if (segment.error_message || this.getRichResultsFindingCount(segment.findings_summary, 'error') > 0) return 'sv-danger';
    if (segment.blocked || this.getRichResultsFindingCount(segment.findings_summary, 'warning') > 0) return 'sv-warning';
    if (segment.success) return 'sv-success';
    return 'sv-secondary';
  }

  getRichResultsValidatorResultLabel(segment: RichResultsValidatorDetailModel): string {
    if (segment.validator === 'google') return 'Abrir resultado en Google';
    return 'Abrir resultado del validador';
  }

  hasRichResultsValidatorDetail(segment: RichResultsValidatorDetailModel): boolean {
    return !!(
      segment.message
      || segment.error_message
      || segment.findings_summary.total > 0
      || segment.screenshots.length > 0
      || segment.html_content
    );
  }

  groupFindingsByItem(
    findings: RichResultsAnalysisFindingModel[],
  ): { item_name: string | null; findings: RichResultsAnalysisFindingModel[] }[] {
    const map = new Map<string, RichResultsAnalysisFindingModel[]>();
    const NULL_KEY = '__no_item__';

    for (const f of findings) {
      const key = f.item_name ?? NULL_KEY;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(f);
    }

    const groups: { item_name: string | null; findings: RichResultsAnalysisFindingModel[] }[] = [];
    // ungrouped first
    if (map.has(NULL_KEY)) {
      groups.push({ item_name: null, findings: map.get(NULL_KEY)! });
      map.delete(NULL_KEY);
    }
    for (const [key, items] of map.entries()) {
      groups.push({ item_name: key, findings: items });
    }
    return groups;
  }

  private startRichResultsPolling(): void {
    if (this.richResultsPollTimer || !isPlatformBrowser(this._platformId)) return;
    this.richResultsPollTimer = setInterval(() => {
      if (!this.autoReload()) return;
      void this.pollPendingRichResults();
    }, 15000);
  }

  private async pollPendingRichResults(): Promise<void> {
    const urls = Array.from(this.richResultsMap().entries())
      .filter(([, items]) => items.some((item) => this.isRichResultsPending(item.status)))
      .map(([url]) => url);

    for (const url of urls) {
      await this.ensureRichResultsLoaded(url, true);
    }

    if (this.data()?.schemas?.length) {
      await this.loadRichResultsStatuses(this.data()!.schemas.map((schema) => schema.url));
    }
  }

  private updateUrlSet(
    signalRef: { (): Set<string>; set(value: Set<string>): void },
    url: string,
    add: boolean,
  ): void {
    const next = new Set(signalRef());
    if (add) next.add(url);
    else next.delete(url);
    signalRef.set(next);
  }

  async ensureRichResultsLoaded(url: string, force = false): Promise<void> {
    if (!url) return;
    if (!force && this.richResultsMap().has(url)) return;

    this.updateUrlSet(this.richResultsLoadingSet, url, true);
    try {
      const response = await this._richResultsRepository.getAll({
        url,
        distinct: false,
        page: 1,
        page_size: 20,
      });
      const next = new Map(this.richResultsMap());
      const items = response.items.filter((item) => item.url === url);
      next.set(url, items);
      this.richResultsMap.set(next);
      this.trackPendingRichResults(items);
      this.notifyCompletedRichResults(items);
      await this.loadRichResultsStatuses([url]);
    } catch (error) {
      console.error('Error loading rich results reports:', error);
    } finally {
      this.updateUrlSet(this.richResultsLoadingSet, url, false);
    }
  }

  getRichResults(url: string): RichResultsReportListItemModel[] {
    return this.richResultsMap().get(url) ?? [];
  }

  isRichResultsLoading(url: string): boolean {
    return this.richResultsLoadingSet().has(url);
  }

  isRichResultsCreating(url: string): boolean {
    return this.richResultsCreatingSet().has(url);
  }

  isRichResultsDeleting(url: string): boolean {
    return this.richResultsDeletingSet().has(url);
  }

  isRichResultsPending(status: string): boolean {
    return status === 'pending' || status === 'in_progress';
  }

  getRichResultsStatusClass(status: string): string {
    const normalized = (status || '').toLowerCase();
    if (normalized === 'completed') return 'sv-success';
    if (normalized === 'failed') return 'sv-danger';
    if (normalized === 'in_progress') return 'sv-info';
    return 'sv-warning';
  }

  isRichResultExpanded(reportId: string): boolean {
    return this.richResultsExpandedSet().has(reportId);
  }

  getRichResultDetail(reportId: string): RichResultsReportDetailResponseModel | null {
    return this.richResultsDetailMap().get(reportId) ?? null;
  }

  async toggleRichResultDetail(reportId: string, url: string): Promise<void> {
    const expanded = new Set(this.richResultsExpandedSet());
    if (expanded.has(reportId)) {
      expanded.delete(reportId);
      this.richResultsExpandedSet.set(expanded);
      return;
    }

    if (!this.richResultsDetailMap().has(reportId)) {
      try {
        const detail = await this._richResultsRepository.find(reportId, url);
        const details = new Map(this.richResultsDetailMap());
        details.set(reportId, detail);
        this.richResultsDetailMap.set(details);
      } catch (error) {
        console.error('Error loading rich results detail:', error);
        await this._sweetAlertUtil.error('', 'No se pudo cargar el detalle del reporte.');
        return;
      }
    }

    expanded.add(reportId);
    this.richResultsExpandedSet.set(expanded);
  }

  async createRichResultsReport(url: string): Promise<void> {
    if (!this.isLoggedIn() || !url) return;
    if (!this.richResultsSingleValidateGoogle() && !this.richResultsSingleValidateSchemaOrg()) {
      await this._sweetAlertUtil.error('', 'Activa Google, Schema.org o ambos para ejecutar el reporte.');
      return;
    }

    this.updateUrlSet(this.richResultsCreatingSet, url, true);
    try {
      const response = await this._richResultsRepository.create(
        new CreateRichResultsReportRequestModel(
          url,
          true,
          this.richResultsSingleAnalyzeWithAi(),
          this.richResultsSingleAutoExtractHtml(),
          this.richResultsSingleValidateGoogle(),
          this.richResultsSingleValidateSchemaOrg(),
        ),
      );
      this.trackRichResultsTask(response);
      await this.ensureRichResultsLoaded(url, true);
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 4000,
        timerProgressBar: true,
        icon: 'success',
        title: 'Reporte de validación iniciado en segundo plano'
      });
    } catch (error) {
      console.error('Error creating rich results report:', error);
      await this._sweetAlertUtil.error('', 'No se pudo iniciar el reporte de validación.');
    } finally {
      this.updateUrlSet(this.richResultsCreatingSet, url, false);
    }
  }

  async createRichResultsBatchReports(): Promise<void> {
    if (!this.isLoggedIn()) return;
    if (!this.richResultsBatchValidateGoogle() && !this.richResultsBatchValidateSchemaOrg()) {
      await this._sweetAlertUtil.error('', 'Activa Google, Schema.org o ambos para ejecutar el lote.');
      return;
    }

    const urls = Array.from(this.selectedRichResultsUrls());
    if (urls.length === 0) {
      await this._sweetAlertUtil.error('', 'Selecciona al menos una URL con los checkboxes para el lote.');
      return;
    }

    this.richResultsBatchSubmitting.set(true);
    try {
      const validationName = this.data()?.name_validation?.trim() || 'Validacion estructurada';
      const response = await this._structuredValidationRepository.create(
        new StructuredValidationCreateRequestModel(
          'url',
          `${validationName} · lote estructurado`,
          'Lote generado desde validaciones URL',
          null,
          null,
          urls.join('\n'),
          [],
          this.richResultsBatchAnalyzeWithAi(),
          this.richResultsBatchAutoExtractHtml(),
          this.richResultsBatchValidateGoogle(),
          this.richResultsBatchValidateSchemaOrg(),
        ),
      );
      this.clearRichResultsBatch();

      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 4500,
        timerProgressBar: true,
        icon: 'success',
        title: `Se creó un paquete con ${urls.length} URL(s)`,
      });
      await this._router.navigate(['/admin/audit/structured-validations', response.task_id, 'info']);
    } catch (error) {
      console.error('Error creating rich results batch:', error);
      await this._sweetAlertUtil.error('', 'No se pudo crear el paquete masivo de validación.');
    } finally {
      this.richResultsBatchSubmitting.set(false);
    }
  }

  async deleteRichResultsReport(reportId: string, url: string): Promise<void> {
    if (!this.isLoggedIn()) return;

    const confirmed = await this._sweetAlertUtil.fire({
      title: 'Eliminar reporte',
      text: 'Se eliminará este reporte de validación estructurada.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Eliminar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed.isConfirmed) return;

    this.updateUrlSet(this.richResultsDeletingSet, url, true);
    try {
      await this._richResultsRepository.delete(reportId, url);
      this.trackedRichResultsTasks.delete(reportId);
      const details = new Map(this.richResultsDetailMap());
      details.delete(reportId);
      this.richResultsDetailMap.set(details);
      const expanded = new Set(this.richResultsExpandedSet());
      expanded.delete(reportId);
      this.richResultsExpandedSet.set(expanded);
      await this.ensureRichResultsLoaded(url, true);
    } catch (error) {
      console.error('Error deleting rich results report:', error);
      await this._sweetAlertUtil.error('', 'No se pudo eliminar el reporte.');
    } finally {
      this.updateUrlSet(this.richResultsDeletingSet, url, false);
    }
  }

  async deleteRichResultsByUrl(url: string): Promise<void> {
    if (!this.isLoggedIn()) return;

    const confirmed = await this._sweetAlertUtil.fire({
      title: 'Eliminar reportes por URL',
      html: `Se eliminarán todos los reportes asociados a esta URL.<br><small class="text-muted">${url}</small>`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Eliminar todos',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed.isConfirmed) return;

    this.updateUrlSet(this.richResultsDeletingSet, url, true);
    try {
      await this._richResultsRepository.deleteByUrl(url);
      for (const [taskId, task] of this.trackedRichResultsTasks.entries()) {
        if (task.url === url) {
          this.trackedRichResultsTasks.delete(taskId);
        }
      }
      const next = new Map(this.richResultsMap());
      next.set(url, []);
      this.richResultsMap.set(next);
      const statusMap = new Map(this.richResultsStatusMap());
      statusMap.set(url, {
        url,
        state: 'none',
        report_id: null,
        report_status: null,
        progress_percentage: 0,
        progress_message: null,
        success: null,
        blocked_by_google: null,
        validate_google: true,
        validate_schema_org: true,
        has_error: false,
        findings_summary: {
          total: 0,
          by_severity: {},
          by_category: {},
        },
        google_validation: {
          validator: 'google',
          label: 'Google Rich Results',
          enabled: false,
          executed: false,
          success: null,
          method_used: null,
          result_url: null,
          message: null,
          error_message: null,
          blocked: false,
          screenshots: [],
          findings: [],
          findings_summary: { total: 0, by_severity: {}, by_category: {} },
          html_content: null,
          markdown_content: null,
        },
        schema_org_validation: {
          validator: 'schema_org',
          label: 'Schema.org Validator',
          enabled: false,
          executed: false,
          success: null,
          method_used: null,
          result_url: null,
          message: null,
          error_message: null,
          blocked: false,
          screenshots: [],
          findings: [],
          findings_summary: { total: 0, by_severity: {}, by_category: {} },
          html_content: null,
          markdown_content: null,
        },
        message: null,
        error_message: null,
        created_at: null,
      });
      this.richResultsStatusMap.set(statusMap);
    } catch (error) {
      console.error('Error deleting rich results reports by url:', error);
      await this._sweetAlertUtil.error('', 'No se pudieron eliminar los reportes.');
    } finally {
      this.updateUrlSet(this.richResultsDeletingSet, url, false);
    }
  }

  private async loadRichResultsStatuses(urls: string[]): Promise<void> {
    const normalizedUrls = Array.from(new Set(urls.filter(Boolean)));
    if (normalizedUrls.length === 0) return;

    try {
      const response = await this._richResultsRepository.getStatuses({
        urls: normalizedUrls,
      });
      const next = new Map(this.richResultsStatusMap());
      for (const item of response.items) {
        next.set(item.url, item);
      }
      this.richResultsStatusMap.set(next);
    } catch (error) {
      console.error('Error loading rich results status summaries:', error);
    }
  }

  private trackRichResultsTask(task: RichResultsReportTaskResponseModel): void {
    if (!task?.task_id || !task?.url) return;

    this.trackedRichResultsTasks.set(task.task_id, {
      url: task.url,
      status: (task.status || 'pending').toLowerCase(),
    });
  }

  private trackPendingRichResults(items: RichResultsReportListItemModel[]): void {
    for (const item of items) {
      const normalizedStatus = (item.status || '').toLowerCase();
      if (!this.isRichResultsPending(normalizedStatus)) continue;
      if (this.trackedRichResultsTasks.has(item.id)) continue;

      this.trackedRichResultsTasks.set(item.id, {
        url: item.url,
        status: normalizedStatus,
      });
    }
  }

  private notifyCompletedRichResults(items: RichResultsReportListItemModel[]): void {
    for (const item of items) {
      const tracked = this.trackedRichResultsTasks.get(item.id);
      if (!tracked) continue;

      const nextStatus = (item.status || '').toLowerCase();
      if (!this.isRichResultsTerminal(nextStatus)) {
        this.trackedRichResultsTasks.set(item.id, {
          url: item.url,
          status: nextStatus,
        });
        continue;
      }

      if (!this.isRichResultsTerminal(tracked.status)) {
        const isCompleted = nextStatus === 'completed';
        this._taskNotificationService.notifyTaskResult({
          title: isCompleted ? 'Reporte de validación listo' : 'Reporte de validación fallido',
          body: isCompleted
            ? `${item.url} ya terminó y está listo para revisarse.`
            : `${item.url} terminó con error.`,
          status: nextStatus,
          route: this.getCurrentRoute(),
          tag: `rich-results:${item.id}`,
        });
      }

      this.trackedRichResultsTasks.delete(item.id);
    }
  }

  private isRichResultsTerminal(status: string): boolean {
    return status === 'completed' || status === 'failed';
  }

  private getCurrentRoute(): string | undefined {
    if (!isPlatformBrowser(this._platformId)) {
      return undefined;
    }

    return `${window.location.pathname}${window.location.search}${window.location.hash}`;
  }

  private escapeHtml(value: string): string {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  async showValidationTaskMessage(): Promise<void> {
    const validationId = this.validationId();
    if (!validationId) return;

    try {
      const logs = await this._repository.getLogs(validationId);
      const fallback = this.data()?.progress_message || 'No hay mensajes registrados todavía.';
      const content = logs.items.length
        ? logs.items
            .map(
              (log) =>
                `[${this.formatDate(log.created_at)}] ${String(log.level || 'info').toUpperCase()}${log.progress_percentage != null ? ` (${log.progress_percentage}%)` : ''}\n${log.message}`
            )
            .join('\n\n')
        : fallback;

      await this._sweetAlertUtil.fire({
        title: 'Mensaje de tarea',
        html: `<div style="text-align:left; max-height:60vh; overflow:auto;"><pre style="white-space:pre-wrap; margin:0;">${this.escapeHtml(content)}</pre></div>`,
        width: 800,
        confirmButtonText: 'Cerrar',
      });
    } catch (error) {
      console.error('Error loading validation task logs:', error);
      await this._sweetAlertUtil.error('', 'No se pudieron cargar los mensajes de la validación.');
    }
  }

  async showRichResultsTaskMessage(report: RichResultsReportListItemModel): Promise<void> {
    try {
      const logs = await this._richResultsRepository.getLogs(report.id, report.url);
      const fallback = this.getRichResultsReportMessage(report);
      const content = logs.items.length
        ? logs.items
            .map(
              (log) =>
                `[${this.formatDate(log.created_at)}] ${String(log.level || 'info').toUpperCase()}${log.progress_percentage != null ? ` (${log.progress_percentage}%)` : ''}\n${log.message}`
            )
            .join('\n\n')
        : fallback;

      await this._sweetAlertUtil.fire({
        title: 'Mensaje de tarea',
        html: `<div style="text-align:left; max-height:60vh; overflow:auto;"><pre style="white-space:pre-wrap; margin:0;">${this.escapeHtml(content)}</pre></div>`,
        width: 800,
        confirmButtonText: 'Cerrar',
      });
    } catch (error) {
      console.error('Error loading rich results logs:', error);
      await this._sweetAlertUtil.error('', 'No se pudieron cargar los mensajes del reporte.');
    }
  }

  async rerunAll(): Promise<void> {
    const id = this.validationId();
    if (!id) return;
    const confirmed = await this._sweetAlertUtil.fire({
      title: 'Re-ejecutar validación completa',
      text: '¿Estás seguro de que deseas re-analizar todas las URLs? Esto puede tardar varios minutos.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, re-ejecutar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed.isConfirmed) return;
    try {
      this.rerunLoading.set(true);
      await this._repository.rerunValidation(id);
      this._taskNotificationService.registerPendingTask('url-validation', id);
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 5000,
        timerProgressBar: true,
        icon: 'success',
        title: 'Validación re-iniciada en segundo plano'
      });
    } catch (error: any) {
      const status = error?.response?.status;
      if (status === 409) {
        await this._sweetAlertUtil.error('', 'Ya hay una validación en progreso. Espera a que termine.');
      } else {
        await this._sweetAlertUtil.error('', 'No se pudo re-ejecutar la validación. Intenta nuevamente.');
      }
    } finally {
      this.rerunLoading.set(false);
    }
  }

  async rerunUrl(url: string): Promise<void> {
    const id = this.validationId();
    if (!id || !url) return;
    const confirmed = await this._sweetAlertUtil.fire({
      title: 'Re-analizar URL',
      html: `¿Re-analizar esta URL?<br><small class="text-muted">${url}</small>`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Sí, re-analizar',
      cancelButtonText: 'Cancelar',
    });
    if (!confirmed.isConfirmed) return;
    try {
      this.rerunUrlTarget.set(url);
      await this._repository.rerunValidationUrl(id, url);
      this._taskNotificationService.registerPendingTask('url-validation', id);
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 5000,
        timerProgressBar: true,
        icon: 'success',
        title: 'URL re-analizada en segundo plano'
      });
    } catch (error: any) {
      const status = error?.response?.status;
      if (status === 409) {
        await this._sweetAlertUtil.error('', 'Ya hay una validación en progreso. Espera a que termine.');
      } else {
        await this._sweetAlertUtil.error('', 'No se pudo re-analizar la URL. Intenta nuevamente.');
      }
    } finally {
      this.rerunUrlTarget.set(null);
    }
  }

  // ===== TARGET HTML METHODS =====

  private getTargetIdFromRoute(): string | null {
    return this.validationId();
  }

  /** Abre en nueva pestaña la página de actualización del target (solo si está logueado) */
  openUpdateTargetPage(): void {
    const targetId = this.getTargetIdFromRoute();
    if (!targetId) return;
    window.open(`/admin/target/update/${targetId}`, '_blank');
  }

  /** Llama al endpoint público GET /targets/html/{url} y copia el HTML al portapapeles */
  async copyTargetHtml(pageUrl: string): Promise<void> {
    if (!pageUrl) return;
    try {
      this.htmlLoading.set(true);
      const response = await this._targetRepository.getHtml(pageUrl);
      await navigator.clipboard.writeText(response.html);
      this._sweetAlertUtil.fire({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 4000,
        timerProgressBar: true,
        icon: 'success',
        title: `HTML copiado (${response.source === 'live' ? 'en vivo' : 'almacenado'} · ${response.html_length.toLocaleString()} chars)`
      });
    } catch (error: any) {
      const status = error?.response?.status;
      if (status === 503) {
        await this._sweetAlertUtil.error('Sin HTML disponible', 'No se pudo obtener el HTML en tiempo real y no hay HTML guardado para esta página.');
      } else {
        await this._sweetAlertUtil.error('Error', 'No se pudo obtener el HTML de la página.');
      }
    } finally {
      this.htmlLoading.set(false);
    }
  }

  /** Valida por URL obteniendo antes el HTML de esa página vía /targets/html/{url} */
  async openValidatorWithHtml(pageUrl: string, tool: 'schema' | 'google'): Promise<void> {
    const validatorUrl = tool === 'schema' ? 'https://validator.schema.org/' : 'https://search.google.com/test/rich-results';
    if (!pageUrl) {
      window.open(validatorUrl, '_blank');
      return;
    }
    try {
      this.htmlLoading.set(true);
      const response = await this._targetRepository.getHtml(pageUrl);
      await navigator.clipboard.writeText(response.html);
      this._sweetAlertUtil.fire({
        icon: 'info',
        title: 'HTML copiado al portapapeles',
        text: 'Pégalo en el validador que se abrirá a continuación (pestaña "Code Snippet").'
      });
      setTimeout(() => {
        window.open(validatorUrl, '_blank');
      }, 2000);
    } catch {
      window.open(validatorUrl, '_blank');
    } finally {
      this.htmlLoading.set(false);
    }
  }
}
