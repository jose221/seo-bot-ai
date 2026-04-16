export class TargetResponseModel {
  constructor(
    public id: string,
    public user_id: string,
    public instructions: string,
    public name: string,
    public tech_stack: string,
    public url: string,
    public is_active: boolean,
    public manual_html_content?: string,
    public tags?: string[],
    public provider?: string,
  ) {}
}

export class SearchTargetResponseModel {
  constructor(
    public id: string,
    public name: string,
    public url: string,
    public is_active: boolean,
    public tags?: string[],
    public provider?: string,
  ) {}
}

export class TargetHtmlResponseModel {
  constructor(
    public target_id: string,
    public url: string,
    public html: string,
    public source: 'live' | 'stored',
    public html_length: number,
  ) {}
}

