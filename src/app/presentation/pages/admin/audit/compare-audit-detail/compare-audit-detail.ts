import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgClass, DatePipe, DecimalPipe } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { MarkdownModule } from 'ngx-markdown';
import { AuditRepository } from '@/app/domain/repositories/audit/audit.repository';
import { FindCompareAuditResponseModel } from '@/app/domain/models/audit/response/audit-response.model';
import { SweetAlertUtil } from '@/app/presentation/utils/sweetAlert.util';
import { ReportDownloadService } from '@/app/infrastructure/services/general/report-download.service';

@Component({
  selector: 'app-compare-audit-detail',
  standalone: true,
  imports: [RouterLink, NgClass, TranslatePipe, MarkdownModule, DatePipe, DecimalPipe],
  templateUrl: './compare-audit-detail.html',
  styleUrl: './compare-audit-detail.scss',
})
export class CompareAuditDetail implements OnInit {
  private readonly _route = inject(ActivatedRoute);
  private readonly _auditRepository = inject(AuditRepository);
  private readonly _sweetAlertUtil = inject(SweetAlertUtil);
  private readonly _reportDownloadService = inject(ReportDownloadService);

  isLoading = signal<boolean>(true);
  item = signal<FindCompareAuditResponseModel | null>(null);

  async ngOnInit() {
    const id = this._route.snapshot.paramMap.get('id');
    if (!id) return;
    await this.load(id);
  }

  async load(id: string) {
    try {
      this.isLoading.set(true);
      const data = await this._auditRepository.findComparisons(id);
      this.item.set(data);
    } catch (e) {
      console.error(e);
      await this._sweetAlertUtil.error('general.messages.error', 'No se pudo cargar la comparación.');
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
      await this._sweetAlertUtil.error('general.messages.error', `El reporte ${type.toUpperCase()} no está disponible`);
      return;
    }

    try {
      await this._reportDownloadService.downloadComparisonReport(id, type);
    } catch (error) {
      console.error(error);
      await this._sweetAlertUtil.error('general.messages.error', `No se pudo descargar el reporte ${type.toUpperCase()}`);
    }
  }
}
