export class RouteGuardRequestModel {
  constructor(
    module_id: string,
    method: string,
    path_pattern: string,
    require_project?: boolean,
    require_platform_admin?: boolean,
    available_token_as_param?: boolean,
    require_tenant?: boolean,
    require_user?: boolean,
    is_active?: boolean,
  ) {
  }
}
