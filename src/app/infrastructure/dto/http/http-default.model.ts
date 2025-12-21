export interface HttpDefaultModel<model>{
  code: number;
  message: string;
  length: number;
  data: model|model[]|any;
  extra: object|string|null;
}


export interface HttpItemsModel<model>{
  total: number;
  page: number;
  page_size: number;
  items: model|model[]|any;
}


