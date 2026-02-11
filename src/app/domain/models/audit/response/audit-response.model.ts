import {StatusType} from '@/app/domain/types/status.type';
import {TargetResponseModel} from '@/app/domain/models/target/response/target-response.model';

export class CreateAuditResponseModel {
  constructor(
  public message: string,
  public status: StatusType,
  public task_id: string
  ) {}
}

export class AuditResponseModel {
  constructor(
    public id: string,
    public web_page_id: string,
    public user_id: string,
    public status: StatusType,
    public performance_score: number,
    public seo_score: number,
    public accessibility_score: number,
    public best_practices_score: number,
    public lcp: number,
    public fid: number,
    public cls: number,
    public error_message: string,
    public created_at: string,
    public completed_at: string,
    public lighthouse_data?: object|any,
    public ai_suggestions?: object|any,
    public web_page?: TargetResponseModel
  ) {}
}

// ============ COMPARE AUDIT MODELS ============
export class CreateCompareAuditResponseModel {
  constructor(
    public message: string,
    public status: string,
    public task_id: string
  ) {
  }

}

export class CompareAuditResponseModel{
  constructor(
    public id: string,
    public base_web_page_id: string,
    public status: string,
    public created_at: string,
    public completed_at: string,
    public base_url: string,
    public total_competitors: number,
    public error_message: string
  ) {
  }
}

export class SearchAuditResponseModel{
  constructor(
    public id: string,
    public web_page_id: string,
    public status: StatusType,
    public performance_score: number,
    public seo_score: number,
    public accessibility_score: number,
    public best_practices_score: number,
    public created_at: string,
    public completed_at: string,
    public web_page_url: string,
    public web_page_name: string
  ) {
  }
}



// ============ FIND COMPARE AUDIT MODELS ============
export class FindCompareAuditResponseModel {
  constructor(
    public id: string,
    public base_web_page_id: string,
    public status: string,
    public created_at: string,
    public completed_at: string,
    public comparison_result: ComparisonResultModel,
    public error_message: string | null,
    public report_pdf_path?: string | null,
    public report_excel_path?: string | null
  ) {}
}

export class ComparisonResultModel {
  constructor(
    public base_url: string,
    public comparisons: ComparisonItemModel[],
    public overall_summary: OverallSummaryModel,
    public ai_schema_comparison: string
  ) {}
}

export class OverallSummaryModel {
  constructor(
    public total_competitors: number,
    public performance_rank: string,
    public seo_rank: string,
    public is_best_performance: boolean,
    public is_best_seo: boolean,
    public areas_to_improve: string[],
    public top_recommendations: TopRecommendationModel[],
    public competitive_advantage: CompetitiveAdvantageModel
  ) {}
}

export class CompetitiveAdvantageModel {
  constructor(
    public performance_above_average: boolean,
    public seo_above_average: boolean
  ) {}
}

export class TopRecommendationModel {
  constructor(
    public category: string,
    public priority: string,
    public title: string,
    public description: string,
    public missing_schemas?: string[],
    public current_value?: number,
    public target_value?: number,
    public action?: string
  ) {}
}

export class ComparisonItemModel {
  constructor(
    public compare_url: string,
    public comparison_date: string,
    public summary: SummaryModel,
    public performance: PerformanceModel,
    public schemas: SchemasModel,
    public seo_analysis: SeoAnalysisModel,
    public recommendations: RecommendationModel[],
    public ai_analysis: string
  ) {}
}

export class SummaryModel {
  constructor(
    public base_audit_id: string,
    public compare_audit_id: string,
    public overall_winner: string
  ) {}
}

export class PerformanceModel {
  constructor(
    public scores: ScoresModel,
    public core_web_vitals: any,
    public overall_better: string
  ) {}
}

export class ScoresModel {
  constructor(
    public performance_score?: ScoreItemModel,
    public seo_score?: ScoreItemModel,
    public accessibility_score?: ScoreItemModel,
    public best_practices_score?: ScoreItemModel
  ) {}
}

export class ScoreItemModel {
  constructor(
    public base?: number,
    public compare?: number,
    public difference?: number,
    public percentage_diff?: number,
    public is_better?: boolean,
    public status?: string
  ) {}
}

export class SchemasModel {
  constructor(
    public base_schemas: string[],
    public compare_schemas: string[],
    public missing_in_base: string[],
    public common_schemas: string[],
    public unique_to_base: string[],
    public base_count: number,
    public compare_count: number,
    public completeness_score: number
  ) {}
}

export class SeoAnalysisModel {
  constructor(
    public onpage: OnPageModel,
    public technical: TechnicalModel
  ) {}
}

export class OnPageModel {
  constructor(
    public title_comparison: TitleComparisonModel,
    public meta_description_comparison: MetaDescriptionComparisonModel,
    public headers_comparison: HeadersComparisonModel,
    public links_comparison: LinksComparisonModel
  ) {}
}

export class TitleComparisonModel {
  constructor(
    public base_length: number,
    public compare_length: number,
    public base_status: string,
    public compare_status: string,
    public recommendation: string
  ) {}
}

export class MetaDescriptionComparisonModel {
  constructor(
    public base_length: number,
    public compare_length: number,
    public base_status: string,
    public compare_status: string,
    public recommendation: string
  ) {}
}

export class HeadersComparisonModel {
  constructor(
    public base_structure: HeaderStructureModel,
    public compare_structure: HeaderStructureModel,
    public base_h1_count: number,
    public compare_h1_count: number,
    public base_h1_status: string,
    public compare_h1_status: string
  ) {}
}

export class HeaderStructureModel {
  constructor(
    public h1: number,
    public h2: number,
    public h3: number,
    public h4?: number,
    public h5?: number,
    public h6?: number
  ) {}
}

export class LinksComparisonModel {
  constructor(
    public base_total: number,
    public compare_total: number,
    public base_internal: number,
    public compare_internal: number,
    public base_external: number,
    public compare_external: number
  ) {}
}

export class TechnicalModel {
  constructor(
    public robots_txt: RobotsTxtModel
  ) {}
}

export class RobotsTxtModel {
  constructor(
    public base_exists: boolean,
    public compare_exists: boolean,
    public base_sitemaps: number,
    public compare_sitemaps: number
  ) {}
}

export class RecommendationModel {
  constructor(
    public category: string,
    public priority: string,
    public title: string,
    public description: string,
    public missing_schemas?: string[],
    public current_value?: number,
    public target_value?: number,
    public action?: string
  ) {}
}
