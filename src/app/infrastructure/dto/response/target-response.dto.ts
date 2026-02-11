export interface TargetResponseDto {
  id: string
  user_id: string
  instructions: string
  name: string
  tech_stack: string
  url: string,
  is_active: boolean
  manual_html_content?: string
}

export interface SearchTargetResponseDto {
  id: string
  name: string
  url: string,
  is_active: boolean
}
