import {isPlatformBrowser} from '@angular/common';
import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { ListDefaultBase } from '@/app/presentation/shared/list-default.base';
import { StatusAuditUtil } from '@/app/presentation/utils/status-audit.util';
import { FilterListConfig } from '@/app/domain/models/general/filter-list.model';
import { TableColumn } from '@/app/domain/models/general/table-column.model';
import { PaginatorHelper } from '@/app/helper/paginator.helper';
import { RouterLink, Router } from '@angular/router';
import { DatePipe, NgClass } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { MarkdownModule } from 'ngx-markdown';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import {
  AuditUrlValidationItemResponseModel,
  FindAuditUrlValidationResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import { environment } from '@/environments/environment';
import {
  BodyModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/body-modal/body-modal.component';
import { DefaultModal } from '@/app/presentation/components/general/bootstrap/general-modals/default-modal/default-modal';
import {
  FooterModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/footer-modal/footer-modal.component';
import {
  HeaderModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/header-modal/header-modal.component';
import { FilterList } from '@/app/presentation/components/general/filter-list/filter-list';
import { PaginatorList } from '@/app/presentation/components/general/paginator-list/paginator-list';
import { TableComponent } from '@/app/presentation/components/general/table/table.component';

@Component({
  selector: 'app-audit-url-validation-list',
  imports: [
    BodyModalComponent,
    DefaultModal,
    FilterList,
    FooterModalComponent,
    HeaderModalComponent,
    PaginatorList,
    RouterLink,
    TableComponent,
    TranslatePipe,
    NgClass,
    DatePipe,
    MarkdownModule,
  ],
  templateUrl: './audit-url-validation-list.html',
  styleUrl: './audit-url-validation-list.scss',
})
export class AuditUrlValidationList
  extends ListDefaultBase<AuditUrlValidationItemResponseModel>
  implements OnInit, OnDestroy
{
  public statusUtil = inject(StatusAuditUtil);
  private readonly _repository = inject(AuditUrlValidationRepository);
  private intervalId: any;
  autoReload = signal<boolean>(true);
  readonly RELOAD_INTERVAL = 12000;

  public showDetail = signal<boolean>(false);
  public selectedItem = signal<FindAuditUrlValidationResponseModel>(
    {} as FindAuditUrlValidationResponseModel
  );
  public loadingDetail = signal<boolean>(false);

  configFilter = signal<FilterListConfig>({
    limit: 8,
    search: {
      label: 'Buscar',
      value: '',
      placeholder: 'Buscar por nombre o ID...',
      attributes: ['id', 'name_validation', 'source_type', 'source_id'],
      key: 'id',
      defaultValue: '',
      type: 'text',
    },
  });

  tableColumn = signal<TableColumn[]>([
    {
      key: 'name_validation',
      name: 'Nombre',
      type: 'text',
    },
    {
      key: 'source_type',
      name: 'Tipo de Fuente',
      type: 'text',
    },
    {
      key: 'status',
      name: 'Estado',
      type: 'text',
      innerHtml: (element: AuditUrlValidationItemResponseModel) => {
        const cls = this.statusUtil.getStatusClass(element.status as any);
        const txt = this.statusUtil.getStatusText(element.status as any);
        return `<span class="badge ${cls}"><span class="status-text">${txt}</span></span>`;
      },
    },
    {
      key: 'global_severity',
      name: 'Severidad',
      type: 'text',
      innerHtml: (element: AuditUrlValidationItemResponseModel) => {
        if (!element.global_severity) return '<span class="text-muted">—</span>';
        const map: Record<string, string> = {
          critical: 'bg-danger',
          high: 'bg-warning text-dark',
          medium: 'bg-info text-dark',
          low: 'bg-success',
        };
        const cls = map[element.global_severity.toLowerCase()] ?? 'bg-secondary';
        return `<span class="badge ${cls}">${element.global_severity}</span>`;
      },
    },
    {
      key: 'created_at',
      name: 'Creado el',
      type: 'datetime',
    },
    {
      key: 'completed_at',
      name: 'Completado el',
      type: 'datetime',
    },
    {
      key: 'id',
      name: 'Schemas',
      type: 'link',
      innerHtml: () => 'Info Schemas',
      action: (item: AuditUrlValidationItemResponseModel) => this._router.navigate(['/admin/audit/url-validations', item.id, 'info']),
    },
    {
      key: 'id',
      name: 'Ver',
      type: 'link',
      innerHtml: () => 'Ver',
      action: (item: AuditUrlValidationItemResponseModel) => this.toShow(item),
    },
    {
      key: 'id',
      name: 'Volver a ejecutar',
      type: 'link',
      innerHtml: () => '<i class="bi bi-arrow-repeat me-1"></i>Volver a ejecutar',
      action: (item: AuditUrlValidationItemResponseModel) => this.toRerun(item),
    },
    {
      key: 'id',
      name: 'Eliminar',
      type: 'link',
      innerHtml: () => 'Eliminar',
      action: (item: AuditUrlValidationItemResponseModel) => this.toDelete(item),
    },
  ]);

  constructor() {
    super();
  }

  override async ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) return;
    await super.ngOnInit();
    this.startAutoReload();
  }

  override ngOnDestroy() {
    this.stopAutoReload();
    super.ngOnDestroy();
  }

  startAutoReload() {
    this.stopAutoReload();
    this.intervalId = setInterval(() => {
      if (this.autoReload()) this.init(true);
    }, this.RELOAD_INTERVAL);
  }

  stopAutoReload() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  toggleAutoReload() {
    this.autoReload.update((v) => !v);
  }

  async init(silent = false) {
    try {
      if (!silent) this.isLoading.set(true);
      const data = await this._repository.getAll({ page: 1 });
      const list = data.items;
      this.cItems.set(new PaginatorHelper(list, this.configFilter().limit ?? 8));
      this.items.set(new PaginatorHelper(list, this.configFilter().limit ?? 8));
      if (!silent) this.isLoading.set(false);
    } catch (error) {
      console.error('Error al cargar validaciones de URL:', error);
      if (!silent) this.isLoading.set(false);
    }
  }

  async toShow(item: AuditUrlValidationItemResponseModel) {
    this.loadingDetail.set(true);
    this.showDetail.set(true);
    try {
      const response = await this._repository.find(item.id);
      this.selectedItem.set(response);
    } catch (e) {
      console.error(e);
    } finally {
      this.loadingDetail.set(false);
    }
  }

  async toRerun(item: AuditUrlValidationItemResponseModel) {
    this.isLoading.set(true);
    try {
      const detail = await this._repository.find(item.id);
      const urls = this.parseResultsJson(detail.results_json)
        .map((result) => result?.url)
        .filter((url): url is string => Boolean(url))
        .join('\n');

      await this._router.navigate(['/admin/audit/url-validations/create'], {
        state: {
          rerunData: {
            source_type: detail.source_type ?? item.source_type ?? 'audit_page',
            source_id: detail.source_id ?? item.source_id ?? '',
            name_validation: detail.name_validation ?? item.name_validation ?? '',
            description_validation: detail.description_validation ?? item.description_validation ?? '',
            ai_instruction: detail.ai_instruction ?? '',
            urls,
          },
        },
      });
    } catch (error) {
      console.error('Error al preparar la re-ejecucion de validacion URL:', error);
      await this._sweetAlertUtil.error(
        'general.messages.error',
        'No se pudo cargar la validacion para re-ejecutarla.'
      );
    } finally {
      this.isLoading.set(false);
    }
  }

  async toDelete(item: AuditUrlValidationItemResponseModel) {
    const result = await this._sweetAlertUtil.fire({
      title: 'Eliminar Validación',
      text: '¿Estás seguro de que deseas eliminar esta validación? Esta acción no se puede deshacer.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#dc3545',
      cancelButtonColor: '#6c757d',
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar',
    });
    if (!result.isConfirmed) return;
    try {
      this.isLoading.set(true);
      await this._repository.delete(item.id);
      await this._sweetAlertUtil.success(
        'general.messages.success',
        'La validación ha sido eliminada correctamente'
      );
    } catch (e) {
      console.error(e);
      await this._sweetAlertUtil.error(
        'general.messages.error',
        'Ocurrió un error al eliminar la validación.'
      );
    } finally {
      await this.init();
    }
  }

  downloadReport(type: 'pdf' | 'word' | 'global_pdf' | 'global_word') {
    const baseUrl = (environment.apiUrl as string).replace('/api/v1', '');
    let path: string | null = null;

    switch (type) {
      case 'pdf':
        path = this.selectedItem().report_pdf_path;
        break;
      case 'word':
        path = this.selectedItem().report_word_path;
        break;
      case 'global_pdf':
        path = this.selectedItem().global_report_pdf_path;
        break;
      case 'global_word':
        path = this.selectedItem().global_report_word_path;
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

  closeDetail() {
    this.showDetail.set(false);
    this.selectedItem.set({} as FindAuditUrlValidationResponseModel);
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

