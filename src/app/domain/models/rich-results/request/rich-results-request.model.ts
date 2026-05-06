export class CreateRichResultsReportRequestModel {
  constructor(
    public content: string,
    public is_url: boolean = true,
    public get_ai_result: boolean = true,
  ) {}
}

export class FilterRichResultsReportsRequestModel {
  constructor(
    public url?: string,
    public distinct?: boolean,
    public page?: number,
    public page_size?: number,
  ) {}
}
