import {Component, inject, signal} from '@angular/core';
import {ListDefaultBase} from '@/app/presentation/shared/list-default.base';
import {AuditResponseModel} from '@/app/domain/models/audit/response/audit-response.model';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {TableColumn} from '@/app/domain/models/general/table-column.model';
import {TableComponent} from '@/app/presentation/components/general/table/table.component';
import {PaginatorList} from '@/app/presentation/components/general/paginator-list/paginator-list';
import {FilterList} from '@/app/presentation/components/general/filter-list/filter-list';

@Component({
  selector: 'app-audit-list',
  imports: [
    TableComponent,
    PaginatorList,
    FilterList
  ],
  templateUrl: './audit-list.html',
  styleUrl: './audit-list.scss',
})
export class AuditList extends ListDefaultBase<AuditResponseModel>{
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
        key: 'web_page.name',
        name: 'Página Web',
        type: 'text'
      },
      {
        key: 'status',
        name: 'Estado',
        type: 'text',
        innerHtml: (element: AuditResponseModel)=>{
          const statusClass = `status-${element.status.replace('_', '-')}`;
          const statusText = this.getStatusText(element.status);
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
        action: (item: any) => this.toDelete(item)
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

  async init() {
    try {
      this.isLoading.set(true);
      const data = await this._auditRepository.get();
      console.log('data:', data);
      this.cItems.set(new PaginatorHelper(data, this.configFilter().limit ?? 12));
      this.items.set(new PaginatorHelper(data, this.configFilter().limit ?? 12));
      console.log('items:', this.items());
      this.isLoading.set(false);
    } catch (error) {
      console.error('Error al cargar items:', error);
      this.isLoading.set(false);
    }
  }

  async toUpdate(item: AuditResponseModel){
    await this._router.navigate(['/admin/modules/update', item?.id])
  }
  async toShow(item: AuditResponseModel){
    await this._router.navigate(['/admin/modules', item?.id])
  }
  async toDelete(item: AuditResponseModel){
    await this._router.navigate(['/admin/modules', item?.id])
  }

  private getStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      'pending': 'Pendiente',
      'in_progress': 'En Progreso',
      'completed': 'Completado',
      'failed': 'Fallido'
    };
    return statusMap[status] || status;
  }

}
