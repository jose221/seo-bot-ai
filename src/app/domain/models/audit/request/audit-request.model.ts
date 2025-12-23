import {StatusType} from '@/app/domain/types/status.type';

export class CreateAuditRequestModel {
  constructor(
    public include_ai_analysis: boolean,
    public web_page_id: string
  ) {
  }
}

export class FilterAuditRequestModel {
  constructor(
    public web_page_id: string,
    public status_filter: StatusType,
    public page: number,
    public page_size: number
  ) {
  }
}

export class CompareAuditRequestModel {
  constructor(
    public include_ai_analysis: boolean,
    public web_page_id: string,
    public web_page_id_to_compare: string[]
  ) {
  }
}

export class SearchAuditRequestModel {
  constructor(
    public query?: string,
    public page?: number,
    public page_size?: number,
    public status_filter?: StatusType,
    public min_performance_score?: number,
    public min_seo_score?: number,
    public unique_web_page?: boolean,
    public exclude_web_page_id?: string
  ) {
  }
}
