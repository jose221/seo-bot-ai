export class AuthLoginResponseModel {
  constructor(
    public access_token: string,
    public token_type: string,
    public token_id: string,
    public user_id: string,
    public user_email: string,
    public user_name: string,
    public tenant_id: string,
    public project_id: string,
    public expires_at: string,
    public scope: string
  ) {}
}

export class AuthRegisterResponseModel {
  constructor(
    public  access_token: string,
    public token_type: string,
    public token_id: string,
    public user_id: string,
    public user_email: string,
    public user_name: string,
    public tenant_id: string,
    public project_id: string,
    public expires_at: string,
    public scope: string
  ) {
  }
}
