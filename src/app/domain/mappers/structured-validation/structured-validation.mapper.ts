import { AppMapper } from '../app.mapper';
import {
  CreatePublicCommentRequestModel,
  AnswerCommentRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import {
  CreatePublicCommentResponseModel,
  PublicCommentItemModel,
  PublicCommentsResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  FilterStructuredValidationTasksRequestModel,
  StructuredValidationTaskDetailRequestModel,
  StructuredValidationCreateRequestModel,
} from '@/app/domain/models/structured-validation/request/structured-validation-request.model';
import {
  StructuredValidationBrowserModeOptionModel,
  StructuredValidationEmbeddedReportModel,
  StructuredValidationRerunResponseModel,
  StructuredValidationTaskCreateResponseModel,
  StructuredValidationTaskItemModel,
  StructuredValidationTaskListItemModel,
  StructuredValidationTaskListResponseModel,
  StructuredValidationTaskResponseModel,
  StructuredValidationTaskSummaryModel,
} from '@/app/domain/models/structured-validation/response/structured-validation-response.model';
import {
  FilterStructuredValidationTasksRequestDto,
  StructuredValidationTaskDetailRequestDto,
  StructuredValidationCreateRequestDto,
} from '@/app/infrastructure/dto/request/structured-validation-request.dto';
import {
  StructuredValidationBrowserModeOptionDto,
  StructuredValidationEmbeddedReportDto,
  StructuredValidationRerunResponseDto,
  StructuredValidationTaskCreateResponseDto,
  StructuredValidationTaskItemDto,
  StructuredValidationTaskListItemDto,
  StructuredValidationTaskListResponseDto,
  StructuredValidationTaskResponseDto,
  StructuredValidationTaskSummaryDto,
} from '@/app/infrastructure/dto/response/structured-validation-response.dto';
import {
  CreatePublicCommentRequestDto,
  AnswerCommentRequestDto,
} from '@/app/infrastructure/dto/request/audit-url-validation-request.dto';
import {
  CreatePublicCommentResponseDto,
  PublicCommentsResponseDto,
} from '@/app/infrastructure/dto/response/audit-url-validation-response.dto';
import {
  RichResultsAIResultModel,
  RichResultsAnalysisFindingModel,
  RichResultsAnalysisSummaryModel,
  RichResultsScreenshotModel,
  RichResultsValidatorDetailModel,
} from '@/app/domain/models/rich-results/response/rich-results-response.model';
import {
  RichResultsAIResultDto,
  RichResultsAnalysisFindingDto,
  RichResultsAnalysisSummaryDto,
  RichResultsScreenshotDto,
  RichResultsValidatorDetailDto,
} from '@/app/infrastructure/dto/response/rich-results-response.dto';

export class StructuredValidationMapper extends AppMapper {
  mapCreate(model: StructuredValidationCreateRequestModel): StructuredValidationCreateRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapFilter(model: FilterStructuredValidationTasksRequestModel): FilterStructuredValidationTasksRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapDetailFilter(model: StructuredValidationTaskDetailRequestModel): StructuredValidationTaskDetailRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapPublicComment(model: CreatePublicCommentRequestModel): CreatePublicCommentRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapAnswerComment(model: AnswerCommentRequestModel): AnswerCommentRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  private mapScreenshot(dto: RichResultsScreenshotDto): RichResultsScreenshotModel {
    return new RichResultsScreenshotModel(dto.path, dto.url);
  }

  private mapFinding(dto: RichResultsAnalysisFindingDto): RichResultsAnalysisFindingModel {
    return new RichResultsAnalysisFindingModel(
      dto.key,
      dto.code,
      dto.severity,
      dto.category,
      dto.selector,
      dto.message,
      dto.document_url,
      dto.document_label,
      dto.element_url,
      dto.item_name,
      dto.color,
    );
  }

  private mapSummary(dto: RichResultsAnalysisSummaryDto): RichResultsAnalysisSummaryModel {
    return new RichResultsAnalysisSummaryModel(dto.total, dto.by_severity ?? {}, dto.by_category ?? {});
  }

  private mapAI(dto: RichResultsAIResultDto | null): RichResultsAIResultModel | null {
    if (!dto) return null;
    return new RichResultsAIResultModel(dto.content, dto.usage ?? null, dto.model ?? null, dto.generated_at ?? null);
  }

  private mapValidator(dto: RichResultsValidatorDetailDto): RichResultsValidatorDetailModel {
    return new RichResultsValidatorDetailModel(
      dto.validator,
      dto.label,
      dto.enabled,
      dto.executed,
      dto.success ?? null,
      dto.method_used ?? null,
      dto.result_url ?? null,
      dto.message ?? null,
      dto.error_message ?? null,
      dto.blocked,
      (dto.screenshots ?? []).map((item) => this.mapScreenshot(item)),
      (dto.findings ?? []).map((item) => this.mapFinding(item)),
      this.mapSummary(dto.findings_summary),
      dto.html_content ?? null,
      dto.markdown_content ?? null,
    );
  }

  private mapEmbeddedReport(dto: StructuredValidationEmbeddedReportDto): StructuredValidationEmbeddedReportModel {
    return new StructuredValidationEmbeddedReportModel(
      dto.success,
      dto.input_type,
      dto.method_used,
      dto.result_url,
      dto.message,
      dto.error_message,
      dto.blocked_by_google,
      dto.validate_google,
      dto.validate_schema_org,
      (dto.screenshots ?? []).map((item) => this.mapScreenshot(item)),
      (dto.findings ?? []).map((item) => this.mapFinding(item)),
      this.mapSummary(dto.findings_summary),
      this.mapValidator(dto.google_validation),
      this.mapValidator(dto.schema_org_validation),
      this.mapAI(dto.get_ai_result),
      dto.ai_error_message,
    );
  }

  private mapItem(dto: StructuredValidationTaskItemDto): StructuredValidationTaskItemModel {
    return new StructuredValidationTaskItemModel(
      dto.item_key,
      dto.input_type,
      dto.label,
      dto.source_preview,
      dto.source_value,
      dto.success,
      dto.severity,
      dto.message,
      dto.error_message,
      this.mapEmbeddedReport(dto.report),
    );
  }

  private mapTaskSummary(dto: StructuredValidationTaskSummaryDto): StructuredValidationTaskSummaryModel {
    return new StructuredValidationTaskSummaryModel(
      dto.total ?? 0,
      dto.ok ?? 0,
      dto.warning ?? 0,
      dto.critical ?? 0,
      dto.error ?? 0,
      dto.pending ?? 0,
    );
  }

  mapBrowserModes(dtos: StructuredValidationBrowserModeOptionDto[]): StructuredValidationBrowserModeOptionModel[] {
    return (dtos ?? []).map(
      (dto) => new StructuredValidationBrowserModeOptionModel(
        dto.code,
        dto.name,
        dto.description,
        dto.available_web,
      ),
    );
  }

  mapResponseTaskCreate(dto: StructuredValidationTaskCreateResponseDto): StructuredValidationTaskCreateResponseModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }

  mapResponseTask(dto: StructuredValidationTaskResponseDto): StructuredValidationTaskResponseModel {
    return new StructuredValidationTaskResponseModel(
      dto.id,
      dto.task_kind,
      dto.supports_runtime_control,
      dto.input_mode,
      dto.name,
      dto.description,
      dto.ai_instruction,
      dto.browser_mode_code,
      dto.requested_ai_result,
      dto.auto_extract_html,
      dto.validate_google,
      dto.validate_schema_org,
      dto.status,
      dto.progress_percentage,
      dto.progress_message,
      dto.total_items,
      dto.completed_items,
      dto.successful_items,
      dto.failed_items,
      dto.success,
      dto.message,
      dto.error_message,
      dto.created_at,
      dto.updated_at,
      dto.completed_at,
      dto.page,
      dto.page_size,
      this.mapTaskSummary(dto.summary),
      (dto.items ?? []).map((item) => this.mapItem(item)),
    );
  }

  mapResponseList(dto: StructuredValidationTaskListResponseDto): StructuredValidationTaskListResponseModel {
    return new StructuredValidationTaskListResponseModel(
      (dto.items ?? []).map(
        (item: StructuredValidationTaskListItemDto) =>
          new StructuredValidationTaskListItemModel(
            item.id,
            item.task_kind,
            item.supports_runtime_control,
            item.input_mode,
            item.name,
            item.description,
            item.status,
            item.progress_percentage,
            item.progress_message,
            item.total_items,
            item.completed_items,
            item.successful_items,
            item.failed_items,
            item.validate_google,
            item.validate_schema_org,
            item.requested_ai_result,
            item.created_at,
            item.completed_at,
          ),
      ),
      dto.total,
      dto.page,
      dto.page_size,
    );
  }

  mapResponseRerun(dto: StructuredValidationRerunResponseDto): StructuredValidationRerunResponseModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }

  mapResponsePublicComments(dto: PublicCommentsResponseDto): PublicCommentsResponseModel {
    return new PublicCommentsResponseModel(
      dto.validation_id,
      dto.items.map((c) => new PublicCommentItemModel(
        c.id,
        c.schema_item_url,
        c.validation_id,
        c.username,
        c.comment,
        c.status,
        c.answer,
        c.answered_at,
        c.created_at,
      )),
      dto.total,
      dto.page,
      dto.page_size,
    );
  }

  mapResponseCreatePublicComment(dto: CreatePublicCommentResponseDto): CreatePublicCommentResponseModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }
}
