import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { AuditUrlValidationSchemasResponseModel, AuditUrlValidationSchemaItemModel } from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import { TranslateModule } from '@ngx-translate/core';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { MarkdownModule } from 'ngx-markdown';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-audit-url-validation-info',
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
export default class AuditUrlValidationInfoComponent implements OnInit {
  private readonly _route = inject(ActivatedRoute);
  private readonly _repository = inject(AuditUrlValidationRepository);
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);

  isLoading = signal<boolean>(true);
  data = signal<AuditUrlValidationSchemasResponseModel | null>(null);
  validationId = signal<string | null>(null);

  // Filters
  searchTerm = signal<string>('');
  severityFilter = signal<string>('');
  typeFilter = signal<string>('');
  onlyWithErrors = signal<boolean>(false);

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
      const response = await this._repository.getSchemas(id);
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
    if (!severity) return 'bg-secondary';
    const map: Record<string, string> = {
      critical: 'bg-danger',
      high: 'bg-warning text-dark',
      warning: 'bg-warning text-dark',
      medium: 'bg-info text-dark',
      low: 'bg-success',
      ok: 'bg-success'
    };
    return map[severity.toLowerCase()] ?? 'bg-secondary';
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
    // Para schema.org no hay una forma fácil de pasar código por URL directamente que funcione siempre bien
    // Pero podemos redirigirlos a la página para que lo peguen.
    // Google Rich Results Test tampoco permite pasar código por URL de forma pública fácilmente.
    // Así que lo mejor es copiar al portapapeles y abrir el validador.
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
