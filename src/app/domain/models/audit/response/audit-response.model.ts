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

