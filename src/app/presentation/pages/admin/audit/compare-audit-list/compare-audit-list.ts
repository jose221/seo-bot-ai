import {isPlatformBrowser} from '@angular/common';
import {Component, inject, signal, OnInit, OnDestroy} from '@angular/core';
import {ListDefaultBase} from '@/app/presentation/shared/list-default.base';
import {StatusAuditUtil} from '@/app/presentation/utils/status-audit.util';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {TableColumn} from '@/app/domain/models/general/table-column.model';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {FilterList} from '@/app/presentation/components/general/filter-list/filter-list';
import {PaginatorList} from '@/app/presentation/components/general/paginator-list/paginator-list';
import {RouterLink} from '@angular/router';
import {TableComponent} from '@/app/presentation/components/general/table/table.component';
import {TranslatePipe} from '@ngx-translate/core';

import {
  CompareAuditResponseModel,
  FindCompareAuditResponseModel,
} from '@/app/domain/models/audit/response/audit-response.model';

@Component({
  selector: 'app-compare-audit-list',
  imports: [
    FilterList,
    PaginatorList,
    RouterLink,
    TableComponent,
    TranslatePipe,
  ],
  templateUrl: './compare-audit-list.html',
  styleUrl: './compare-audit-list.scss',
})
export class CompareAuditList  extends ListDefaultBase<CompareAuditResponseModel> implements OnInit, OnDestroy{
  public statusAuditUtil = inject(StatusAuditUtil);
  private intervalId: any;
  autoReload = signal<boolean>(true);
  readonly RELOAD_INTERVAL = 10000;
  configFilter  = signal<FilterListConfig>({
    limit: 6,
    search: {
      label: "Buscar",
      value: "",
      placeholder: "Buscar",
      attributes: ['web_page_id', 'user_id', 'id'],
      key: "web_page_id",
      defaultValue: "",
      type: "text"
    }
  })
  tableColumn = signal<TableColumn[]>(
    [
      {
        key: 'base_url',
        name: 'Página Web',
        type: 'text'
      },
      {
        key: 'status',
        name: 'Estado',
        type: 'text',
        innerHtml: (element: CompareAuditResponseModel)=>{
          const statusClass = this.statusAuditUtil.getStatusClass(element.status);
          const statusText = this.statusAuditUtil.getStatusText(element.status);
          return `<span class="badge ${statusClass}"><span class="status-text">${statusText}</span></span>`;
        },
      },
      {
        key: 'total_competitors',
        name: 'Total Competidores',
        type: 'number'
      },
      {
        key: 'error_message',
        name: 'Mensaje de Error',
        type: 'text'
      },
      {
        key: 'created_at',
        name: 'Creado el',
        type: 'datetime'
      },
      {
        key: 'completed_at',
        name: 'Completado el',
        type: 'datetime'
      },
      {
        key: 'created_at',
        name: 'Ver',
        type: 'link',
        innerHtml: (element: any)=>'Ver',
        action: (item: any) => this.toShow(item)
      },
      {
        key: 'id',
        name: 'Volver a ejecutar',
        type: 'link',
        innerHtml: () => '<i class="bi bi-arrow-repeat me-1"></i>Volver a ejecutar',
        action: (item: CompareAuditResponseModel) => this.toRerun(item)
      },
      {
        key: 'id',
        name: 'Schema',
        type: 'link',
        innerHtml: (element: any) => '<i class="bi bi-braces-asterisk me-1"></i>Schema',
        action: (item: CompareAuditResponseModel) => this._router.navigate(['/admin/audit/schemas/create'], {
          queryParams: { source_type: 'audit_comparison', source_id: item.id }
        })
      },
      {
        key: 'id',
        name: 'Validar URLs',
        type: 'link',
        innerHtml: (element: any) => '<i class="bi bi-link-45deg me-1"></i>Validar',
        action: (item: CompareAuditResponseModel) => this._router.navigate(['/admin/audit/url-validations/create'], {
          queryParams: { source_type: 'audit_comparison', source_id: item.id }
        })
      },
      {
        key: 'created_at',
        name: 'Eliminar',
        type: 'link',
        innerHtml: (element: any)=>'Eliminar',
        action: (item: any) => this.toDelete(item)
      }
    ]
  );
  public showMessageComparison = signal<boolean>(false)
  _auditRepository = inject(AuditRepository)
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

