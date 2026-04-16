// ============ LIST ITEM MODEL ============
export class AuditUrlValidationItemResponseModel {
  constructor(
    public id: string,
    public source_type: string,
    public source_id: string,
    public name_validation: string,
    public description_validation: string,
    public status: string,
    public global_severity: string | null,
    public input_tokens: number | null,
    public output_tokens: number | null,
    public error_message: string | null,
    public report_pdf_path: string | null,
    public report_word_path: string | null,
    public global_report_pdf_path: string | null,
    public global_report_word_path: string | null,
    public created_at: string,
    public completed_at: string | null
  ) {}
}

export class AuditUrlValidationListResponseModel {
  constructor(
    public items: AuditUrlValidationItemResponseModel[],
    public total: number,
    public page: number,
    public page_size: number | null
  ) {}
}

export class CreateAuditUrlValidationResponseModel {
  constructor(
    public id: string,
    public source_type: string,
    public source_id: string,
    public name_validation: string,
    public description_validation: string,
    public status: string,
    public created_at: string,
    public completed_at: string | null,
    public error_message: string | null
  ) {}
}

// ============ DETAIL / FIND MODEL ============
export class FindAuditUrlValidationResponseModel {
  constructor(
    public id: string,
    public user_id: string,
    public source_type: string,
    public source_id: string,
    public name_validation: string,
    public description_validation: string,
    public ai_instruction: string,
    public status: string,
    public global_severity: string | null,
    public results_json: any | null,
    public input_tokens: number | null,
    public output_tokens: number | null,
    public error_message: string | null,
    public report_pdf_path: string | null,
    public report_word_path: string | null,
    public global_report_pdf_path: string | null,
    public global_report_word_path: string | null,
    public global_report_ai_text: string | null,
    public created_at: string,
    public completed_at: string | null
  ) {}
}

// ============ PUBLIC COMMENTS MODELS ============
export class PublicCommentItemModel {
  constructor(
    public id: string,
    public schema_item_url: string,
    public validation_id: string,
    public username: string,
    public comment: string,
    public status: string,
    public answer: string | null,
    public answered_at: string | null,
    public created_at: string
  ) {}
}

export class PublicCommentsResponseModel {
  constructor(
    public validation_id: string,
    public items: PublicCommentItemModel[],
    public total: number,
    public page: number,
    public page_size: number
  ) {}
}

export class CreatePublicCommentResponseModel {
  constructor(
    public id: string,
    public schema_item_url: string,
    public validation_id: string,
    public username: string,
    public comment: string,
    public status: string,
    public answer: string | null,
    public answered_at: string | null,
    public created_at: string
  ) {}
}

// ============ SCHEMAS MODEL ============
export class AuditUrlValidationSchemaItemModel {
  constructor(
    public url: string,
    public schema_types_found: string[] | null,
    public extracted_schemas: any[] | null,
    public validation_errors: any | null,
    public severity: string | null,
    public ai_report: string | null,
    public error: string | null,
    public comparison_table: any | null
  ) {}
}

export class AuditUrlValidationSchemasResponseModel {
  constructor(
    public validation_id: string,
    public name_validation: string,
    public status: string,
    public global_severity: string | null,
    public total: number,
    public schemas: AuditUrlValidationSchemaItemModel[]
  ) {}
}

