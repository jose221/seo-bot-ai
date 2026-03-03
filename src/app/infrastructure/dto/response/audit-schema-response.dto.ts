// ============ LIST ITEM DTO ============
export interface AuditSchemaItemResponseDto {
  id: string;
  source_type: string;
  source_id: string;
  status: string;
  programming_language: string;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  report_pdf_path: string | null;
  report_word_path: string | null;
}

export interface AuditSchemaListResponseDto {
  items: AuditSchemaItemResponseDto[];
  total: number;
  page: number;
  page_size: number | null;
}

export interface CreateAuditSchemaResponseDto {
  id: string;
  source_type: string;
  source_id: string;
  status: string;
  programming_language: string;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  report_pdf_path: string | null;
  report_word_path: string | null;
}

// ============ DETAIL / FIND DTO ============
export interface FindAuditSchemaResponseDto {
  id: string;
  user_id: string;
  source_type: string;
  source_id: string;
  status: string;
  programming_language: string;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  report_pdf_path: string | null;
  report_word_path: string | null;
  original_schema_json: any[];
  proposed_schema_json: any;
  incoming_schema_json: string;
  schema_org_validation_result: SchemaOrgValidationResultDto | null;
  triple_comparison_result: TripleComparisonResultDto | null;
  progress_report: ProgressReportDto | null;
  ai_report: string | null;
  cqrs_solid_model_text: string | null;
  include_ai_analysis: boolean;
  input_tokens: number | null;
  output_tokens: number | null;
}

export interface SchemaOrgValidationResultDto {
  original: SchemaValidationDetailDto;
  proposed: SchemaValidationDetailDto;
  incoming: SchemaValidationDetailDto;
}

export interface SchemaValidationDetailDto {
  label: string;
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  items_count: number;
}

export interface TripleComparisonResultDto {
  types: TripleTypesDto;
  delta: TripleDeltaDto;
  original_integrity: OriginalIntegrityDto;
}

export interface TripleTypesDto {
  original: string[];
  proposed: string[];
  incoming: string[];
}

export interface TripleDeltaDto {
  implemented_from_proposed: string[];
  pending_from_proposed: string[];
  new_not_in_proposed: string[];
  kept_from_original: string[];
}

export interface OriginalIntegrityDto {
  is_preserved: boolean;
  missing_original_types: string[];
  changed_fields: ChangedFieldDto[];
}

export interface ChangedFieldDto {
  type: string;
  field: string;
  original: any;
  incoming: any;
}

export interface ProgressReportDto {
  implemented: string[];
  pending: string[];
  out_of_scope: string[];
  original_integrity: OriginalIntegrityDto;
}

