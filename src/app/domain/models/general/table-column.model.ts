export interface TableColumn {
  name: string;
  key: string;
  type: 'text' | 'number' | 'datetime' | 'date' | 'button' | 'link' | 'boolean';
  action?: (item: any) => void;
  innerHtml?: ((item: any) => string);
  cssClass?: string;
  href?: string;
}

