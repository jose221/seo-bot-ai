import { Injectable, NgZone } from "@angular/core";
import {ResponsiveCheckHelper} from '@/app/helper/responsive-check.helper';
declare var Plotly: any;

/***Documentation**/
//https://plotly.com/javascript/reference/layout/#layout-autosize

@Injectable({
  providedIn: 'root'
})
export class PlotlyUtil {
  element = null
  private responsiveCheckHelper: ResponsiveCheckHelper = new ResponsiveCheckHelper()
  constructor(private zone: NgZone) {

  }
  config: any =  {
    modeBarButtonsToRemove: ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
  };
  layout: any = {
    autosize: true,
    title: '',
    font: { size: 8 },
    legend: {
      x: 0.5,
      y: -0.1,
      xanchor: 'center',
      orientation: 'h'
    }
  };
  roundToTwoDecimals(num: number, decimals: number = 2) {
    return num.toFixed(decimals);
  }

  convert_to_xy_format(dataList: Array<any> = [], type = "bar", xKey = "", xValue = "") {
    let obj: any = {};
    if (xKey) {
      obj.x = dataList.map(item => item[xKey]);
    }
    if (xValue) {
      obj.y = dataList.map(item => item[xValue]);
    }
    obj.type = type;

    return obj;
  }
  convert_just_to_xy_format(dataList: Array<any> = [], xKey = "", xValue = "") {
    let obj: any = {};
    if (xKey) {
      obj.x = dataList.map(item => item[xKey]);
    }
    if (xValue) {
      obj.y = dataList.map(item => item[xValue]);
    }

    return obj;
  }
  convert_just_to_labels_values_format(dataList: Array<any> = [], xKey = "", xValue = ""){
    let items = (this.convert_just_to_xy_format(dataList, xKey, xValue) ?? []);
    return {
      ...items,
      labels: items.x,
      values: items.y
    }
  }
  convertFormatAndRenameKeys(dataList: Array<any> = [], xKey: string = "", xValue:string = "", newKey:string="x", newValue:string="y"){
    let items = (this.convert_just_to_xy_format(dataList, xKey, xValue) ?? []);
    return {
      ...items,
      [newKey]: items.x,
      [newValue]: items.y
    }
  }

  private getLayout(layout: any){
    return {
      ...this.layout,
      ...layout
    };
  }
  private getConfig(config: any){
    return {
      ...this.config,
      ...config
    };
  }

  initPlot(element: any, data: Array<any>, layout = {}, config = {}) {
    config = this.getConfig(config)
    layout = this.getLayout(layout)
    return this.zone.runOutsideAngular(() => {
      let plot = Plotly.newPlot(element, data, layout, config);
      this.element = element
      return plot;
    });
  }
  deleteTraces(element: any, layout = [0]){
    Plotly.deleteTraces(element, layout);
  }

  purge(element: any){
    Plotly.purge(element);
  }

  updateTraces(element: any, data: any | any[] = [], layout: any = {}, config: any = {}) {
    layout = this.getLayout(layout)
    config = this.getConfig(config)
    try {
      return this.zone.runOutsideAngular(() => {
        let plotUpdate = Plotly.react(element, data, layout, config).then(()=>{
          setTimeout(()=>{
            try {
              this.resize(element);
            }catch (e){
              this.resize(element);
            }
          }, 2000)
          this.element = element
        });
        return plotUpdate;
      });
    } catch (e) {
      console.error(e);
    }
  }
  update(element: any, data: any | any[] = []){
    data = data.forEach((item: any) => {
      Plotly.update(element, item);
    })
  }
  resize(element: any){
    try {
      Plotly.Plots.resize(element).catch((e: any)=>{
      });
    }catch (e: any){

    }
  }

  relayout(element: any, options: any){
    Plotly.relayout(element, options)
  }

  limitItems(array: any[], limit: number = 100, last: boolean = false): any[] {
    if (last) {
      return array.slice(-limit);
    } else {
      return array.slice(0, limit);
    }
  }
}
