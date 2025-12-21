export interface TargetRequestDto {
  id: string
  user_id: string
  instructions: string
  name: string
  tech_stack: string
  url: string
}

export interface CreateTargetRequestDto {
  instructions: string
  name: string
  tech_stack: string
  url: string
}

export interface FilterTargetRequestDto {
  page: number
  page_size: number
  is_active: boolean
}
