export interface HttpDefaultModel<model>{
  code: number;
  message: string;
  length: number;
  data: model|model[]|any;
  extra: object|string|null;
}
