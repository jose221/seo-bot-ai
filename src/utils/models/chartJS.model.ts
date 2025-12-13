import {ChartData, ChartOptions, ChartType, FontSpec, PluginOptionsByType} from 'chart.js';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';

/* INTERFACES PARA DATOS */
export interface DataTableOptions {
  classValue?: (item: any, options: ItemsOptionsInterface) => number | any;
}

export interface ConditionConvertGraphic {
  fromType: string;
  toType: string;
}

export interface DatasetOptions {
  label?: string;
  type?: string;
  yKey?: string;
  xKey?: string;
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  barPercentage?: number;
  categoryPercentage?: number;
  fill?: boolean;
  stack?: string;
  hidden?: boolean;
}

export interface ItemsOptionsInterface {
  noShowTable?: boolean;
  value: any[];
  backgroundColorFn?: any|Function;
  datasetOptions?: DatasetOptions | any;
  dataTableOptions?: DataTableOptions;
  conditionConvertGraphic?: ConditionConvertGraphic[];
  graphicsConfig?:{
    xKeysAvailable?: ExtraKeysListAvailable[];
    yKeysAvailable?: ExtraKeysListAvailable[];
  };
}



/* INTERFACES PARA OPCIONES DEL GRÁFICO */
export interface AxisOptions {
  beginAtZero?: boolean;
  max?: number;
  suggestedMax?: number;
  suggestedMin?: number;
  min?: number;
  title?: {
    display?: boolean;
    text?: string;
    color?: string;
    font?: Partial<FontSpec>;
  };
  ticks?: {
    stepSize?: number;
    color?: string;
    font?: Partial<FontSpec>;
    callback?: (value: any, index: number, values: any[]) => string;
  };
  grid?: {
    display?: boolean;
    color?: string;
    drawOnChartArea?: boolean;
    drawTicks?: boolean;
  };
  type?: 'linear' | 'logarithmic' | 'category' | 'time' | 'timeseries';
  position?: 'left' | 'right' | 'top' | 'bottom';
  stacked?: boolean;
}

export interface TooltipOptions {
  enabled?: boolean;
  mode?: 'nearest' | 'index' | 'dataset' | 'point';
  intersect?: boolean;
  backgroundColor?: string;
  titleColor?: string;
  bodyColor?: string;
  titleFont?: FontSpec;
  bodyFont?: FontSpec|any;
  usePointStyle?: boolean;
  callbacks?: {
    label?: (context: any) => string;
    title?: (context: any[]) => string;
  };
}

export interface LegendOptions {
  display?: boolean;
  position?: 'top' | 'left' | 'bottom' | 'right';
  labels?: {
    color?: string;
    font?: Partial<FontSpec>;
    boxWidth?: number;
    padding?: number;
    usePointStyle?: boolean;
  };
  onClick?: (event: MouseEvent, legendItem: any, legend: any) => void;
}

export interface TitleOptions {
  display?: boolean;
  text?: string;
  color?: string;
  font?: FontSpec|any;
  position?: 'top' | 'left' | 'bottom' | 'right';
  padding?: number | { top: number; bottom: number };
  align?: 'start' | 'center' | 'end';
}

export interface AnimationOptions {
  duration?: number;
  easing?: 'linear' | 'easeInQuad' | 'easeOutQuad' | 'easeInOutQuad';
  loop?: boolean;
}

export interface InteractionOptions {
  mode?: 'nearest' | 'index' | 'dataset' | 'point';
  intersect?: boolean;
}

export interface LayoutOptions {
  padding?: number | { top: number; right: number; bottom: number; left: number };
  autoPadding?: boolean;
}

export type ColumnType = 'string'| 'number' | 'button' | 'checkbox' | 'icon';

export interface ColumnsList {
  column: string;
  label: string;
  html?: (item: any) => string;
  type: ColumnType;
  action?: (item: any) => void;
  classAction?: string;
  item?: any
  hidden?: (item: any) => boolean;
  active?: boolean;
}

export type CustomChartOptions<T extends ChartType = ChartType> = ChartOptions<T> & {
  hiddenOptions?: boolean;
  hiddenFiltersOptions?: string[];
  roundValue?: number;
  indexAxis?: 'x' | 'y';
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  devicePixelRatio?: number;
  plugins?: {
    legend?: LegendOptions;
    tooltip?: TooltipOptions;
    title?: TitleOptions|any;
    datalabels?: PluginOptionsByType<T>;
  }|any;
  scales?: {
    x?: AxisOptions;
    y?: AxisOptions;
    [key: string]: AxisOptions | undefined;
  };
  animations?: AnimationOptions|any;
  interaction?: InteractionOptions;
  layout?: LayoutOptions;
  elements?: {
    line?: {
      tension?: number;
      borderWidth?: number;
      borderDash?: number[];
    };
    point?: {
      radius?: number;
      hoverRadius?: number;
      hitRadius?: number;
    };
    bar?: {
      borderWidth?: number;
      borderRadius?: number | { topLeft: number; topRight: number; bottomLeft: number; bottomRight: number };
    };
  };
  columnsList?: ColumnsList[]|ColumnsList|any|any[];
  tableConfig?: {
    filters: FilterListConfig|any
  };
};

export interface ConfigChartInterface {
  type: any;
  data: ChartData<any, any[], unknown> | null | undefined;
  options: CustomChartOptions;
}


export interface ExtraKeysListAvailable{
  key: string;
  label: string;
}
