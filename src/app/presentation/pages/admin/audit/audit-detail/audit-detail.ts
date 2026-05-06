import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgClass } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { MarkdownComponent } from 'ngx-markdown';
import { AuditRepository } from '@/app/domain/repositories/audit/audit.repository';
import { AuditResponseModel } from '@/app/domain/models/audit/response/audit-response.model';
import { StatusAuditUtil } from '@/app/presentation/utils/status-audit.util';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { DateFormatPipe } from '@/app/pipes/date-format-pipe';
import { ReportDownloadService } from '@/app/infrastructure/services/general/report-download.service';

@Component({
  selector: 'app-audit-detail',
  standalone: true,
  imports: [RouterLink, NgClass, TranslatePipe, MarkdownComponent, DateFormatPipe],
  templateUrl: './audit-detail.html',
  styleUrl: './audit-detail.scss',
})
export class AuditDetail implements OnInit {
  private readonly _route = inject(ActivatedRoute);
  private readonly _auditRepository = inject(AuditRepository);
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);
  private readonly _reportDownloadService = inject(ReportDownloadService);
  public readonly statusAuditUtil = inject(StatusAuditUtil);

  isLoading = signal<boolean>(true);
  item = signal<AuditResponseModel | null>(null);

  async ngOnInit() {
    const id = this._route.snapshot.paramMap.get('id');
    if (!id) return;
    await this.load(id);
  }

  async load(id: string) {
    try {
      this.isLoading.set(true);
      const data = await this._auditRepository.find(id);
      this.item.set(data);
    } catch (e) {
      console.error(e);
      await this._sweetAlertUtil.error('general.messages.error', 'No se pudo cargar la auditoría.');
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
      await this._reportDownloadService.downloadAuditReport(id, type);
    } catch (error) {
      console.error(error);
      await this._sweetAlertUtil.error('general.messages.error', 'No se pudo descargar el reporte');
    }
  }
}
