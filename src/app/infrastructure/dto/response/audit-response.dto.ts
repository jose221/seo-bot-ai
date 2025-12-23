import {StatusType} from '@/app/domain/types/status.type';
import {TargetResponseDto} from '@/app/infrastructure/dto/response/target-response.dto';

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
  web_page?: TargetResponseDto
  error_message: string
  created_at: string
  completed_at: string
}
export interface CreateAuditResponseDto {
  message: string
  status: StatusType
  task_id: string
}


export interface CompareAuditResponseDto {
  ai_schema_comparison: string
  base_url: string
  comparisons: ComparisonsAuditResponseDto[]
  overall_summary: OverallSummaryAuditResponseDto
}

export interface OverallSummaryAuditResponseDto {
  best_in_performance: string
  best_in_seo: string
  areas_to_improve: string[]
}

export interface RecommendationsAuditResponseDto {
  category: string
  priority: string
  title: string
}
export interface SummaryAuditResponseDto {
  overall_winner: string
}

export interface ComparisonsAuditResponseDto {
  compare_url: string
  recommendations: RecommendationsAuditResponseDto[]
  summary: SummaryAuditResponseDto
}

export interface SearchAuditResponseDto{
  id: string
  web_page_id: string
  status: StatusType
  performance_score: number
  seo_score: number
  accessibility_score: number
  best_practices_score: number
  created_at: string
  completed_at: string
  web_page_url: string
  web_page_name: string
}
