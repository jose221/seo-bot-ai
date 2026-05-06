import {isPlatformBrowser} from '@angular/common';
import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { ListDefaultBase } from '@/app/presentation/shared/list-default.base';
import { StatusAuditUtil } from '@/app/presentation/utils/status-audit.util';
import { FilterListConfig } from '@/app/domain/models/general/filter-list.model';
import { TableColumn } from '@/app/domain/models/general/table-column.model';
import { PaginatorHelper } from '@/app/helper/paginator.helper';
import { RouterLink } from '@angular/router';
import { NgClass } from '@angular/common';
import { TranslatePipe } from '@ngx-translate/core';
import { AuditSchemaRepository } from '@/app/domain/repositories/audit-schema/audit-schema.repository';
import { AuditSchemaItemResponseModel, FindAuditSchemaResponseModel } from '@/app/domain/models/audit-schema/response/audit-schema-response.model';
import { FilterList } from '@/app/presentation/components/general/filter-list/filter-list';
import { PaginatorList } from '@/app/presentation/components/general/paginator-list/paginator-list';
import { TableComponent } from '@/app/presentation/components/general/table/table.component';

@Component({
  selector: 'app-audit-schema-list',
  imports: [
    FilterList,
    PaginatorList,
    RouterLink,
    TableComponent,
    TranslatePipe,
  
  ],
  templateUrl: './audit-schema-list.html',
  styleUrl: './audit-schema-list.scss',
})
export class AuditSchemaList extends ListDefaultBase<AuditSchemaItemResponseModel> implements OnInit, OnDestroy {
  public statusUtil = inject(StatusAuditUtil);
  private readonly _auditSchemaRepository = inject(AuditSchemaRepository);
  private intervalId: any;
  autoReload = signal<boolean>(true);
  readonly RELOAD_INTERVAL = 12000;

  configFilter = signal<FilterListConfig>({
    limit: 8,
    search: {
      label: 'Buscar',
      value: '',
      placeholder: 'Buscar por ID o fuente...',
      attributes: ['id', 'source_id', 'source_type'],
      key: 'id',
      defaultValue: '',
      type: 'text',
    },
  });

  tableColumn = signal<TableColumn[]>([
    {
      key: 'source_type',
      name: 'Tipo de Fuente',
      type: 'text',
    },
    {
      key: 'source_id',
      name: 'ID de Fuente',
      type: 'text',
    },
    {
      key: 'status',
      name: 'Estado',
      type: 'text',
      innerHtml: (element: AuditSchemaItemResponseModel) => {
        const cls = this.statusUtil.getStatusClass(element.status as any);
        const txt = this.statusUtil.getStatusText(element.status as any);
        return `<span class="badge ${cls}"><span class="status-text">${txt}</span></span>`;
      },
    },
    {
      key: 'programming_language',
      name: 'Lenguaje',
      type: 'text',
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
      name: 'Ver',
      type: 'link',
      innerHtml: () => 'Ver',
      action: (item: AuditSchemaItemResponseModel) => this.toShow(item),
    },
    {
      key: 'id',
      name: 'Volver a ejecutar',
      type: 'link',
      innerHtml: () => '<i class="bi bi-arrow-repeat me-1"></i>Volver a ejecutar',
      action: (item: AuditSchemaItemResponseModel) => this.toRerun(item),
    },
    {
      key: 'id',
      name: 'Validar URLs',
      type: 'link',
      innerHtml: () => '<i class="bi bi-link-45deg me-1"></i>Validar',
      action: (item: AuditSchemaItemResponseModel) => this._router.navigate(['/admin/audit/url-validations/create'], {
        queryParams: { source_type: item.source_type, source_id: item.source_id }
      }),
    },
    {
      key: 'id',
      name: 'Eliminar',
      type: 'link',
      innerHtml: () => 'Eliminar',
      action: (item: AuditSchemaItemResponseModel) => this.toDelete(item),
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
    this.autoReload.update(v => !v);
  }

  async init(silent = false) {
    if (!silent) this.isLoading.set(true);
    try {
      const data = await this._auditSchemaRepository.getAll({ page: 1 });
      const list = data.items;
      this.cItems.set(new PaginatorHelper(list, this.configFilter().limit ?? 8));
      this.items.set(new PaginatorHelper(list, this.configFilter().limit ?? 8));
    } catch (error) {
      console.error('Error al cargar audit schemas:', error);
    } finally {
      if (!silent) this.isLoading.set(false);
    }
  }

  async toShow(item: AuditSchemaItemResponseModel) {
    this._router.navigate(['/admin/audit/schemas', item.id]);
  }

  private getSchemaJsonForRerun(item: FindAuditSchemaResponseModel): string {
    const incoming = item.incoming_schema_json;
    if (incoming?.trim()) return incoming;
    if (incoming) return JSON.stringify(incoming, null, 2);
    if (item.proposed_schema_json) return JSON.stringify(item.proposed_schema_json, null, 2);
    return '';
  }

  async toRerun(item: AuditSchemaItemResponseModel) {
    this.isLoading.set(true);
    try {
      const detail = await this._auditSchemaRepository.find(item.id);
      await this._router.navigate(['/admin/audit/schemas/create'], {
        state: {
          rerunData: {
            source_type: detail.source_type ?? item.source_type ?? 'audit_page',
            source_id: detail.source_id ?? item.source_id ?? '',
            programming_language: detail.programming_language ?? 'c#',
            include_ai_analysis: detail.include_ai_analysis ?? true,
            modified_schema_json: this.getSchemaJsonForRerun(detail),
          },
        },
      });
    } catch (error) {
      console.error('Error al preparar la re-ejecucion de schema:', error);
      await this._sweetAlertUtil.error(
        'general.messages.error',
        'No se pudo cargar el schema para re-ejecutarlo.'
      );
    } finally {
      this.isLoading.set(false);
    }
  }

  async toDelete(item: AuditSchemaItemResponseModel) {
    const result = await this._sweetAlertUtil.fire({
      title: 'Eliminar Propuesta',
      text: '¿Estás seguro de que deseas eliminar esta propuesta? Esta acción no se puede deshacer.',
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
      await this._auditSchemaRepository.delete(item.id);
      await this.init(true);
      this.toastService.success('La propuesta ha sido eliminada correctamente');
    } catch (e) {
      console.error(e);
      await this._sweetAlertUtil.error(
        'general.messages.error',
        'Ocurrió un error al eliminar la propuesta. Por favor, inténtalo de nuevo.'
      );
    } finally {
      this.isLoading.set(false);
    }
  }

}
