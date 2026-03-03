// ============ REQUEST MODELS ============
export class CreateAuditSchemaRequestModel {
  constructor(
    public source_type: string,
    public source_id: string,
    public modified_schema_json: string,
    public include_ai_analysis: boolean,
    public programming_language: string
  ) {}
}

export class FilterAuditSchemaRequestModel {
  constructor(
    public page?: number,
    public page_size?: number
  ) {}
}

