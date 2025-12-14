export class AuthLoginResponseModel {
  constructor(
    access_token: string,
    token_type: string,
    token_id: string,
    user_id: string,
    user_email: string,
    user_name: string,
    tenant_id: string,
    project_id: string,
    expires_at: string,
    scope: string
  ) {}
}

export class AuthRegisterResponseModel {
  constructor(
    access_token: string,
    token_type: string,
    token_id: string,
    user_id: string,
    user_email: string,
    user_name: string,
    tenant_id: string,
    project_id: string,
    expires_at: string,
    scope: string
  ) {
  }
}
