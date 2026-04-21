export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  //prometheusUrl: 'http://84.247.137.97:9090',
  prometheusUrl: 'https://prometheus.herandro.com.mx',
  metricsUrl: 'https://api.seo-bot-ai.herandro.com.mx/metrics',
  timeout: 360000,
  keycloak: {
    /** URL base del servidor Keycloak (sin /realms/...) */
    url: 'https://auth-keycloak.herandro.com.mx',
    /** Realm donde está configurado el cliente */
    realm: 'herandro',
    /** Cliente público del frontend */
    clientId: 'portfolio-web',
    /** Redirección tras login exitoso */
    redirectUri: 'http://localhost:4200/admin',
    /** Redirección tras logout */
    postLogoutRedirectUri: 'http://localhost:4200/',
  },
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
      search: '/targets/search',
      tags: '/targets/tags'
    },
    audit:{
      path: '/audits',
      compare: '/audits/compare',
      comparisons: '/audits/comparisons',
      search: '/audits/search'
    },
    auditSchema:{
      path: '/audits/schemas'
    },
    auditUrlValidation:{
      path: '/audits/url-validations'
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

