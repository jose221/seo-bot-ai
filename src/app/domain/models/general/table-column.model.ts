export interface TableColumn {
  name: string;
  key: string;
  type: 'text' | 'number' | 'datetime' | 'date' | 'button' | 'link' | 'boolean';
  action?: (item: unknown) => void;
  innerHtml?: string;
  cssClass?: string;
  href?: string;
}

