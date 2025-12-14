export const environment = {
  production: false,
  apiUrl: 'https://localhost:8000/api/v1',
  endpoints: {
    auth:{
      login: '/auth/login',
      register: '/auth/register',
      route_guard: {
        get: '/route-guards',
        get_one: '/route-guards',
        create: '/route-guards/create',
        update: '/route-guards',
        delete: '/route-guards',
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

