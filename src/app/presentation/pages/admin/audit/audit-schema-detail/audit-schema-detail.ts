import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgClass, DatePipe } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { MarkdownModule } from 'ngx-markdown';
import { AuditSchemaRepository } from '@/app/domain/repositories/audit-schema/audit-schema.repository';
import { FindAuditSchemaResponseModel } from '@/app/domain/models/audit-schema/response/audit-schema-response.model';
import { StatusAuditUtil } from '@/app/presentation/utils/status-audit.util';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { environment } from '@/environments/environment';

@Component({
  selector: 'app-audit-schema-detail',
  standalone: true,
  imports: [RouterLink, NgClass, TranslatePipe, MarkdownModule, DatePipe],
  templateUrl: './audit-schema-detail.html',
  styleUrl: './audit-schema-detail.scss',
})
export class AuditSchemaDetail implements OnInit {
  private readonly _route = inject(ActivatedRoute);
  private readonly _auditSchemaRepository = inject(AuditSchemaRepository);
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);
  public readonly statusUtil = inject(StatusAuditUtil);

  isLoading = signal<boolean>(true);
  item = signal<FindAuditSchemaResponseModel | null>(null);

  async ngOnInit() {
    const id = this._route.snapshot.paramMap.get('id');
    if (!id) return;
    await this.load(id);
  }

  async load(id: string) {
    try {
      this.isLoading.set(true);
      const data = await this._auditSchemaRepository.find(id);
      this.item.set(data);
    } catch (e) {
      console.error(e);
      await this._sweetAlertUtil.error('general.messages.error', 'No se pudo cargar el schema.');
    } finally {
      this.isLoading.set(false);
    }
  }

  downloadReport(type: 'pdf' | 'word') {
    const baseUrl = (environment.apiUrl as string).replace('/api/v1', '');
    const path = type === 'pdf' ? this.item()?.report_pdf_path : this.item()?.report_word_path;

    if (!path) {
      this._sweetAlertUtil.error('general.messages.error', `El reporte no está disponible`);
      return;
    }
    window.open(`${baseUrl}/${path}`, '_blank');
  }

  getStatusClass(status: string): string {
    return this.statusUtil.getStatusClass(status as any);
  }

  getStatusIcon(status: string): string {
    const icons: Record<string, string> = {
      completed: 'bi-check-circle',
      pending: 'bi-clock',
      failed: 'bi-x-circle',
      processing: 'bi-arrow-repeat',
    };
    return icons[status] ?? 'bi-circle';
  }

  getValidationStatusClass(isValid: boolean): string {
    return isValid ? 'text-success' : 'text-danger';
  }

  getValidationIcon(isValid: boolean): string {
    return isValid ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
  }
}
