import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgClass, DatePipe } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { MarkdownModule } from 'ngx-markdown';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { FindAuditUrlValidationResponseModel } from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import { StatusAuditUtil } from '@/app/presentation/utils/status-audit.util';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { environment } from '@/environments/environment';

@Component({
  selector: 'app-audit-url-validation-detail',
  standalone: true,
  imports: [RouterLink, NgClass, TranslatePipe, MarkdownModule, DatePipe],
  templateUrl: './audit-url-validation-detail.html',
  styleUrl: './audit-url-validation-detail.scss',
})
export class AuditUrlValidationDetail implements OnInit {
  private readonly _route = inject(ActivatedRoute);
  private readonly _repository = inject(AuditUrlValidationRepository);
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);
  public readonly statusUtil = inject(StatusAuditUtil);

  isLoading = signal<boolean>(true);
  item = signal<FindAuditUrlValidationResponseModel | null>(null);

  async ngOnInit() {
    const id = this._route.snapshot.paramMap.get('id');
    if (!id) return;
    await this.load(id);
  }

  async load(id: string) {
    try {
      this.isLoading.set(true);
      const data = await this._repository.find(id);
      this.item.set(data);
    } catch (e) {
      console.error(e);
      await this._sweetAlertUtil.error('general.messages.error', 'No se pudo cargar la validación.');
    } finally {
      this.isLoading.set(false);
    }
  }

  downloadReport(type: 'pdf' | 'word' | 'global_pdf' | 'global_word') {
    const baseUrl = (environment.apiUrl as string).replace('/api/v1', '');
    let path: string | null = null;

    switch (type) {
      case 'pdf':
        path = this.item()?.report_pdf_path ?? null;
        break;
      case 'word':
        path = this.item()?.report_word_path ?? null;
        break;
      case 'global_pdf':
        path = this.item()?.global_report_pdf_path ?? null;
        break;
      case 'global_word':
        path = this.item()?.global_report_word_path ?? null;
        break;
    }

    if (!path) {
      this._sweetAlertUtil.error('general.messages.error', 'El reporte no está disponible');
      return;
    }
    window.open(`${baseUrl}/${path}`, '_blank');
  }

  getSeverityClass(severity: string | null): string {
    if (!severity) return 'bg-secondary';
    const map: Record<string, string> = {
      critical: 'bg-danger',
      high: 'bg-warning text-dark',
      medium: 'bg-info text-dark',
      low: 'bg-success',
    };
    return map[severity.toLowerCase()] ?? 'bg-secondary';
  }

  getStatusClass(status: string): string {
    return this.statusUtil.getStatusClass(status as any);
  }

  getResultsWithErrors(results: any[]): number {
    return results.filter(r => r.validation_errors && !r.validation_errors.is_valid).length;
  }

  parseResultsJson(raw: any): any[] {
    if (!raw) return [];
    if (Array.isArray(raw)) return raw;
    try {
      const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch {
      return [];
    }
  }

  formatJson(raw: any): string {
    if (!raw) return '';
    try {
      const obj = typeof raw === 'string' ? JSON.parse(raw) : raw;
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(raw);
    }
  }
}