  async init(silent: boolean = false) {
    try {
      if (!silent) this.isLoading.set(true);
      const data = await this._auditRepository.getComparisons();
      console.log('data:', data);
      this.cItems.set(new PaginatorHelper(data, this.configFilter().limit ?? 12));
      this.items.set(new PaginatorHelper(data, this.configFilter().limit ?? 12));
      console.log('items:', this.items());
      if (!silent) this.isLoading.set(false);
    } catch (error) {
      console.error('Error al cargar items:', error);
      if (!silent) this.isLoading.set(false);
    }
  }

  async toUpdate(item: CompareAuditResponseModel){
    await this._router.navigate(['/admin/modules/update', item?.id])
  }
  async toShow(item: CompareAuditResponseModel){
    this._router.navigate(['/admin/audit/comparisons', item.id]);
  }

  private async resolveCompetitorWebPageIds(response: FindCompareAuditResponseModel): Promise<string[]> {
    const auditIds = (response.comparison_result?.comparisons ?? [])
      .map((comparison: any) => comparison.summary?.compare_audit_id as string | undefined)
      .filter((id): id is string => Boolean(id)) ?? [];

    const uniqueAuditIds = Array.from(new Set(auditIds));
    const competitorWebPageIds = await Promise.all(
      uniqueAuditIds.map(async (auditId: string) => {
        try {
          const audit = await this._auditRepository.find(auditId);
          return audit.web_page_id;
        } catch {
          return null;
        }
      })
    );

    return Array.from(
      new Set(
        competitorWebPageIds.filter(
          (id): id is string => Boolean(id) && id !== response.base_web_page_id
        )
      )
    );
  }

  async toRerun(item: CompareAuditResponseModel) {
    this.isLoading.set(true);
    try {
      const detail = await this._auditRepository.findComparisons(item.id);
      const competitorWebPageIds = await this.resolveCompetitorWebPageIds(detail);

      await this._router.navigate(['/admin/audit/compare'], {
        state: {
          rerunData: {
            web_page_id: detail.base_web_page_id ?? item.base_web_page_id ?? '',
            web_page_id_to_compare: competitorWebPageIds,
            include_ai_analysis: (detail as any)?.include_ai_analysis ?? true,
          },
        },
      });
    } catch (error) {
      console.error('Error al preparar la re-ejecucion de comparacion:', error);
      await this._sweetAlertUtil.error(
        'general.messages.error',
        'No se pudo cargar la comparacion para re-ejecutarla.'
      );
    } finally {
      this.isLoading.set(false);
    }
  }

  async toDelete(item: CompareAuditResponseModel){
    const result = await this._sweetAlertUtil.fire({
      title: 'general.messages.confirmDelete',
      text: `¿Estás seguro de eliminar esta comparación? Esta acción no se puede deshacer.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#6c757d',
      confirmButtonText: 'general.actions.delete',
      cancelButtonText: 'general.actions.cancel'
    }, ['title', 'confirmButtonText', 'cancelButtonText']);

    if (result.isConfirmed) {
      try {
        this.isLoading.set(true);
        if(item.id) await this._auditRepository.deleteComparisons(item.id);
        await this._sweetAlertUtil.success(
          'general.messages.success',
          'La comparación ha sido eliminada correctamente'
        );
      } catch (error) {
        console.error('Error al eliminar comparación:', error);
        await this._sweetAlertUtil.error(
          'general.messages.error',
          'Ocurrió un error al eliminar la comparación. Por favor, inténtalo de nuevo.'
        );
      } finally {
        await this.init();
      }
    }
  }

}
