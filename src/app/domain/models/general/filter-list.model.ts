
export interface FilterListConfigSearchOption {
  label: string;
  value: string|any;
  checked?: boolean;
  disabled?: boolean;
}
export interface FilterListConfigSearch{
  label: string;
  placeholder: string;
  attributes: string|string[];
  key: string;
  defaultValue: string|any;
  value: string|any;
  type: 'text' | 'number' | 'date' | 'select' | 'checkbox' | 'radio' | 'range';
  options?: any[];
  event?: (value: any) => void;
}
export interface FilterListConfig {
  limit?: number;
  search?: FilterListConfigSearch
  filters?: FilterListConfigSearch[];
}
