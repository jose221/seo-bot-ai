export interface TargetResponseDto {
  id: string
  user_id: string
  instructions: string
  name: string
  tech_stack: string
  url: string,
  is_active: boolean
}

export interface SearchTargetResponseDto {
  id: string
  name: string
  url: string,
  is_active: boolean
}
