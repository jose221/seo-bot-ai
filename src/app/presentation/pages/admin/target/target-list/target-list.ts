import {Component, inject, signal} from '@angular/core';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {ListDefaultBase} from '@/app/presentation/shared/list-default.base';
import {FilterList} from '@/app/presentation/components/general/filter-list/filter-list';
import {PaginatorList} from '@/app/presentation/components/general/paginator-list/paginator-list';
import {TranslatePipe} from '@ngx-translate/core';
import {RouterLink} from '@angular/router';

@Component({
  selector: 'app-target-list',
  imports: [
    FilterList,
    PaginatorList,
    TranslatePipe,
    RouterLink
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
      this.cItems.set(new PaginatorHelper(data, this.configFilter().limit ?? 12));
      this.items.set(new PaginatorHelper(data, this.configFilter().limit ?? 12));
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
    const result = await this._sweetAlertUtil.fire({
      title: 'general.messages.confirmDelete',
      text: `¿Estás seguro de eliminar "${item.name}"? Esta acción marcará el target como inactivo.`,
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
        await this._targetRepository.delete(item.id as any);
        await this._sweetAlertUtil.success(
          'general.messages.success',
          'El target ha sido eliminado correctamente'
        );
        // Recargar la lista después de eliminar
        await this.init();
      } catch (error) {
        console.error('Error al eliminar target:', error);
        await this._sweetAlertUtil.error(
          'general.messages.error',
          'Ocurrió un error al eliminar el target. Por favor, inténtalo de nuevo.'
        );
        this.isLoading.set(false);
      }
    }
  }

  navigateToAudit(itemId: string) {
    this._router.navigate(['/admin/audit/create'], {
      queryParams: { web_page_id: itemId }
    });
  }

}
