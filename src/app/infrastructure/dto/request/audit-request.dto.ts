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
