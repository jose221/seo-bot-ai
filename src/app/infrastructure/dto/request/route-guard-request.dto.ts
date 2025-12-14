export interface RouteGuardRequestDto {
  module_id: string;
  method: string;
  require_project?: boolean;
  require_platform_admin?: boolean;
  available_token_as_param?: boolean;
  path_pattern: string;
  require_tenant?: boolean
  require_user?: boolean;
  is_active?: boolean;
}
