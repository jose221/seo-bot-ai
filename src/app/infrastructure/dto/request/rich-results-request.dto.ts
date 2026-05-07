export class CreateRichResultsReportRequestDto {
  constructor(
    public content: string,
    public is_url: boolean,
    public get_ai_result: boolean,
    public auto_extract_html: boolean,
    public validate_google: boolean,
    public validate_schema_org: boolean,
  ) {}
}

export class CreateRichResultsBatchReportRequestDto {
  constructor(
    public urls: string[],
    public get_ai_result: boolean,
    public auto_extract_html: boolean,
    public validate_google: boolean,
    public validate_schema_org: boolean,
  ) {}
}

export class GetRichResultsStatusesRequestDto {
  constructor(public urls: string[]) {}
}

export class FilterRichResultsReportsRequestDto {
  constructor(
    public url?: string,
    public distinct?: boolean,
    public page?: number,
    public page_size?: number,
  ) {}
}
