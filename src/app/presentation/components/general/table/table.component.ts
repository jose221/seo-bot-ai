import {ChangeDetectionStrategy, Component, computed, effect, input, output, signal} from '@angular/core';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {DateFormatPipe} from '@/app/pipes/date-format-pipe';
import {getValueByKey, orderBy, orderByDate, orderByString} from '@/app/helper/map-data.helper';
import {RouterLink} from '@angular/router';
import {TableColumn} from '@/app/domain/models/general/table-column.model';

interface SortState {
  key: string;
  ascending: boolean;
}

@Component({
  selector: 'app-table',
  templateUrl: './table.component.html',
  styleUrls: ['./table.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DateFormatPipe
  ],
  standalone: true
})
export class TableComponent {
  // Inputs usando signals de Angular v20+
  data = input<PaginatorHelper<any>>({} as PaginatorHelper<any>);
  readonly labels = input<TableColumn[]>([]);

  // Output opcional para emitir la data modificada
  readonly dataChange = output<any>();

  // Signal para el estado de ordenamiento
  private readonly sortState = signal<SortState>({ key: '', ascending: true });

  // Computed signals para estado derivado reactivo
  protected readonly tableData = computed(() => this.data());
  protected readonly tableColumns = computed(() => this.labels());

  constructor() {
    effect(() => {
      // cambio de estado de las variables
    });
  }

  // Método para manejar acciones de botones/links
  protected handleAction(column: TableColumn, item: unknown): void {
    if (column.action) {
      column.action(item);
      // Emitir los datos actualizados si hay cambios
      this.dataChange.emit(this.tableData());
    }
  }

  // Método para obtener el valor de una celda
  protected getCellValue(item: unknown, key: string): unknown {
    return  getValueByKey(item, key);
  }

  // Método para manejar click en columnas
  protected columnClick(column: TableColumn): void {
    const currentSort = this.sortState();

    if (currentSort.key === column.key) {
      // Cambiar dirección si es la misma columna
      this.sortState.update(state => ({ ...state, ascending: !state.ascending }));
    } else {
      // Nueva columna, orden ascendente por defecto
      this.sortState.set({ key: column.key, ascending: true });
    }

    const updatedSort = this.sortState();
    const sortedData = this.getSortedData(column, updatedSort);
    this.dataChange.emit(sortedData);
  }

  // Método privado para seleccionar la función de ordenamiento apropiada
  private getSortedData(column: TableColumn, sortState: SortState): any[] {
    const { key, ascending } = sortState;
    const sourceData = this.data().all;

    switch (column.type) {
      case 'text':
        return orderByString(sourceData, key, ascending);
      case 'date':
      case 'datetime':
        return orderByDate(sourceData, key, ascending);
      default:
        return orderBy(sourceData, key, ascending);
    }
  }
}
