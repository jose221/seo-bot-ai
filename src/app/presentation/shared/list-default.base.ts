import {Directive, effect, inject, OnDestroy, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {SweetAlertUtil} from '@/app/presentation/utils/sweetAlert.util';
import {Router} from '@angular/router';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {LoadingService} from '@/app/helper/loading.service';
import {ToastService} from '@/app/helper/toast.service';

@Directive()
export abstract class ListDefaultBase<model> implements OnDestroy {
  //protected abstract readonly form: any
  cItems = signal<PaginatorHelper<model>>(new PaginatorHelper([], 12));
  items = signal<PaginatorHelper<model>>(new PaginatorHelper([], 12));
  loadingService = inject(LoadingService)
  protected readonly toastService = inject(ToastService);
  protected isLoading = signal<boolean>(true);
  protected readonly _sweetAlertUtil = inject(SweetAlertUtil)
  protected readonly  _router = inject(Router)
  protected readonly platformId = inject(PLATFORM_ID);

  constructor() {
    effect(() => {
      if (isPlatformBrowser(this.platformId)) {
        if (this.isLoading()) {
          this.loadingService.show();
        } else {
          this.loadingService.hide();
        }
      }
    });
  }

  protected abstract init(): void;

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.init();
    }
  }

  ngOnDestroy() {
    // Evita que el overlay global quede visible al navegar fuera del listado.
    this.loadingService.hide();
  }
}
