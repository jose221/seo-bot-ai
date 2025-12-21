import { Component, ElementRef, input, signal, effect, ViewChild, untracked, computed } from '@angular/core';
import { ChartData } from 'chart.js';
import {
  deepCopy,
  deepMerge, isNumberOrText,
  orderBy,
  pushIfNotExist,
  pushIfNotExistByKey,
  validateAndAddOrder
} from "@/app/helper/map-data.helper";
import {Observable} from "rxjs";
import {NgxSkeletonLoaderModule} from "ngx-skeleton-loader";
import { v4 as uuidv4 } from 'uuid';
import {FormsModule} from "@angular/forms";
import {GraphicsFilter} from '@/app/presentation/components/general/charts/bar-chart/bar-chart.filter';
import {TranslatePipe} from '@ngx-translate/core';
import {RoundPipe} from '@/app/pipes/round-pipe';
import {
  BottomModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/bottom-modal/bottom-modal.component';
import {
  HeaderModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/header-modal/header-modal.component';
import {
  BodyModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/body-modal/body-modal.component';
import {NgClass} from '@angular/common';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {TableComponent} from '@/app/presentation/components/general/table/table.component';
import {PaginatorList} from '@/app/presentation/components/general/paginator-list/paginator-list';
import {FilterList} from '@/app/presentation/components/general/filter-list/filter-list';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';
import {
  ColumnsList,
  CustomChartOptions,
  ExtraKeysListAvailable,
  ItemsOptionsInterface
} from '@/app/presentation/utils/models/chartJS.model';
import {ChartJSUtil} from '@/app/presentation/utils/chartJS.util';
import {TableColumn} from '@/app/domain/models/general/table-column.model';


@Component({
  selector: 'app-bar-chart',
  standalone: true,
  imports: [
    NgxSkeletonLoaderModule,
    NgClass,
    FormsModule,
    TranslatePipe,
    //RoundPipe,
    BottomModalComponent,
    HeaderModalComponent,
    BodyModalComponent,
    TableComponent,
    PaginatorList,
    FilterList,
  ],
  templateUrl: './bar-chart.component.html',
  styleUrl: './bar-chart.component.scss'
})
export class BarChartComponent {
  // Signals para inputs
  items = input<Observable<any> | ItemsOptionsInterface | ItemsOptionsInterface[] | any | any[]>([]);
  showAll = input<boolean>(false);
  id = input<string>("");
  xKey = input<string>('label');
  yKey = input<string>('value');
  options = input<CustomChartOptions<'bar'> | any>({
    columnsList: [],
    tableConfig: {
      filters: {}
    },
    hiddenOptions: false,
    hiddenFiltersOptions:[],
    roundValue: 0,
    responsive: true,
    backgroundColorFn: null,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
    },
    scales: {
      y:{
        beginAtZero: true,
        min: 0,
        ma: 100
      },
      x:{
        beginAtZero: true,
        min: 0,
        ma: 100
      }
    }
  });

  // Signals para estados internos
  private rawData = signal<any>([]);
  boolResultadosConBaseEnUnPerfilEsperado = signal<boolean>(true);
  loading = signal<boolean>(true);
  xKeyList = signal<string[] | ColumnsList[]>([]);
  isModalOpen = signal<boolean>(false);
  cOptions = signal<CustomChartOptions<'bar'>>({} as CustomChartOptions<'bar'>);
  columnsList = signal<ColumnsList[]>([]);

  // Computed signal para procesar datos
  data = computed(() => {
    const raw = this.rawData();
    if (!raw || (Array.isArray(raw) && raw.length === 0)) {
      return [];
    }
    return Array.isArray(raw) ? raw : raw;
  });

  graphicsFilter: GraphicsFilter = new GraphicsFilter();

  @ViewChild('chartCanvas', { static: true }) chartCanvas!: ElementRef<HTMLCanvasElement>;
  public chartId: string;
  chartUtil: ChartJSUtil = new ChartJSUtil();

  constructor() {
    this.chartId = uuidv4();

    // Effect para procesar items cuando cambien - SOLO SIGNALS
    effect(() => {
      const itemsValue = this.items();

      // Si itemsValue es un Signal, leerlo
      let actualValue = itemsValue;
      this.processRawData(actualValue);
    });

    // Effect para inicializar cuando las opciones cambien
    effect(() => {
      const opts = this.options();
      if (opts) {
        setTimeout(() => {
          this.cOptions.set(opts);
          this.mapTableColumns()
          this.graphicsFilter.setConfigurations(this.id(), null, opts);
          this.initChart();
        }, 500);
      }
    });

    // Effect para actualizar chart cuando los datos procesados cambien
    effect(() => {
      const processedData = this.data();
      if (processedData && (Array.isArray(processedData) ? processedData.length > 0 : true)) {
        untracked(() => {
          this.loading.set(false);
          setTimeout(() => {
            this.mapTableFilters()
            this.mapTableColumns()
            this.mapTableData()
            this.mapDataConfig()
          }, 2000)
          this.graphicsFilter.setConfigurations(this.id(), processedData);
          setTimeout(() => {
            this.updateChart();
          }, 1000);
        });
      }
    });
  }

  /**
   * Procesar datos raw y actualizar el signal
   */
  private processRawData(data: any): void {
    if (data) {
      this.rawData.set(deepCopy(data));
    }
  }

  private generateDatasets(data: any[] | ItemsOptionsInterface[] | ItemsOptionsInterface | any): any[] {
    return this.chartUtil.generateDatasets(data, this.options().roundValue ?? 0);
  }

  private generateLabels(data: any | ItemsOptionsInterface[] | ItemsOptionsInterface): string[] {
    return this.chartUtil.generateLabels(data, this.xKey());
  }

  initChart(type: any = 'bar', data: any = null) {
    const currentOptions = this.options();

    let chartData: ChartData<any, any[], unknown> | null | undefined = null;
    const mParams = this.graphicsFilter.mapDataOptionsOfFiltersSelected(deepCopy(data), currentOptions, this.cOptions());

    if (mParams.data) {
      chartData = this.chartUtil.mapDataset(data, this.xKey());
      this.mapXkeyList(chartData.labels);
      this.mapColumnList(mParams.data);
    }
    this.cOptions.set(mParams.options);
    this.chartUtil.initChart(this.chartCanvas.nativeElement as HTMLCanvasElement, type, chartData, mParams.options);
  }

  updateChart() {
    const canvas = this.chartCanvas.nativeElement as HTMLCanvasElement;
    const currentData = this.data();
    const mParams = this.graphicsFilter.mapDataOptionsOfFiltersSelected(deepCopy(currentData), this.options(), this.cOptions());
    const datasets = this.generateDatasets(mParams.data);
    const labels = this.generateLabels(mParams.data);

    this.mapColumnList(Array.isArray(currentData) ? currentData : [currentData]);
    this.mapXkeyList(labels);

    const chartData: ChartData<'bar'> = {
      labels,
      datasets,
    };

    this.chartUtil.updateChartData(canvas, chartData);
    this.chartUtil.updateChartOptions(canvas, deepMerge(this.options(), mParams.options));
  }

  destroyChart() {
    this.chartUtil.destroyChart(this.chartCanvas.nativeElement as HTMLCanvasElement);
  }

  get isLoading() {
    return this.loading();
  }

  private mapXkeyList(elements: string[] | any) {
    this.xKeyList.set(pushIfNotExist(this.xKeyList(), elements));
  }

  closeFilters() {
    this.isModalOpen.set(false);
  }

  openFilters() {
    this.isModalOpen.update(value => !value);
  }

  actionCollapse(item: any) {
    item.selected = !item.selected;
  }

  onChangeFilter(filter: any, configuration: any) {
    this.graphicsFilter.select(filter.id, {filter, configuration});
    this.actionFilter(filter, configuration);
  }

  actionFilter(filter: any, configuration: any) {
    console.log("filter", filter)
    console.log("configuration", configuration)
    configuration.selected = true;
    const currentData = this.data();
    const currentOptions = this.options();
    if (Object.values(configuration.datasetOptions).length > 0) {
      const newData = this.graphicsFilter.mapData(currentData, filter, configuration);
      this.rawData.set(newData);
      this.chartUtil.updateChartData(
        this.chartCanvas.nativeElement as HTMLCanvasElement,
        this.chartUtil.mapDataset(newData, this.xKey(), this.options())
      );
    }

    if (Object.values(configuration.options).length > 0) {
      const newOptions = this.graphicsFilter.mapOptions(currentOptions, this.cOptions(), configuration);
      this.cOptions.set(newOptions);
      this.chartUtil.updateChartOptions(this.chartCanvas.nativeElement as HTMLCanvasElement, newOptions);
    }
  }

  get gGraphicsFilter() {
    const hiddenFiltersOptions = this.options().hiddenFiltersOptions ?? [];

    return this.graphicsFilter.data.filter((filter: any) => {
      let isValid = true;
      filter.configurations = (filter.configurations ?? []).filter((configuration: any) => {
        let isValid2 = true;
        if (hiddenFiltersOptions.length > 0) {
          isValid2 = !hiddenFiltersOptions.includes(configuration.id);
        }
        return isValid2;
      });

      if (filter.isHidden || (filter.configurations ?? []).length <= 0) isValid = false;
      return isValid;
    });
  }

  mapColumnList(data: any[] = []) {
    const currentOptions = this.options();
    let currentColumnsList = this.columnsList();

    if (!currentOptions.columnsList?.length) {
      currentColumnsList = pushIfNotExistByKey<ColumnsList[]>(currentColumnsList, {
        column: this.xKey(),
        label: this.xKey(),
        type: 'string'
      }, "column") as ColumnsList[];

      for (const item of data) {
        // ✅ Validar que item.datasetOptions exista antes de acceder a sus propiedades
        if (item && item.datasetOptions && item.datasetOptions.yKey) {
          currentColumnsList = pushIfNotExistByKey<ColumnsList[]>(currentColumnsList, {
            column: item.datasetOptions.yKey,
            label: item.datasetOptions.label || item.datasetOptions.yKey,
            type: 'string'
          }, "column") as ColumnsList[];
        }
      }
    } else {
      currentColumnsList = currentOptions.columnsList;
    }
    this.columnsList.set(currentColumnsList);
    return currentColumnsList;
  }

  findItem(list: any[], value: string) {
    return (list || []).find(x => {
      return x[this.xKey()] === value
    });
  }

  findData(items: any[] | any, column: string, value: string) {
    let res: any = {} as any;
    if (Array.isArray(items)) {
      for (const x of (items || [])) {
        if (!Object.keys(res).length) {
          const fItem = this.findItem(x.value, value);

          if (fItem) {
            if (fItem[column]) {
              res = {...fItem, dataFrom: x};
              break;
            }
          }
        }
      }
    } else {
      const fItem = this.findItem(items.value, value);
      if (fItem) {
        if (fItem[column]) {
          res = {...fItem, dataFrom: items};
        }
      }
    }
    return res as any;
  }

  innerColumn(value: any) {
    return deepCopy(this.columnsList()).map((element: ColumnsList) => {
      element.item = this.findData(this.data(), element.column, value);
      element.type = (['string', 'number'].includes(element.type))
        ? isNumberOrText(element.item[element.column]).isText ? 'string' : 'number'
        : element.type;
      return element;
    });
  }
  tableColumn = signal<TableColumn[]>([]);
  tableData = signal<PaginatorHelper<any[]>>(new PaginatorHelper([], 7));
  cTableData = signal<PaginatorHelper<any[]>>(new PaginatorHelper([], 7));
  tableDataConfigFilter  = signal<FilterListConfig>({})
  mapTableData(){
    const tableData: any[] = [];
    const xKeys = this.xKeyList();
    const columns = this.columnsList();

    for (const xKey of xKeys) {
      const rowData: any = {};
      const innerColumns = this.innerColumn(xKey);

      for (const column of innerColumns) {
        if (!column.item.dataFrom?.noShowTable && !column.hidden?.(column.item)) {
          if (column.html) {
            rowData[column.column] = column.html(column.item);
          } else {
            if (column.type === 'number') {
              rowData[column.column] = this.options()?.roundValue
                ? Number(column.item[column.column]).toFixed(this.options()?.roundValue)
                : column.item[column.column];
            } else {
              rowData[column.column] = column.item[column.column];
            }
          }
        }
      }

      if (Object.keys(rowData).length > 0) {
        tableData.push(rowData);
      }
    }
    this.tableData.set(new PaginatorHelper(tableData, this.tableDataConfigFilter()?.limit ?? 5));
    this.cTableData.set(new PaginatorHelper(tableData, this.tableDataConfigFilter()?.limit ?? 5));
    return tableData;
  }
  mapTableColumns() {
    const currentOptions = this.options();
    let tableColumns: TableColumn[] = deepCopy(this.tableColumn());
    for (const datum of currentOptions.columnsList ?? []) {
      tableColumns = pushIfNotExistByKey<TableColumn[]>(tableColumns, {
        key: datum.column,
        name: datum.label,
        type: datum.type,
        action: datum.action
      }, "key")
    }
    this.tableColumn.set(tableColumns);
  }
  mapTableFilters(){
    const currentOptions = this.options();
    this.tableDataConfigFilter.set(currentOptions?.tableConfig?.filters ?? {})
  }
  dataConfig = signal<any[]>([]);
  mapDataConfig() {
    let currentDataConfig = this.dataConfig();
    const currentData = this.data();
    if(Array.isArray(currentData)){
      for (const datum of currentData) {
        currentDataConfig = pushIfNotExist<any>(currentDataConfig, datum)
      }
      this.dataConfig.set(currentDataConfig);
    }else{
      currentDataConfig = pushIfNotExist<any>(currentDataConfig, currentData)
      this.dataConfig.set(currentDataConfig);
    }
  }

  onChangeKey(key: string, value: ExtraKeysListAvailable){
    const attribute = key =='y' ? 'yKey' : 'xKey';
    const currentData = this.data();
    if(Array.isArray(currentData)){
      currentData.map((datum: ItemsOptionsInterface) => {
        if(datum.value.some((item: any) =>{
          return item.hasOwnProperty(value.key)
        })){
          datum.datasetOptions[attribute] = value.key
        }
        return datum
      })
    }else{
      if(currentData.value.some((item: any) =>{
        return item.hasOwnProperty(value.key)
      })) {
        currentData.datasetOptions[attribute] = value.key
      }
    }
    this.rawData.set(currentData);
    this.updateChart()

  }
}
