import {Component, effect, input, output, signal} from '@angular/core';
import {PaginatorHelper} from '@/app/helper/paginator.helper';
import {Query} from '@/app/helper/map-data.helper';
import {FormsModule} from '@angular/forms';
import {FilterListConfig} from '@/app/domain/models/general/filter-list.model';


@Component({
  selector: 'app-filter-list',
  imports: [
    FormsModule
  ],
  templateUrl: './filter-list.html',
  standalone: true,
  styleUrl: './filter-list.scss'
})
export class FilterList {
  data = input<PaginatorHelper<any>>({} as PaginatorHelper<any>);
  config = input<FilterListConfig|any>({} as FilterListConfig);
  internalConfig = signal<FilterListConfig>({} as FilterListConfig);
  listLimit = [
    5,
    10,
    15,
    20,
    50,
    100
  ]
  dataChange = output<PaginatorHelper<any>>();

  constructor() {
    effect(() => {
      this.internalConfig.set(this.config());
      if(this.config().limit){
        if(!this.listLimit.includes(this.config().limit)){
          this.listLimit.push(this.config().limit)
          this.listLimit.sort((a, b) => a - b)
        }
      }
      //this.internalData.set(this.data());
    });
  }

  filterData(event: any){
    let result = new Query(this.data().all)
    if(this.internalConfig().search?.attributes){
      result = result.like(this.internalConfig().search?.attributes,`%${this.internalConfig().search?.value ?? this.internalConfig().search?.defaultValue}%`)
    }
    if(this.internalConfig().filters && this.internalConfig().filters?.length){
      for (const filter of this.internalConfig().filters ?? []) {
        result = result.like(filter.attributes, filter.value ?? filter.defaultValue);
      }
    }

    this.changePage(result.get())
  }

  eventChange(event: any, key: string, ){
    this.internalConfig.update(config => {
      const nConfig = {
        ...config
      } as any;
      if(nConfig[key]?.value !== undefined) {
        nConfig[key].value = event;
      }
      return nConfig as FilterListConfig;
    });
    this.filterData(event)
  }

  changePage(result: any[]) {
    //this.internalData.set(new PaginatorHelper(result, this.internalConfig().limit ?? 10));
    this.dataChange.emit(new PaginatorHelper(result, this.internalConfig().limit ?? 10));
  }
  limitChange(event: any){
    this.internalConfig.update(config => {
      const nConfig = {
        ...config
      } as any;
      if(nConfig.limit !== undefined) {
        nConfig.limit = event;
      }
      return nConfig as FilterListConfig;
    });

    this.eventChange(event, 'limit')
  }

}
