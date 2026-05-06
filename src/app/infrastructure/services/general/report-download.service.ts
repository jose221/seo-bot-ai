import { Inject, Injectable } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { BaseService } from '@/app/infrastructure/services/base/base.service';
import { HttpService } from '@/app/infrastructure/services/general/http.service';
import { environment } from '@/environments/environment';

type ReportFormat = 'pdf' | 'word';

@Injectable({
  providedIn: 'root',
})
export class ReportDownloadService extends BaseService {
  constructor(
    private readonly httpService: HttpService,
    @Inject(DOCUMENT) private readonly document: Document,
  ) {
    super();
  }

  async downloadAuditReport(id: string, format: ReportFormat): Promise<void> {
    await this.handleEndpoint(
      `${environment.endpoints.audit.path}/${id}/download/${format}`,
      `audit-${id}.${this.getExtension(format)}`,
      format,
    );
  }

  async downloadComparisonReport(id: string, format: ReportFormat): Promise<void> {
    await this.handleEndpoint(
      `${environment.endpoints.audit.comparisons}/${id}/download/${format}`,
      `comparison-${id}.${this.getExtension(format)}`,
      format,
    );
  }

  async downloadSchemaReport(id: string, format: ReportFormat): Promise<void> {
    await this.handleEndpoint(
      `${environment.endpoints.auditSchema.path}/${id}/download/${format}`,
      `schema-audit-${id}.${this.getExtension(format)}`,
      format,
    );
  }

  async downloadUrlValidationReport(id: string, format: ReportFormat): Promise<void> {
    await this.handleEndpoint(
      `${environment.endpoints.auditUrlValidation.path}/${id}/download/${format}`,
      `url-validation-${id}.${this.getExtension(format)}`,
      format,
    );
  }

  async downloadUrlValidationGlobalReport(id: string, format: ReportFormat): Promise<void> {
    await this.handleEndpoint(
      `${environment.endpoints.auditUrlValidation.path}/${id}/global/download/${format}`,
      `url-validation-global-${id}.${this.getExtension(format)}`,
      format,
    );
  }

  private async handleEndpoint(endpoint: string, filename: string, format: ReportFormat): Promise<void> {
    if (format === 'pdf') {
      await this.openPdfInNewTab(endpoint);
      return;
    }

    await this.downloadFile(endpoint, filename);
  }

  private async openPdfInNewTab(endpoint: string): Promise<void> {
    const previewWindow = this.document.defaultView?.open('', '_blank');
    if (previewWindow?.document) {
      previewWindow.document.title = 'Cargando PDF...';
      previewWindow.document.body.innerHTML = '<p style="font-family: sans-serif; padding: 16px;">Cargando PDF...</p>';
    }

    try {
      const blob = await this.fetchBlob(endpoint);
      const objectUrl = URL.createObjectURL(blob);
      if (previewWindow) {
        previewWindow.location.href = objectUrl;
      } else {
        this.document.defaultView?.open(objectUrl, '_blank');
      }
    } catch (error) {
      previewWindow?.close();
      throw error;
    }
  }

  private async downloadFile(endpoint: string, filename: string): Promise<void> {
    const blob = await this.fetchBlob(endpoint);
    const objectUrl = URL.createObjectURL(blob);
    const link = this.document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    this.document.body.appendChild(link);
    link.click();
    this.document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
  }

  private async fetchBlob(endpoint: string): Promise<Blob> {
    return this.httpService.get<Blob>(
      endpoint,
      {},
      { responseType: 'blob' },
      this.getToken,
    );
  }

  private getExtension(format: ReportFormat): string {
    return format === 'pdf' ? 'pdf' : 'docx';
  }
}
