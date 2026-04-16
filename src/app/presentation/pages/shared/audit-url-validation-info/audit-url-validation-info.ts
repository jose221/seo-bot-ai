import { Component, inject, signal, OnInit, computed, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { AuthRepository } from '@/app/domain/repositories/auth/auth.repository';
import {
  AuditUrlValidationSchemasResponseModel,
  AuditUrlValidationSchemaItemModel,
  PublicCommentItemModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  CreatePublicCommentRequestModel,
  AnswerCommentRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import { TranslateModule } from '@ngx-translate/core';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { MarkdownModule } from 'ngx-markdown';
import { FormsModule } from '@angular/forms';

const LS_USERNAME_KEY = 'public_validator_username';

@Component({
  selector: 'app-public-audit-url-validation-info',
  standalone: true,
  imports: [
    CommonModule,
    TranslateModule,
    MarkdownModule,
    FormsModule
  ],
  templateUrl: './audit-url-validation-info.html',
  styleUrl: './audit-url-validation-info.scss'
})
export default class PublicAuditUrlValidationInfoComponent implements OnInit {
  private readonly _route = inject(ActivatedRoute);
  private readonly _repository = inject(AuditUrlValidationRepository);
  private readonly _authRepository = inject(AuthRepository);
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);
  private readonly _platformId = inject(PLATFORM_ID);

  isLoading = signal<boolean>(true);
  data = signal<AuditUrlValidationSchemasResponseModel | null>(null);
  validationId = signal<string | null>(null);
  showFilters = signal<boolean>(false);

  // Filters
  searchTerm = signal<string>('');
  severityFilter = signal<string>('');
  typeFilter = signal<string>('');
  onlyWithErrors = signal<boolean>(false);

  // Accordion
  expandedCards = signal<Set<number>>(new Set([0]));

  // Modal expand
  modalSchema = signal<AuditUrlValidationSchemaItemModel | null>(null);
  modalTab = signal<'schema' | 'report'>('schema');

  // Auth
  isLoggedIn = signal<boolean>(false);

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
    return this.searchTerm() !== '' || this.severityFilter() !== '' || this.typeFilter() !== '' || this.onlyWithErrors();
  });

  toggleCard(index: number): void {
    const current = new Set(this.expandedCards());
    if (current.has(index)) {
      current.delete(index);
    } else {
      current.add(index);
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
    }
  }

  async loadSchemas(id: string) {
    try {
      this.isLoading.set(true);
      const response = await this._repository.getSchemasPublic(id);
      this.data.set(response);
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
}
