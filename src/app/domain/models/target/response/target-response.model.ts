export class TargetResponseModel {
  constructor(
    public id: string,
    public user_id: string,
    public instructions: string,
    public name: string,
    public tech_stack: string,
    public url: string,
    public is_active: boolean
  ) {}
}
