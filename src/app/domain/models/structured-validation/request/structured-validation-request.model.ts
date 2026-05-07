export class StructuredValidationCreateRequestModel {
  constructor(
    public input_mode: 'url' | 'html',
    public name: string,
    public description: string | null = null,
    public ai_instruction: string | null = null,
    public raw_urls: string | null = null,
    public html_items: string[] = [],
    public get_ai_result: boolean = true,
    public auto_extract_html: boolean = false,
    public validate_google: boolean = true,
    public validate_schema_org: boolean = true,
  ) {}
}

export class FilterStructuredValidationTasksRequestModel {
  constructor(
    public page: number = 1,
    public page_size: number = 20,
  ) {}
}
