export interface TargetRequestDto {
  id: string
  user_id: string
  instructions: string
  name: string
  tech_stack: string
  url: string
  manual_html_content?: string
}

export interface CreateTargetRequestDto {
  instructions: string
  name: string
  tech_stack: string
  url: string
  manual_html_content?: string
}

export interface FilterTargetRequestDto {
  page: number
  page_size: number
  is_active: boolean
}

export interface SearchTargetRequestDto {
  query: string
  page: number
  page_size: number
  is_active: boolean
  only_page_with_audits_completed?: boolean
}
