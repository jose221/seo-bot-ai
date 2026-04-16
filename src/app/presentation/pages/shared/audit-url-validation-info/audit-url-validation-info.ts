import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { AuditUrlValidationSchemasResponseModel, AuditUrlValidationSchemaItemModel } from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import { TranslateModule } from '@ngx-translate/core';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { MarkdownModule } from 'ngx-markdown';
import { FormsModule } from '@angular/forms';

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
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);

  isLoading = signal<boolean>(true);
  data = signal<AuditUrlValidationSchemasResponseModel | null>(null);
  validationId = signal<string | null>(null);
  showFilters = signal<boolean>(false);

  // Filters
  searchTerm = signal<string>('');
  severityFilter = signal<string>('');
  typeFilter = signal<string>('');
  onlyWithErrors = signal<boolean>(false);

  // Collapsed state per schema card
  expandedCards = signal<Set<number>>(new Set([0]));

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
}
