export class CreateRichResultsReportRequestModel {
  constructor(
    public content: string,
    public is_url: boolean = true,
    public get_ai_result: boolean = true,
    public auto_extract_html: boolean = false,
    public validate_google: boolean = true,
    public validate_schema_org: boolean = true,
  ) {}
}

export class CreateRichResultsBatchReportRequestModel {
  constructor(
    public urls: string[],
    public get_ai_result: boolean = true,
    public auto_extract_html: boolean = false,
    public validate_google: boolean = true,
    public validate_schema_org: boolean = true,
  ) {}
}

export class GetRichResultsStatusesRequestModel {
  constructor(public urls: string[]) {}
}

export class FilterRichResultsReportsRequestModel {
  constructor(
    public url?: string,
    public distinct?: boolean,
    public page?: number,
    public page_size?: number,
  ) {}
}
