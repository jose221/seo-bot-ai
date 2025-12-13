import {Chart, ChartConfiguration, ChartData, ChartType, registerables} from 'chart.js';
import ChartDataLabels from "chartjs-plugin-datalabels";
import {ConfigChartInterface, CustomChartOptions, ItemsOptionsInterface} from "@/utils/models/chartJS.model";


export class ChartJSUtil {
  private defaultOptions: CustomChartOptions|any = {
    responsive: true,
    maintainAspectRatio: false,
    devicePixelRatio: window.devicePixelRatio || 1,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#333',
          font: { size: 12, family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif" },
          boxWidth: 20,
          usePointStyle: true
        }
      },
      title: {
        display: false,
        text: 'Chart Title',
        color: '#666',
        font: { size: 18, weight: "bold" },
        padding: 10,
        align: 'center'
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0,0,0,0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        bodyFont: { size: 12 },
        usePointStyle: true
      }
    },
    scales: {
    },
    elements: {
      bar: {
        borderRadius: 4,
        borderWidth: 0
      },
      line: {
        //tension: 0.4,
        borderWidth: 2
      },
      point: {
        radius: 3,
        hoverRadius: 5
      }
    },
    animations: {
      duration: 800,
      easing: 'easeOutQuad'
    }
  };

  private charts: { [id: string]: Chart }|any = {};

  constructor() {
    Chart.register(...registerables, ChartDataLabels);
  }

  private sanitizeScales<T extends ChartType>(options: CustomChartOptions<T>|any, type: T): CustomChartOptions<T> {
    const sanitizedOptions = { ...options };

    // Elimina configuraciones de escala específicas para gráficos incompatibles
    if (type !== 'radar') {
      delete sanitizedOptions.scales?.r; // Escala "r" solo es válida para radar
    }

    return sanitizedOptions;
  }

  initChart<T extends ChartType>(
    canvas: HTMLCanvasElement,
    type: T,
    data: ChartData<T> | null | undefined,
    options: CustomChartOptions<T> = {} as CustomChartOptions<T>,
    beforeInit?: (config: ConfigChartInterface) => {
      type: T;
      data: ChartData<T> | null | undefined;
      options: CustomChartOptions<T>;
    }
  ): Chart<T> {
    const defaultData: ChartData<T> = {
      labels: [],
      datasets: [],
    };
    //Limpia configuraciones de escalas específicas si no son compatibles
    const sanitizedOptions = this.sanitizeScales(options, type);

    const mergedOptions = this.deepMerge(this.defaultOptions, sanitizedOptions) as CustomChartOptions<T>;

    let config: ConfigChartInterface|any = {
      type,
      data: data || defaultData,
      options: mergedOptions
    };

    if (beforeInit) {
      config = beforeInit(config) as ConfigChartInterface;
    }

    const chart = new Chart(canvas, config as ChartConfiguration<T>);
    this.charts[canvas.id] = chart;

    return chart;
  }

  updateChartOptions(canvas: HTMLCanvasElement, newOptions: CustomChartOptions): void {
    const chart = this.charts[canvas.id];
    if (chart) {
      chart.options = this.deepMerge(newOptions, this.defaultOptions,)
      chart.update();
    }
  }

  updateChartData(canvas: HTMLCanvasElement, newData: ChartData): void {
    const chart = this.getChart(canvas);
    if (chart) {
      chart.data = newData;
      chart.update();
    }
  }

  destroyChart(canvas: HTMLCanvasElement): void {
    const chart = this.getChart(canvas);
    if (chart) {
      chart.destroy();
      delete this.charts[canvas.id];
    }
  }

  getChart(canvas: HTMLCanvasElement): Chart | undefined {
    return this.charts[canvas.id];
  }

  generateDatasets(data: ItemsOptionsInterface[] | ItemsOptionsInterface | any, roundValue: number = 0): any[] {
    const backgroundColors = ["rgba(255, 99, 132, .6)", "rgba(75, 192, 192, 0.6)", "rgba(246,198,105,.6)", "rgba(58,141,209,0.6)"];
    const borderColors = ["rgba(255, 99, 132, 1)", "rgba(75, 192, 192, 1)", "rgba(246,198,105,1)", "rgba(58,141,209,1)"];
    if (Array.isArray(data)) {
      return data.map((group: ItemsOptionsInterface, index: number) => {
        const datasetConfig = group.datasetOptions || {};
        const yKey = datasetConfig.yKey;
        let datad =  group.value.map((item: any) => Number(item[yKey]).toFixed(roundValue))
        let colorsD = (group.backgroundColorFn) ? datad.map((valor: any) => group.backgroundColorFn(valor)) : [];
        return {
          ...datasetConfig,
          label: datasetConfig.label || `Dataset ${index + 1}`,
          data:datad,
          type: datasetConfig.type || 'bar',
          backgroundColor: (colorsD.length) ? colorsD : datasetConfig.backgroundColor || backgroundColors[index] || this.getRandomColor(),
          borderColor: (colorsD.length) ? colorsD.map((color: any) => color.replace('0.2', '1')) : datasetConfig.borderColor || borderColors[index] || this.getRandomColor(),
          borderWidth: datasetConfig.borderWidth || 1,
          fill: datasetConfig.fill || false,
        };
      });
    }
    const datasetConfig = data.datasetOptions || {};
    const yKey = datasetConfig.yKey;
    let datad =  (data.value ?? []).map((item: any) => Number(item[yKey]).toFixed(roundValue))
    let colorsD = (data.backgroundColorFn) ? datad.map((valor: any) => data.backgroundColorFn(valor)) : [];
    return [{
      label: datasetConfig.label || 'Dataset',
      data: datad,
      type: datasetConfig.type || 'bar',
      backgroundColor: (colorsD.length) ? colorsD : datasetConfig.backgroundColor || this.getRandomColor(),
      borderColor: (colorsD.length) ? colorsD.map((color: any) => color.replace('0.2', '1')) : datasetConfig.borderColor || this.getRandomColor(),
      borderWidth: datasetConfig.borderWidth || 1,
      fill: datasetConfig.fill || false,
    }];
  }

  generateLabels(data: ItemsOptionsInterface[] | ItemsOptionsInterface, xKey: string): string[] {
    if (Array.isArray(data)) {
      const firstItem = data[0] as ItemsOptionsInterface;
      // ✅ Validar que firstItem.value exista y sea un array
      if (!firstItem || !firstItem.value || !Array.isArray(firstItem.value)) {
        return [];
      }
      return firstItem.value.map((item: any) => item[xKey]);
    }

    // ✅ Validar que data.value exista para datos no-array
    if (!data || !data.value || !Array.isArray(data.value)) {
    }
    return (data.value ?? []).map((item: any) => item[xKey]);
  }

  private deepMerge(target: any, source: any): any {
    const output = { ...target };
    if (this.isObject(target) && this.isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this.isObject(source[key])) {
          if (!(key in target)) Object.assign(output, { [key]: source[key] });
          else output[key] = this.deepMerge(target[key], source[key]);
        } else if (Array.isArray(source[key])) {
          output[key] = [...(target[key] || []), ...source[key]];
        } else {
          Object.assign(output, { [key]: source[key] });
        }
      });
    }
    return output;
  }

  private isObject(item: any): boolean {
    return item && typeof item === 'object' && !Array.isArray(item);
  }

  private getRandomColor(): string {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgba(${r}, ${g}, ${b}, 0.6)`;
  }
  mapDataset(data: ItemsOptionsInterface[] | ItemsOptionsInterface|any, xKey: string, options?: any): ChartData<any>{
    const datasets = this.generateDatasets(data, options?.roundValue || 0);
    const labels = this.generateLabels(data, xKey);
    return {
      labels,
      datasets,
    };
  }

}
