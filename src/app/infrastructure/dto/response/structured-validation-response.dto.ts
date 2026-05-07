import { RichResultsAIResultDto, RichResultsAnalysisFindingDto, RichResultsAnalysisSummaryDto, RichResultsScreenshotDto, RichResultsValidatorDetailDto } from '@/app/infrastructure/dto/response/rich-results-response.dto';

export class StructuredValidationEmbeddedReportDto {
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
    public screenshots: RichResultsScreenshotDto[],
    public findings: RichResultsAnalysisFindingDto[],
    public findings_summary: RichResultsAnalysisSummaryDto,
    public google_validation: RichResultsValidatorDetailDto,
    public schema_org_validation: RichResultsValidatorDetailDto,
    public get_ai_result: RichResultsAIResultDto | null,
    public ai_error_message: string | null,
  ) {}
}

export class StructuredValidationTaskItemDto {
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
    public report: StructuredValidationEmbeddedReportDto,
  ) {}
}

export class StructuredValidationTaskResponseDto {
  constructor(
    public id: string,
    public input_mode: 'url' | 'html',
    public name: string,
    public description: string | null,
    public ai_instruction: string | null,
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
    public items: StructuredValidationTaskItemDto[],
  ) {}
}

export class StructuredValidationTaskListItemDto {
  constructor(
    public id: string,
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

export class StructuredValidationTaskListResponseDto {
  constructor(
    public items: StructuredValidationTaskListItemDto[],
    public total: number,
    public page: number,
    public page_size: number,
  ) {}
}

export class StructuredValidationTaskCreateResponseDto {
  constructor(
    public task_id: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public total_items: number,
    public message: string,
  ) {}
}

export class StructuredValidationRerunResponseDto {
  constructor(
    public task_id: string,
    public status: string,
    public progress_percentage: number,
    public progress_message: string | null,
    public message: string,
  ) {}
}
