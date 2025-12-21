export class CreateTargetRequestModel {
  constructor(
  public instructions: string,
  public name: string,
  public tech_stack: string,
  public url: string
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
