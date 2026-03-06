// ============ REQUEST MODELS ============
export class CreateAuditUrlValidationRequestModel {
  constructor(
    public name_validation: string,
    public description_validation: string,
    public ai_instruction: string,
    public source_id: string,
    public source_type: string,
    public urls: string
  ) {}
}

export class FilterAuditUrlValidationRequestModel {
  constructor(
    public page?: number,
    public page_size?: number
  ) {}
}

