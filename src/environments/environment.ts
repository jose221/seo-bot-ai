export const environment = {
  production: false,
  apiUrl: 'https://herandro-services-api.herandro.com.mx',
  endpoints: {
    dashboard: '/api/dashboard',
    auth:{
      user: {
        login: '/auth/platform-admin/login',
        get: '/users',
        get_one: '/users',
        create: '/users/create',
        update: '/users',
        delete: '/users',
      },
      project: {
        get: '/projects',
        get_one: '/projects',
        create: '/projects/create',
        update: '/projects/update',
        delete: '/projects/delete',
        add_project_user: '/project-users/create',
        remove_project_user: '/project-users/delete',
      },
      tenant: {
        get: '/tenants',
        get_one: '/tenants',
        create: '/tenants/create',
        update: '/tenants/update',
        delete: '/tenants/delete',
        add_tenant_user: '/tenant-users/create',
        remove_tenant_user: '/tenant-users/delete',
      },
      module: {
        get: '/modules',
        get_one: '/modules',
        create: '/modules/create',
        update: '/modules/update',
        delete: '/modules/delete',
      },
      route_guard: {
        get: '/route-guards',
        get_one: '/route-guards',
        create: '/route-guards/create',
        update: '/route-guards',
        delete: '/route-guards',
      }
    },
    ai:{
      ai_models:{
        get: '/ai-model',
        get_one: '/ai-model',
        filter: '/ai-model/filter',
        create: '/ai-model/create',
        update: '/ai-model',
        delete: '/ai-model',
        sync_prices_models: '/ai-model/update/price/async'
      },
      ai_vendors:{
        get: '/ai-vendor',
        filter: '/ai-vendor/find',
        create: '/ai-vendor/create',
        update: '/ai-vendor',
        delete: '/ai-vendor'
      },
      ai_request_log:{
        get: '/request-log',
        filter: '/request-log/find',
        report_general: '/request-log/reports/general',
        report_daily: '/request-log/reports/daily',
        report_status: '/request-log/reports/status',
        report_monthly: '/request-log/reports/monthly',
        report_grouped: '/request-log/reports/grouped'
      }
    },
    translate:{
      translate: `/translate`,
      loadTranslations: `/translate`,
      loadTranslationsAsync: `/translate`,
      createOrUpdate: `/translate`,
      delete: `/translate`,
    }
  }
};

