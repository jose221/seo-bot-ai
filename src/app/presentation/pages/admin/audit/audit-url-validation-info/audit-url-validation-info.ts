import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { AuditUrlValidationSchemasResponseModel, AuditUrlValidationSchemaItemModel } from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import { TranslateModule } from '@ngx-translate/core';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { MarkdownModule } from 'ngx-markdown';

@Component({
  selector: 'app-audit-url-validation-info',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TranslateModule,
    MarkdownModule
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
