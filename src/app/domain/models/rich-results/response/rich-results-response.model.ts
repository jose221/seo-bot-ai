export class RichResultsReportTaskResponseModel {
  constructor(
    public task_id: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public url: string,
    public message: string,
  ) {}
}

export class RichResultsReportBatchResponseModel {
  constructor(
    public total: number,
    public created_count: number,
    public items: RichResultsReportTaskResponseModel[],
    public message: string,
  ) {}
}

export class RichResultsReportStatusSummaryItemModel {
  constructor(
    public url: string,
    public state: string,
    public report_id: string | null,
    public report_status: string | null,
    public progress_percentage: number,
    public progress_message: string | null,
    public success: boolean | null,
    public blocked_by_google: boolean | null,
    public has_error: boolean,
    public message: string | null,
    public error_message: string | null,
    public findings_summary: RichResultsAnalysisSummaryModel,
    public created_at: string | null,
  ) {}
}

export class RichResultsReportStatusSummaryResponseModel {
  constructor(public items: RichResultsReportStatusSummaryItemModel[]) {}
}

export class RichResultsReportListItemModel {
  constructor(
    public id: string,
    public url: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public input_type: string,
    public requested_ai_result: boolean,
    public success: boolean,
    public method_used: string,
    public result_url: string | null,
    public message: string,
    public error_message: string | null,
    public blocked_by_google: boolean,
    public findings_summary: RichResultsAnalysisSummaryModel,
    public created_at: string,
  ) {}
}

export class RichResultsReportListResponseModel {
  constructor(
    public items: RichResultsReportListItemModel[],
    public total: number,
    public page: number,
    public page_size: number | null,
  ) {}
}

export class RichResultsScreenshotModel {
  constructor(
    public path: string,
    public url: string,
  ) {}
}

export class RichResultsAIResultModel {
  constructor(
    public content: string,
    public usage: Record<string, any> | null,
    public model: string | null,
    public generated_at: string | null,
  ) {}
}

export class RichResultsAnalysisFindingModel {
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

export class RichResultsAnalysisSummaryModel {
  constructor(
    public total: number = 0,
    public by_severity: Record<string, number> = {},
    public by_category: Record<string, number> = {},
  ) {}
}

export class RichResultsReportDetailResponseModel {
  constructor(
    public id: string,
    public url: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public input_type: string,
    public requested_ai_result: boolean,
    public success: boolean,
    public method_used: string,
    public result_url: string | null,
    public message: string,
    public error_message: string | null,
    public blocked_by_google: boolean,
    public screenshots: RichResultsScreenshotModel[],
    public findings: RichResultsAnalysisFindingModel[],
    public findings_summary: RichResultsAnalysisSummaryModel,
    public get_ai_result: RichResultsAIResultModel | null,
    public ai_error_message: string | null,
    public created_at: string,
  ) {}
}
