export interface TargetRequestDto {
  id: string
  user_id: string
  instructions: string
  name: string
  tech_stack: string
  url: string
  manual_html_content?: string
  tags?: string[]
  provider?: string
}

export interface CreateTargetRequestDto {
  instructions: string
  name: string
  tech_stack: string
  url: string
  manual_html_content?: string
  tags?: string[]
  provider?: string
}

export interface UpdateTargetRequestDto {
  name?: string
  instructions?: string
  tech_stack?: string
  is_active?: boolean
  manual_html_content?: string
  tags?: string[]
  provider?: string
}

export interface FilterTargetRequestDto {
  page: number
  page_size: number
  is_active: boolean
  tag?: string
  provider?: string
}

export interface SearchTargetRequestDto {
  query?: string
  page?: number
  page_size?: number
  is_active?: boolean
  only_page_with_audits_completed?: boolean
  exclude_web_page_id?: string
  tag?: string
  provider?: string
}
