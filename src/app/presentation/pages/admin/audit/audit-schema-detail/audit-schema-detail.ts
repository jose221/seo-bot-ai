import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgClass, DatePipe } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { MarkdownModule } from 'ngx-markdown';
import { AuditSchemaRepository } from '@/app/domain/repositories/audit-schema/audit-schema.repository';
import { FindAuditSchemaResponseModel } from '@/app/domain/models/audit-schema/response/audit-schema-response.model';
import { StatusAuditUtil } from '@/app/presentation/utils/status-audit.util';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { ReportDownloadService } from '@/app/infrastructure/services/general/report-download.service';

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
  private readonly _reportDownloadService = inject(ReportDownloadService);
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

  canDownloadReports(): boolean {
    return this.item()?.status === 'completed';
  }

  async downloadReport(type: 'pdf' | 'word') {
    const id = this.item()?.id;
    if (!id || !this.canDownloadReports()) {
      await this._sweetAlertUtil.error('general.messages.error', 'El reporte no está disponible');
      return;
    }

    try {
      await this._reportDownloadService.downloadSchemaReport(id, type);
    } catch (error) {
      console.error(error);
      await this._sweetAlertUtil.error('general.messages.error', 'No se pudo descargar el reporte');
    }
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
