import {StatusType} from '@/app/domain/types/status.type';

export interface CreateAuditRequestDto {
  include_ai_analysis: boolean
  web_page_id: string
}

export interface FilterAuditRequestDto {
  web_page_id: string
  status_filter: StatusType
  page: number
  page_size: number
}
export interface CompareAuditRequestDto {
  include_ai_analysis: boolean
  web_page_id: string
  web_page_id_to_compare: string[]
}

export interface SearchAuditRequestDto {
  query?: string
  page?: number
  page_size?: number
  status_filter?: StatusType
  min_performance_score?: number
  min_seo_score?: number
  unique_web_page?: boolean
  exclude_web_page_id?: string
}
