export interface AuthLoginRequestDto {
  email: string
  password: string
  token_name: string
  expires_in_days: number
}

export interface AuthRegisterRequestDto {
  city: string,
  country_code: string,
  email: string,
  full_name: string,
  password: string,
  project_id: string,
  username: string
}
