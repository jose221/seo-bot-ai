import {ChangeDetectionStrategy, Component, input, output} from '@angular/core';
import {PaginatorHelper} from '@/app/helper/paginator.helper';

@Component({
  selector: 'app-paginator-list',
  imports: [],
  templateUrl: './paginator-list.html',
  styleUrl: './paginator-list.scss',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PaginatorList {
  data = input<PaginatorHelper<any>>({} as PaginatorHelper<any>);
  sizeButtonsPagination = input<number>(10);
  dataChange = output<PaginatorHelper<any>>();


  changePage() {
    // Crear una nueva instancia para forzar la detección de cambios
    const newPaginator = new PaginatorHelper(this.data().all, this.data().pageSize);
    newPaginator.goToPage(this.data().getCurrentPage);
    this.dataChange.emit(newPaginator);
  }
  prevPage() {
    this.data().prevPage();
    this.changePage()
  }
  goToPage(page: number) {
    this.data().goToPage(page);
    this.changePage()
  }
  nextPage() {
    this.data().nextPage();
    this.changePage()
  }



}
