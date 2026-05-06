export class CreateRichResultsReportRequestDto {
  constructor(
    public content: string,
    public is_url: boolean,
    public get_ai_result: boolean,
  ) {}
}

export class FilterRichResultsReportsRequestDto {
  constructor(
    public url?: string,
    public distinct?: boolean,
    public page?: number,
    public page_size?: number,
  ) {}
}
