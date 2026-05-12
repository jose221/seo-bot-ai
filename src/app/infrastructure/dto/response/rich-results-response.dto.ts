export class RichResultsReportTaskResponseDto {
  constructor(
    public task_id: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public url: string,
    public message: string,
  ) {}
}

export class RichResultsReportBatchResponseDto {
  constructor(
    public total: number,
    public created_count: number,
    public items: RichResultsReportTaskResponseDto[],
    public message: string,
  ) {}
}

export class RichResultsReportStatusSummaryItemDto {
  constructor(
    public url: string,
    public state: string,
    public report_id: string | null,
    public report_status: string | null,
    public progress_percentage: number,
    public progress_message: string | null,
    public success: boolean | null,
    public blocked_by_google: boolean | null,
    public validate_google: boolean,
    public validate_schema_org: boolean,
    public has_error: boolean,
    public message: string | null,
    public error_message: string | null,
    public findings_summary: RichResultsAnalysisSummaryDto,
    public google_validation: RichResultsValidatorDetailDto,
    public schema_org_validation: RichResultsValidatorDetailDto,
    public created_at: string | null,
  ) {}
}

export class RichResultsReportStatusSummaryResponseDto {
  constructor(public items: RichResultsReportStatusSummaryItemDto[]) {}
}

export class RichResultsReportListItemDto {
  constructor(
    public id: string,
    public url: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public input_type: string,
    public requested_ai_result: boolean,
    public validate_google: boolean,
    public validate_schema_org: boolean,
    public success: boolean,
    public method_used: string,
    public result_url: string | null,
    public message: string,
    public error_message: string | null,
    public blocked_by_google: boolean,
    public findings_summary: RichResultsAnalysisSummaryDto,
    public google_validation: RichResultsValidatorDetailDto,
    public schema_org_validation: RichResultsValidatorDetailDto,
    public created_at: string,
  ) {}
}

export class RichResultsReportListResponseDto {
  constructor(
    public items: RichResultsReportListItemDto[],
    public total: number,
    public page: number,
    public page_size: number | null,
  ) {}
}

export class RichResultsScreenshotDto {
  constructor(
    public path: string,
    public url: string,
  ) {}
}

export class RichResultsAIResultDto {
  constructor(
    public content: string,
    public usage: Record<string, any> | null,
    public model: string | null,
    public generated_at: string | null,
  ) {}
}

export class RichResultsAnalysisFindingDto {
  constructor(
    public key: string,
    public code: string,
    public severity: string,
    public category: string,
    public selector: string,
    public message: string,
    public document_url: string | null,
    public document_label: string | null,
    public element_url: string | null,
    public item_name: string | null,
    public color: string | null,
  ) {}
}

export class RichResultsAnalysisSummaryDto {
  constructor(
    public total: number = 0,
    public by_severity: Record<string, number> = {},
    public by_category: Record<string, number> = {},
  ) {}
}

export class RichResultsValidatorDetailDto {
  constructor(
    public validator: string,
    public label: string,
    public enabled: boolean,
    public executed: boolean,
    public proxy_used: boolean,
    public success: boolean | null,
    public method_used: string | null,
    public result_url: string | null,
    public message: string | null,
    public error_message: string | null,
    public blocked: boolean,
    public screenshots: RichResultsScreenshotDto[],
    public findings: RichResultsAnalysisFindingDto[],
    public findings_summary: RichResultsAnalysisSummaryDto,
    public html_content: string | null,
    public markdown_content: string | null,
  ) {}
}

export class RichResultsReportDetailResponseDto {
  constructor(
    public id: string,
    public url: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public input_type: string,
    public requested_ai_result: boolean,
    public validate_google: boolean,
    public validate_schema_org: boolean,
    public success: boolean,
    public method_used: string,
    public result_url: string | null,
    public message: string,
    public error_message: string | null,
    public blocked_by_google: boolean,
    public screenshots: RichResultsScreenshotDto[],
    public findings: RichResultsAnalysisFindingDto[],
    public findings_summary: RichResultsAnalysisSummaryDto,
    public google_validation: RichResultsValidatorDetailDto,
    public schema_org_validation: RichResultsValidatorDetailDto,
    public get_ai_result: RichResultsAIResultDto | null,
    public ai_error_message: string | null,
    public created_at: string,
  ) {}
}
