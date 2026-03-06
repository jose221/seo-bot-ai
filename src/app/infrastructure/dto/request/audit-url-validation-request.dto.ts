export interface CreateAuditUrlValidationRequestDto {
  name_validation: string;
  description_validation: string;
  ai_instruction: string;
  source_id: string;
  source_type: string;
  urls: string;
}

export interface FilterAuditUrlValidationRequestDto {
  page?: number;
  page_size?: number;
}

