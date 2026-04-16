export class CreateTargetRequestModel {
  constructor(
  public instructions: string,
  public name: string,
  public tech_stack: string,
  public url: string,
  public manual_html_content?: string,
  public tags?: string[],
  public provider?: string,
  ) {
  }
}

export class UpdateTargetRequestModel {
  constructor(
    public name?: string,
    public instructions?: string,
    public tech_stack?: string,
    public is_active?: boolean,
    public manual_html_content?: string,
    public tags?: string[],
    public provider?: string,
  ) {}
}

export class FilterTargetRequestModel {
  constructor(
    public page: number,
    public page_size: number,
    public is_active: boolean,
    public tag?: string,
    public provider?: string,
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
    public exclude_web_page_id?: string,
    public tag?: string,
    public provider?: string,
  ) {
  }
}
