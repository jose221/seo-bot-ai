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
// ============ COMPARE AUDIT MODELS ============

export interface CreateCompareAuditResponseDto {
  message: string
  status: string
  task_id: string

}

export interface CompareAuditResponseDto{
  id: string
  base_web_page_id: string
  status: string
  created_at: string
  completed_at: string
  base_url: string
  total_competitors: number
  error_message: string
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

// ============ FIND COMPARE AUDIT DTOs ============
export interface FindCompareAuditResponseDto {
  id: string
  base_web_page_id: string
  status: string
  created_at: string
  completed_at: string
  comparison_result: ComparisonResultDto
  error_message: string | null
}

export interface ComparisonResultDto {
  base_url: string
  comparisons: ComparisonsAuditResponseDto[]
  overall_summary: OverallSummaryAuditResponseDto
  ai_schema_comparison: string
}

export interface OverallSummaryAuditResponseDto {
  total_competitors: number
  performance_rank: string
  seo_rank: string
  is_best_performance: boolean
  is_best_seo: boolean
  areas_to_improve: string[]
  top_recommendations: TopRecommendationDto[]
  competitive_advantage: CompetitiveAdvantageDto
}

export interface CompetitiveAdvantageDto {
  performance_above_average: boolean
  seo_above_average: boolean
}

export interface TopRecommendationDto {
  category: string
  priority: string
  title: string
  description: string
  missing_schemas?: string[]
  current_value?: number
  target_value?: number
  action?: string
}

export interface ComparisonsAuditResponseDto {
  compare_url: string
  comparison_date: string
  summary: SummaryAuditResponseDto
  performance: PerformanceDto
  schemas: SchemasDto
  seo_analysis: SeoAnalysisDto
  recommendations: RecommendationsAuditResponseDto[]
  ai_analysis: string
}

export interface SummaryAuditResponseDto {
  base_audit_id: string
  compare_audit_id: string
  overall_winner: string
}

export interface PerformanceDto {
  scores: ScoresDto
  core_web_vitals: any
  overall_better: string
}

export interface ScoresDto {
  performance_score?: ScoreItemDto
  seo_score?: ScoreItemDto
  accessibility_score?: ScoreItemDto
  best_practices_score?: ScoreItemDto
}

export interface ScoreItemDto {
  base?: number
  compare?: number
  difference?: number
  percentage_diff?: number
  is_better?: boolean
  status?: string
}

export interface SchemasDto {
  base_schemas: string[]
  compare_schemas: string[]
  missing_in_base: string[]
  common_schemas: string[]
  unique_to_base: string[]
  base_count: number
  compare_count: number
  completeness_score: number
}

export interface SeoAnalysisDto {
  onpage: OnPageDto
  technical: TechnicalDto
}

export interface OnPageDto {
  title_comparison: TitleComparisonDto
  meta_description_comparison: MetaDescriptionComparisonDto
  headers_comparison: HeadersComparisonDto
  links_comparison: LinksComparisonDto
}

export interface TitleComparisonDto {
  base_length: number
  compare_length: number
  base_status: string
  compare_status: string
  recommendation: string
}

export interface MetaDescriptionComparisonDto {
  base_length: number
  compare_length: number
  base_status: string
  compare_status: string
  recommendation: string
}

export interface HeadersComparisonDto {
  base_structure: HeaderStructureDto
  compare_structure: HeaderStructureDto
  base_h1_count: number
  compare_h1_count: number
  base_h1_status: string
  compare_h1_status: string
}

export interface HeaderStructureDto {
  h1: number
  h2: number
  h3: number
  h4?: number
  h5?: number
  h6?: number
}

export interface LinksComparisonDto {
  base_total: number
  compare_total: number
  base_internal: number
  compare_internal: number
  base_external: number
  compare_external: number
}

export interface TechnicalDto {
  robots_txt: RobotsTxtDto
}

export interface RobotsTxtDto {
  base_exists: boolean
  compare_exists: boolean
  base_sitemaps: number
  compare_sitemaps: number
}

export interface RecommendationsAuditResponseDto {
  category: string
  priority: string
  title: string
  description: string
  missing_schemas?: string[]
  current_value?: number
  target_value?: number
  action?: string
}
