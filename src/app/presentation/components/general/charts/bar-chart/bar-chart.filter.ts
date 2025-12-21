import {deepMerge, getRepeatedElements, getValueByKey, orderBySimple, uniqueSimpleArray} from "@/app/helper/map-data.helper";
import {ConditionConvertGraphic, CustomChartOptions} from '@/app/presentation/utils/models/chartJS.model';

export interface GraphicsFilterInterface {
  id: string;
  label: string;
  selected: boolean;
  isHidden: boolean;
  primaryConfigurationReference?: string;
  configurations: {
    id: string;
    label: string;
    options?: any;
    datasetOptions?: any;
    selected: boolean;
    cleanOptions?: boolean;
    hiddenFiltersId?: string[];
  }[];
  onChange?: (filter: any, configuration: any) => void|any;
}

export class GraphicsFilter {
  selectedFilters: any = {} as any;
  id: string = "default-filter-id";
  filters: GraphicsFilterInterface[] = [
    {
      isHidden: false,
      id: "change-orientation-graphics",
      label: "Cambiar orientación del grafico",
      selected: false,
      primaryConfigurationReference:"options.indexAxis",
      configurations:[
        {
          id:'vertical',
          label: 'Vertical',
          options:{
            indexAxis: "x",
            scales: {
              y:{
                beginAtZero: true,
                suggestedMax: 100,
                min: 0, // Forzar el mínimo a 0
              },
              x:{
                beginAtZero: true, // Esto asegura que el eje comience en 0 automáticamente (si no se usa `min`)
              }
            }
          },
          datasetOptions: {},
          selected: true,
          cleanOptions: false,
          hiddenFiltersId:[]
        },
        {
          id:'horizontal',
          label: 'Horizontal',
          options:{
            indexAxis: "y",
            scales: {
              y:{
                beginAtZero: true, // Esto asegura que el eje comience en 0 automáticamente (si no se usa `min`)
              },
              x:{
                suggestedMax: 100,
                beginAtZero: true,
                min: 0, // Forzar el mínimo a 0
                max: 100
              }
            }
          },
          datasetOptions: {},
          selected: false,
          cleanOptions: false,
          hiddenFiltersId:[]
        }
      ],
      onChange: (filter: any, configuration: any) => {


      }
    },
    {
      isHidden: false,
      id: "change-graphics",
      label: "Cambiar graficos",
      selected: true,
      primaryConfigurationReference: "datasetOptions.type",
      configurations:[
        {
          id:'bar',
          label: 'Barras',
          options:{
            scales: {
              r: undefined
            }
          },
          datasetOptions: {
            type: 'bar',
            fill: true,
            borderWidth: 2,
          },
          selected: true,
          cleanOptions: false,
        },
        {
          id:'line',
          label: 'Lineas',
          options:{
            scales: {
              r: {}
            }
          },
          datasetOptions: {
            type: 'line',
            fill: false,
            borderWidth: 2,
          },
          selected: false,
          cleanOptions: false,
          hiddenFiltersId:[]
        },
        {
          id:'radar',
          label: 'Radar',
          options:{
            roundValue: 0,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: true,
                position: 'top',
              },
            },
            elements: {
              line: {
                borderWidth: 3
              }
            },
            scales: {}
          },
          datasetOptions: {
            type: 'radar',
            fill: true,
            borderWidth: 2,
          },
          cleanOptions: true,
          selected: false,
          hiddenFiltersId:['change-orientation-graphics']
        }
      ],
      onChange: (filter: any, configuration: any) => {

      }
    }
  ];
  copy: any = {}
  constructor(id?: string) {
    if(id) this.setConfigurations(id);
  }
  setConfigurations(id: string, data?: any, options?: any){
    this.id = id;
    const filters = this.autoSelectedFilters(data, options)
    this.initSelectedFilters();
  }
  initSelectedFilters(){
    this.selectedFilters = this.defaultSelected();
    for (const params of Object.values(this.selectedFilters) as any) {
      if (params && params?.filter && params?.configuration) {
        this.select(params?.filter.id, params, false);
      }
    }
  }
  getSelectedFiltersSaved(){
    const res = sessionStorage.getItem(this.id)
    return res ? JSON.parse(res || '{}') : null
  }
  autoSelectedFilters(data?: any, options?: any){
    let mData = data ? Array.isArray(data) ? data : [data] : [];
    this.filters.map((filter: any)=>{
      if(options){
        const valueOptions = getValueByKey({options}, filter.primaryConfigurationReference)
        if(valueOptions){
          filter.configurations.map((conf: any)=>{
            conf.selected = getValueByKey(conf, filter.primaryConfigurationReference) == valueOptions;
            if(conf.selected) this.select(filter.id, {filter, configuration: conf}, false);
            return conf
          })
        }

      }
      const values = getRepeatedElements(mData.map((item: any)=>{
        return getValueByKey(item, filter.primaryConfigurationReference)
      }))
      if(values.length && values[0]){
        const value = values[0];
        filter.configurations.map((conf: any)=>{
          const isValue = getValueByKey(conf, filter.primaryConfigurationReference)
          conf.selected = isValue == value;
          //filter.selected = conf.selected;
          if(conf.selected) this.select(filter.id, {filter, configuration: conf}, false);
          return conf
        })
      }

      return filter;
    })
    return this.filters
  }
  private defaultSelected(key? : string):any{
    let result: any = {}
    let filters: any = this.filters.filter((filter: any) => {
      if(key) return key == filter.id;
      return filter.configurations.find((configuration: any) => configuration.selected)
    }) ?? {}
    filters.forEach((filter: any) => {
      const configuration = (filter?.configurations ?? []).find((configuration: any) => {
        return configuration.selected
      }) ?? {}
      result[filter.id] = {filter, configuration}
    })

    return key ? result[key] ?? {} : result;
  }
  select(key: string, data: {filter: any, configuration: any}, autoSave: boolean = true){
    if(data){
      data.configuration.selected = true;
      this.selectedFilters[key] = data;
    }
    //if(this.id && autoSave) sessionStorage.setItem(this.id, JSON.stringify(this.selectedFilters));

    this.filters.find((cif: any)=>cif.id === data.filter.id)?.configurations.map((conf: any)=>{
      conf.selected = conf.label === data.configuration.label;
      return conf
    })
    this.filters = this.filters.map((cif: any)=>{
      cif.isHidden = !!(data.configuration.hiddenFiltersId ?? []).includes(cif.id);
      return cif
    })

  }
  filterSelected(key?: string): any{
    return (key ? this.selectedFilters[key] : this.selectedFilters) ?? this.defaultSelected(key);
  }
  mapData(data: any|any[], filter: any, configuration: any){
    if(Array.isArray(data)){
      return data.map((item: any)=>{
        // Validar que item y datasetOptions existan antes de acceder
        if(!item || !item.datasetOptions){
          item.datasetOptions = configuration.datasetOptions ?? {};
          return item;
        }

        const condition = (item.datasetOptions.conditionConvertGraphic ?? []).find((ccg: ConditionConvertGraphic)=>ccg.fromType == configuration.datasetOptions?.type)
        if(condition){
          configuration = (filter.configurations ?? []).find((conf: any)=>conf.datasetOptions.type === condition.toType) ?? configuration;
        }

        item.datasetOptions = deepMerge(item.datasetOptions, configuration.datasetOptions)
        return item
      })
    }else{
      // Validar que data y datasetOptions existan
      if(!data || !data.datasetOptions){
        data.datasetOptions = configuration.datasetOptions ?? {};
        return data;
      }

      const condition = (data.datasetOptions.conditionConvertGraphic ?? []).find((ccg: ConditionConvertGraphic)=>ccg.fromType == configuration.datasetOptions?.type)
      if(condition){
        configuration = (filter.configurations ?? []).find((conf: any)=>conf.datasetOptions.type === condition.toType) ?? configuration;
      }
      data.datasetOptions = deepMerge(data.datasetOptions, configuration.datasetOptions)
    }
    return data
  }
  mapOptions(options: CustomChartOptions<'bar'>, cOptions: CustomChartOptions<'bar'>, configuration: any){4
    if(configuration.cleanOptions){
      options = configuration.options as CustomChartOptions<'bar'>;
    }else{
      options = deepMerge(cOptions ?? {}, configuration.options)
    }
    return options
  }

  get data(){
    return this.filters ?? [];
  }
  mapDataOptionsOfFiltersSelected(data?: any, options?: any, cOptions?: any):{data: any, options: any}{
    this.initSelectedFilters()
    //for loop
    for (const params of Object.values(this.filterSelected()) as any) {
      if (params && params?.filter && params?.configuration) {
        if(data) data = this.mapData(data, params?.filter, params?.configuration);
        options = this.mapOptions(options, cOptions ?? options, params?.configuration);
      }
    }
    return {data, options}
  }
}
