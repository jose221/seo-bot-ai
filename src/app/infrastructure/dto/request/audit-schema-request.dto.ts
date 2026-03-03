export interface CreateAuditSchemaRequestDto {
  source_type: string;
  source_id: string;
  modified_schema_json: string;
  include_ai_analysis: boolean;
  programming_language: string;
}

export interface FilterAuditSchemaRequestDto {
  page?: number;
  page_size?: number;
}

