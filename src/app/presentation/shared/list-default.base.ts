import {Directive, effect, inject, OnDestroy, signal} from '@angular/core';
import {SweetAlertUtil} from '@/app/presentation/utils/sweetAlert.util';
import {Router} from '@angular/router';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {LoadingService} from '@/app/helper/loading.service';

@Directive()
export abstract class ListDefaultBase<model> implements OnDestroy {
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

  ngOnDestroy() {
    // Evita que el overlay global quede visible al navegar fuera del listado.
    this.loadingService.hide();
  }
}
