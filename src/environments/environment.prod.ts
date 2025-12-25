export const environment = {
  production: true,
  //apiUrl: 'http://84.247.137.97:3101/api/v1',
  apiUrl: 'https://api.seo-bot-ai.herandro.com.mx/api/v1',
  //prometheusUrl: 'http://84.247.137.97:9090',
  prometheusUrl: 'https://prometheus.herandro.com.mx',
  metricsUrl: 'https://api.seo-bot-ai.herandro.com.mx/metrics',
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

