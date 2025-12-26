export const environment = {
  production: false,
  apiUrl: 'http://localhost:3101/api/v1',
  prometheusUrl: 'http://localhost:9090',
  metricsUrl: 'http://localhost:3101/metrics',
  timeout: 360000,
  endpoints: {
    auth:{
      login: '/auth/login',
      register: '/auth/register'
    },
    translate:{
      translate: `/translate`,
      loadTranslations: `/translate`,
      loadTranslationsAsync: `/translate`,
      createOrUpdate: `/translate`,
      delete: `/translate`,
    },
    target:{
      path: '/targets',
      search: '/targets/search'
    },
    audit:{
      path: '/audits',
      compare: '/audits/compare',
      comparisons: '/audits/comparisons',
      search: '/audits/search'
    }
  },
  settings:{
    auth:{
      expires_in_days: 30,
      token_name: 'seoBotAi',
    },
    translate:{
      default_language: 'es',
      expires_in_days: 30,
      cookie_name: 'lang'
    }
  }
};

