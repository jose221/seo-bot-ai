export class AuthLoginRequestModel {
  constructor(
    public email: string,
    public password: string,
    public token_name: string,
    public expires_in_days: number
  ) {
  }
}

export class AuthRegisterRequestModel {
  constructor(
    city: string,
    country_code: string,
    email: string,
    full_name: string,
    password: string,
    project_id: string,
    username: string
  ) {
  }
}
