import { RenderMode, ServerRoute } from '@angular/ssr';

/**
 * Configuración de Renderizado por Vista
 *
 * RenderMode.Prerender:
 *   - Se renderiza en tiempo de build
 *   - Mejor para páginas públicas estáticas (login, home, about)
 *   - Ventajas: Carga ultra-rápida, mejor SEO
 *
 * RenderMode.Server:
 *   - Se renderiza en el servidor en cada petición
 *   - Mejor para páginas protegidas o dinámicas
 *   - Ventajas: Contenido inicial visible, funciona con guards, hidratación en cliente
 *
 * RenderMode.Client:
 *   - Se renderiza solo en el navegador
 *   - Mejor para páginas altamente interactivas sin necesidad de SEO
 *   - Ventajas: Sin complejidad de SSR
 */

export const serverRoutes: ServerRoute[] = [
  {
    path: '',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'admin',
    renderMode: RenderMode.Server
  },
  {
    path: 'admin/target',
    renderMode: RenderMode.Server
  },
  {
    path: 'admin/**',
    renderMode: RenderMode.Server
  },
  {
    path: '**',
    renderMode: RenderMode.Prerender
  }
];
