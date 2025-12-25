import {Directive, effect, inject, Injectable, signal, WritableSignal} from '@angular/core';
import {ValidationMessagesUtil} from '@/app/presentation/utils/validationMessages.util';
import {SweetAlertUtil} from '@/app/presentation/utils/sweetAlert.util';
import {Router} from '@angular/router';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';
import {TableColumn} from '@/app/domain/models/general/table-column.model';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {LoadingService} from '@/app/helper/loading.service';

@Directive()
export abstract class ListDefaultBase<model> {
  //protected abstract readonly form: any
  cItems = signal<PaginatorHelper<model>>(new PaginatorHelper([], 12));
  items = signal<PaginatorHelper<model>>(new PaginatorHelper([], 12));
  loadingService = inject(LoadingService)
  protected isLoading = signal<boolean>(true);
  protected readonly _sweetAlertUtil = inject(SweetAlertUtil)
  protected readonly  _router = inject(Router)
  constructor() {
    effect(() => {
      if (this.isLoading()) {
        this.loadingService.show();
      } else {
        this.loadingService.hide();
      }
    });
  }

  protected abstract init(): void;

  ngOnInit() {
    this.init();
  }
}
