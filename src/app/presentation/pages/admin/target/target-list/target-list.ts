import {Component, inject, signal} from '@angular/core';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {TableColumn} from '@/app/domain/models/general/table-column.model';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {ListTableDefaultBase} from '@/app/presentation/shared/list-table-default.base';
import {ListDefaultBase} from '@/app/presentation/shared/list-default.base';
import {FilterList} from '@/app/presentation/components/general/filter-list/filter-list';
import {PaginatorList} from '@/app/presentation/components/general/paginator-list/paginator-list';
import {TranslatePipe} from '@ngx-translate/core';

@Component({
  selector: 'app-target-list',
  imports: [
    FilterList,
    PaginatorList,
    TranslatePipe
  ],
  templateUrl: './target-list.html',
  styleUrl: './target-list.scss',
})
export class TargetList extends ListDefaultBase<TargetResponseModel>{

  configFilter  = signal<FilterListConfig>({
    limit: 6,
    search: {
      label: "Buscar",
      value: "",
      placeholder: "Buscar",
      attributes: ['name', 'url', 'tech_stack'],
      key: "name",
      defaultValue: "",
      type: "text"
    }
  })
  _targetRepository = inject(TargetRepository)
  constructor() {
    super();
  }

  async init() {
    try {
      this.isLoading.set(true);
      const data = await this._targetRepository.get();
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

  async toUpdate(item: TargetResponseModel){
    await this._router.navigate(['/admin/modules/update', item?.id])
  }
  async toShow(item: TargetResponseModel){
    await this._router.navigate(['/admin/modules', item?.id])
  }
  async toDelete(item: TargetResponseModel){
    await this._router.navigate(['/admin/modules', item?.id])
  }



}
