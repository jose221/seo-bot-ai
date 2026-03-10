// ============ LIST ITEM DTO ============
export interface AuditUrlValidationItemResponseDto {
  id: string;
  source_type: string;
  source_id: string;
  name_validation: string;
  description_validation: string;
  status: string;
  global_severity: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  error_message: string | null;
  report_pdf_path: string | null;
  report_word_path: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface AuditUrlValidationListResponseDto {
  items: AuditUrlValidationItemResponseDto[];
  total: number;
  page: number;
  page_size: number | null;
}

export interface CreateAuditUrlValidationResponseDto {
  id: string;
  source_type: string;
  source_id: string;
  name_validation: string;
  description_validation: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

// ============ DETAIL / FIND DTO ============
export interface FindAuditUrlValidationResponseDto {
  id: string;
  user_id: string;
  source_type: string;
  source_id: string;
  name_validation: string;
  description_validation: string;
  ai_instruction: string;
  status: string;
  global_severity: string | null;
  results_json: any | null;
  input_tokens: number | null;
  output_tokens: number | null;
  error_message: string | null;
  report_pdf_path: string | null;
  report_word_path: string | null;
  created_at: string;
  completed_at: string | null;
}

// ============ SCHEMAS DTO ============
export interface AuditUrlValidationSchemaItemDto {
  url: string;
  schema_types_found: string[] | null;
  extracted_schemas: any[] | null;
  validation_errors: any | null;
  severity: string | null;
  ai_report: string | null;
  error: string | null;
  comparison_table: any | null;
}

export interface AuditUrlValidationSchemasResponseDto {
  validation_id: string;
  name_validation: string;
  status: string;
  global_severity: string | null;
  total: number;
  schemas: AuditUrlValidationSchemaItemDto[];
}

