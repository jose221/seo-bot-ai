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
    public created_at: string,
    public completed_at: string | null
  ) {}
}

