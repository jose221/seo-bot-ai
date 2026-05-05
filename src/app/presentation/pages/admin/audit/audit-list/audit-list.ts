import {isPlatformBrowser} from '@angular/common';
import {Component, inject, signal, OnInit, OnDestroy} from '@angular/core';
import {ListDefaultBase} from '@/app/presentation/shared/list-default.base';
import {AuditResponseModel} from '@/app/domain/models/audit/response/audit-response.model';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {TableColumn} from '@/app/domain/models/general/table-column.model';
import {TableComponent} from '@/app/presentation/components/general/table/table.component';
import {PaginatorList} from '@/app/presentation/components/general/paginator-list/paginator-list';
import {FilterList} from '@/app/presentation/components/general/filter-list/filter-list';
import {TranslatePipe} from '@ngx-translate/core';
import {RouterLink} from '@angular/router';
import {StatusAuditUtil} from '@/app/presentation/utils/status-audit.util';

@Component({
  selector: 'app-audit-list',
  imports: [
    TableComponent,
    PaginatorList,
    FilterList,
    TranslatePipe,
    RouterLink,
  ],
  templateUrl: './audit-list.html',
  styleUrl: './audit-list.scss',
})
export class AuditList extends ListDefaultBase<AuditResponseModel> implements OnInit, OnDestroy {
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
      attributes: ['web_page_id', 'user_id', 'id', 'web_page.name', 'web_page.tech_stack', 'web_page.url'],
      key: "web_page_id",
      defaultValue: "",
      type: "text"
    }
  })
  tableColumn = signal<TableColumn[]>(
    [
      {
        key: 'web_page.name',
        name: 'Página Web',
        type: 'text'
      },
      {
        key: 'status',
        name: 'Estado',
        type: 'text',
        innerHtml: (element: AuditResponseModel)=>{
          const statusClass = this.statusAuditUtil.getStatusClass(element.status);
          const statusText = this.statusAuditUtil.getStatusText(element.status);
          return `<span class="badge ${statusClass}"><span class="status-text">${statusText}</span></span>`;
        },
      },
      {
        key: 'performance_score',
        name: 'Performance Score',
        type: 'text'
      },
      {
        key: 'accessibility_score',
        name: 'Accesibilidad Score',
        type: 'text'
      },
      {
        key: 'best_practices_score',
        name: 'Mejores Prácticas Score',
        type: 'text'
      },
      {
        key: 'fid',
        name: 'FID',
        type: 'text'
      },
      {
        key: 'cls',
        name: 'CLS',
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
        action: (item: AuditResponseModel) => this.toRerun(item)
      },
      {
        key: 'id',
        name: 'Schema',
        type: 'link',
        innerHtml: (element: any) => '<i class="bi bi-braces-asterisk me-1"></i>Schema',
        action: (item: AuditResponseModel) => this._router.navigate(['/admin/audit/schemas/create'], {
          queryParams: { source_type: 'audit_page', source_id: item.id }
        })
      },
      {
        key: 'id',
        name: 'Validar URLs',
        type: 'link',
        innerHtml: (element: any) => '<i class="bi bi-link-45deg me-1"></i>Validar',
        action: (item: AuditResponseModel) => this._router.navigate(['/admin/audit/url-validations/create'], {
          queryParams: { source_type: 'audit_page', source_id: item.id }
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
      const data = await this._auditRepository.get();
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

  async toUpdate(item: AuditResponseModel){
    await this._router.navigate(['/admin/modules/update', item?.id])
  }
  showItem = signal<AuditResponseModel|any>({} as AuditResponseModel)
  async toShow(item: AuditResponseModel){
    this._router.navigate(['/admin/audit', item.id]);
  }

  async toRerun(item: AuditResponseModel) {
    await this._router.navigate(['/admin/audit/create'], {
      queryParams: {
        rerun_audit_id: item.id,
        web_page_id: item.web_page_id ?? '',
      },
    });
  }

  async toDelete(item: AuditResponseModel){
    const result = await this._sweetAlertUtil.fire({
      title: 'general.messages.confirmDelete',
      text: `¿Estás seguro de eliminar esta auditoría? Esta acción no se puede deshacer.`,
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
        if(item.id) await this._auditRepository.delete(item.id);
        await this._sweetAlertUtil.success(
          'general.messages.success',
          'La auditoría ha sido eliminada correctamente'
        );
      } catch (error) {
        console.error('Error al eliminar auditoría:', error);
        await this._sweetAlertUtil.error(
          'general.messages.error',
          'Ocurrió un error al eliminar la auditoría. Por favor, inténtalo de nuevo.'
        );
      } finally {
        await this.init();
      }
    }
  }

}
