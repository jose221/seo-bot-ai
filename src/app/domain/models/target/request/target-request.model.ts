export class CreateTargetRequestModel {
  constructor(
  public instructions: string,
  public name: string,
  public tech_stack: string,
  public url: string,
  public manual_html_content?: string
  ) {
  }
}

export class FilterTargetRequestModel {
  constructor(
    public page: number,
    public page_size: number,
    public is_active: boolean,
  ) {
  }
}

export class SearchTargetRequestModel {
  constructor(
    public query?: string,
    public page?: number,
    public page_size?: number,
    public is_active?: boolean,
    public only_page_with_audits_completed?: boolean,
  ) {
  }
}
