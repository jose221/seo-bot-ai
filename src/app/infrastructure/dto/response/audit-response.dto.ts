import {StatusType} from '@/app/domain/types/status.type';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';

export interface AuditResponseDto {
  id: string
  web_page_id: string
  user_id: string
  status: StatusType
  performance_score: number
  seo_score: number
  accessibility_score: number
  best_practices_score: number
  lcp: number
  fid: number
  cls: number
  lighthouse_data?: object|any
  ai_suggestions?: object|any
  web_page?: TargetResponseModel
  error_message: string
  created_at: string
  completed_at: string
}
export interface CreateAuditResponseDto {
  message: string
  status: StatusType
  task_id: string
}
