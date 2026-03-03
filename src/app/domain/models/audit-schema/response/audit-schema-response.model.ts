// ============ LIST ITEM MODEL ============
export class AuditSchemaItemResponseModel {
  constructor(
    public id: string,
    public source_type: string,
    public source_id: string,
    public status: string,
    public programming_language: string,
    public created_at: string,
    public completed_at: string | null,
    public error_message: string | null,
    public report_pdf_path: string | null,
    public report_word_path: string | null
  ) {}
}

export class AuditSchemaListResponseModel {
  constructor(
    public items: AuditSchemaItemResponseModel[],
    public total: number,
    public page: number,
    public page_size: number | null
  ) {}
}

export class CreateAuditSchemaResponseModel {
  constructor(
    public id: string,
    public source_type: string,
    public source_id: string,
    public status: string,
    public programming_language: string,
    public created_at: string,
    public completed_at: string | null,
    public error_message: string | null,
    public report_pdf_path: string | null,
    public report_word_path: string | null
  ) {}
}

// ============ DETAIL / FIND MODEL ============
export class FindAuditSchemaResponseModel {
  constructor(
    public id: string,
    public user_id: string,
    public source_type: string,
    public source_id: string,
    public status: string,
    public programming_language: string,
    public created_at: string,
    public completed_at: string | null,
    public error_message: string | null,
    public report_pdf_path: string | null,
    public report_word_path: string | null,
    public original_schema_json: any[],
    public proposed_schema_json: any,
    public incoming_schema_json: string,
    public schema_org_validation_result: SchemaOrgValidationResultModel | null,
    public triple_comparison_result: TripleComparisonResultModel | null,
    public progress_report: ProgressReportModel | null,
    public ai_report: string | null,
    public cqrs_solid_model_text: string | null,
    public include_ai_analysis: boolean,
    public input_tokens: number | null,
    public output_tokens: number | null
  ) {}
}

export class SchemaOrgValidationResultModel {
  constructor(
    public original: SchemaValidationDetailModel,
    public proposed: SchemaValidationDetailModel,
    public incoming: SchemaValidationDetailModel
  ) {}
}

export class SchemaValidationDetailModel {
  constructor(
    public label: string,
    public is_valid: boolean,
    public errors: string[],
    public warnings: string[],
    public items_count: number
  ) {}
}

export class TripleComparisonResultModel {
  constructor(
    public types: TripleTypesModel,
    public delta: TripleDeltaModel,
    public original_integrity: OriginalIntegrityModel
  ) {}
}

export class TripleTypesModel {
  constructor(
    public original: string[],
    public proposed: string[],
    public incoming: string[]
  ) {}
}

export class TripleDeltaModel {
  constructor(
    public implemented_from_proposed: string[],
    public pending_from_proposed: string[],
    public new_not_in_proposed: string[],
    public kept_from_original: string[]
  ) {}
}

export class OriginalIntegrityModel {
  constructor(
    public is_preserved: boolean,
    public missing_original_types: string[],
    public changed_fields: ChangedFieldModel[]
  ) {}
}

export class ChangedFieldModel {
  constructor(
    public type: string,
    public field: string,
    public original: any,
    public incoming: any
  ) {}
}

export class ProgressReportModel {
  constructor(
    public implemented: string[],
    public pending: string[],
    public out_of_scope: string[],
    public original_integrity: OriginalIntegrityModel
  ) {}
}

