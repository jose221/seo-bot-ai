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

export class CompareAuditResponseModel {
  constructor(
    public ai_schema_comparison: string,
    public base_url: string,
    public comparisons: ComparisonsAuditResponseModel[],
    public overall_summary: OverallSummaryAuditResponseModel
  ) {}
}

export class OverallSummaryAuditResponseModel {
  constructor(
    public best_in_performance: string,
    public best_in_seo: string,
    public areas_to_improve: string[]
  ){}
}

export class RecommendationsAuditResponseModel {
  constructor(
    public category: string,
    public priority: string,
    public title: string
){}
}
export class SummaryAuditResponseModel {
  constructor(
    public overall_winner: string
  ){}
}

export class ComparisonsAuditResponseModel {
  constructor(
    public compare_url: string,
    public recommendations: RecommendationsAuditResponseModel[],
    public summary: SummaryAuditResponseModel
  ){}
}
