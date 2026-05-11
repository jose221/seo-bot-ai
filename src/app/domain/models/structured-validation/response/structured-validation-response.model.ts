import {
  RichResultsAIResultModel,
  RichResultsAnalysisFindingModel,
  RichResultsAnalysisSummaryModel,
  RichResultsScreenshotModel,
  RichResultsValidatorDetailModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';

export class StructuredValidationEmbeddedReportModel {
  constructor(
    public success: boolean,
    public input_type: string,
    public method_used: string,
    public result_url: string | null,
    public message: string,
    public error_message: string | null,
    public blocked_by_google: boolean,
    public validate_google: boolean,
    public validate_schema_org: boolean,
    public screenshots: RichResultsScreenshotModel[],
    public findings: RichResultsAnalysisFindingModel[],
    public findings_summary: RichResultsAnalysisSummaryModel,
    public google_validation: RichResultsValidatorDetailModel,
    public schema_org_validation: RichResultsValidatorDetailModel,
    public get_ai_result: RichResultsAIResultModel | null,
    public ai_error_message: string | null,
  ) {}
}

export class StructuredValidationTaskItemModel {
  constructor(
    public item_key: string,
    public input_type: 'url' | 'html',
    public label: string,
    public source_preview: string | null,
    public source_value: string | null,
    public success: boolean,
    public severity: string | null,
    public message: string | null,
    public error_message: string | null,
    public report: StructuredValidationEmbeddedReportModel,
  ) {}
}

export class StructuredValidationTaskSummaryModel {
  constructor(
    public total: number,
    public ok: number,
    public warning: number,
    public critical: number,
    public error: number,
    public pending: number,
  ) {}
}

export class StructuredValidationBrowserModeOptionModel {
  constructor(
    public code: string,
    public name: string,
    public description: string,
    public available_web: boolean,
  ) {}
}

export class StructuredValidationTaskResponseModel {
  constructor(
    public id: string,
    public task_kind: string,
    public supports_runtime_control: boolean,
    public input_mode: 'url' | 'html',
    public name: string,
    public description: string | null,
    public ai_instruction: string | null,
    public browser_mode_code: string | null,
    public requested_ai_result: boolean,
    public auto_extract_html: boolean,
    public validate_google: boolean,
    public validate_schema_org: boolean,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public total_items: number,
    public completed_items: number,
    public successful_items: number,
    public failed_items: number,
    public success: boolean,
    public message: string,
    public error_message: string | null,
    public created_at: string,
    public updated_at: string,
    public completed_at: string | null,
    public page: number,
    public page_size: number,
    public summary: StructuredValidationTaskSummaryModel,
    public items: StructuredValidationTaskItemModel[],
  ) {}
}

export class StructuredValidationTaskListItemModel {
  constructor(
    public id: string,
    public task_kind: string,
    public supports_runtime_control: boolean,
    public input_mode: 'url' | 'html',
    public name: string,
    public description: string | null,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public total_items: number,
    public completed_items: number,
    public successful_items: number,
    public failed_items: number,
    public validate_google: boolean,
    public validate_schema_org: boolean,
    public requested_ai_result: boolean,
    public created_at: string,
    public completed_at: string | null,
  ) {}
}

export class StructuredValidationTaskListResponseModel {
  constructor(
    public items: StructuredValidationTaskListItemModel[],
    public total: number,
    public page: number,
    public page_size: number,
  ) {}
}

export class StructuredValidationTaskCreateResponseModel {
  constructor(
    public task_id: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public total_items: number,
    public message: string,
  ) {}
}

export class StructuredValidationRerunResponseModel {
  constructor(
    public task_id: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public message: string,
  ) {}
}

export type StructuredValidationTaskControlAction = 'pause' | 'resume' | 'cancel' | 'restart';
