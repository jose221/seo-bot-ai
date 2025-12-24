import {Component, inject, signal} from '@angular/core';
import {ListDefaultBase} from '@/app/presentation/shared/list-default.base';
import {StatusAuditUtil} from '@/app/presentation/utils/status-audit.util';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {TableColumn} from '@/app/domain/models/general/table-column.model';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {
  BodyModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/body-modal/body-modal.component';
import {DateFormatPipe} from '@/app/pipes/date-format-pipe';
import {DefaultModal} from '@/app/presentation/components/general/bootstrap/general-modals/default-modal/default-modal';
import {FilterList} from '@/app/presentation/components/general/filter-list/filter-list';
import {
  FooterModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/footer-modal/footer-modal.component';
import {
  HeaderModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/header-modal/header-modal.component';
import {PaginatorList} from '@/app/presentation/components/general/paginator-list/paginator-list';
import {RouterLink} from '@angular/router';
import {TableComponent} from '@/app/presentation/components/general/table/table.component';
import {TranslatePipe} from '@ngx-translate/core';
import {DatePipe, DecimalPipe, NgClass} from '@angular/common';
import {
  CompareAuditResponseModel,
  FindCompareAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';
import {MarkdownModule} from 'ngx-markdown';

@Component({
  selector: 'app-compare-audit-list',
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
    DecimalPipe,
    MarkdownModule
  ],
  templateUrl: './compare-audit-list.html',
  styleUrl: './compare-audit-list.scss',
})
export class CompareAuditList  extends ListDefaultBase<CompareAuditResponseModel>{
  public statusAuditUtil = inject(StatusAuditUtil);
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
        key: 'created_at',
        name: 'Eliminar',
        type: 'link',
        innerHtml: (element: any)=>'Eliminar',
        action: (item: any) => this.toDelete(item)
      }
    ]
  );
  public showMessageComparison = signal<boolean>(false)
  public responseCompareAudit = signal<FindCompareAuditResponseModel>({} as FindCompareAuditResponseModel)
  _auditRepository = inject(AuditRepository)
  constructor() {
    super();
  }

  async init() {
    try {
      this.isLoading.set(true);
      const data = await this._auditRepository.getComparisons();
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

  async toUpdate(item: CompareAuditResponseModel){
    await this._router.navigate(['/admin/modules/update', item?.id])
  }
  async toShow(item: CompareAuditResponseModel){
    console.log('item:', item);
    const response =await this._auditRepository.findComparisons(item.id)
    this.responseCompareAudit.set(response)
    this.showMessageComparison.set(true)
    console.log('response:', response);
  }
  async toDelete(item: CompareAuditResponseModel){
    if(item.id) await this._auditRepository.delete(item.id)
    this.init()
  }

}
