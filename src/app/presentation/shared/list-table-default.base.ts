import {Directive, WritableSignal} from '@angular/core';
import {TableColumn} from '@/app/domain/models/general/table-column.model';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {ListDefaultBase} from '@/app/presentation/shared/list-default.base';

@Directive()
export abstract class ListTableDefaultBase<model> extends ListDefaultBase<model> {
  //protected abstract readonly form: any
  protected abstract tableColumn: WritableSignal<TableColumn[]>;
  protected abstract configFilter: WritableSignal<FilterListConfig>;
}
