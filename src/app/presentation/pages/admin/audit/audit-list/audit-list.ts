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
import {DefaultModal} from '@/app/presentation/components/general/bootstrap/general-modals/default-modal/default-modal';
import {
  BodyModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/body-modal/body-modal.component';
import {
  HeaderModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/header-modal/header-modal.component';
import {
  FooterModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/footer-modal/footer-modal.component';
import {DateFormatPipe} from '@/app/pipes/date-format-pipe';
import {NgClass} from '@angular/common';
import {MarkdownComponent} from 'ngx-markdown';

@Component({
  selector: 'app-audit-list',
  imports: [
    TableComponent,
    PaginatorList,
    FilterList,
    TranslatePipe,
    RouterLink,
    DefaultModal,
    BodyModalComponent,
    HeaderModalComponent,
    FooterModalComponent,
    DateFormatPipe,
    NgClass,
    MarkdownComponent
  ],
  templateUrl: './audit-list.html',
  styleUrl: './audit-list.scss',
})
export class AuditList extends ListDefaultBase<AuditResponseModel> implements OnInit, OnDestroy {
  public statusAuditUtil = inject(StatusAuditUtil);
  private intervalId: any;
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
    await super.ngOnInit();
    this.intervalId = setInterval(() => {
      this.init(true);
    }, 10000);
  }

  ngOnDestroy() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
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
    console.log('item:', item);
    this.showItem.set(item);
  }
  async toDelete(item: AuditResponseModel){
    if(item.id) await this._auditRepository.delete(item.id)
    this.init()
  }

}
