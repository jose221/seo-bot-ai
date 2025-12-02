"""
Motor de auditoría web usando Playwright y Lighthouse.
Realiza análisis técnicos de páginas web.
"""
import asyncio
import json
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime

from app.core.config import get_settings


class AuditEngine:
    """Motor de auditoría para análisis de sitios web"""

    def __init__(self):
        self.settings = get_settings()
        self.browser: Optional[Browser] = None

    async def _init_browser(self):
        """Inicializar navegador Playwright"""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )

    async def _close_browser(self):
        """Cerrar navegador"""
        if self.browser:
            await self.browser.close()
            self.browser = None

    async def execute_navigation_instructions(
        self,
        page: Page,
        instructions: Optional[str]
    ) -> bool:
        """
        Ejecutar instrucciones de navegación antes de auditar.

        Args:
            page: Página de Playwright
            instructions: Texto con instrucciones (ej. "click en #accept-cookies")

        Returns:
            True si se ejecutaron exitosamente, False si hubo errores
        """
        if not instructions or instructions.strip() == "":
            return True

        try:
            # Esperar un poco para que cargue la página
            await asyncio.sleep(2)

            # Analizar instrucciones simples
            # Formato esperado: "click en #selector" o "esperar 3 segundos"
            for line in instructions.lower().split('\n'):
                line = line.strip()

                if not line:
                    continue

                if 'esperar' in line or 'wait' in line:
                    # Extraer segundos
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        seconds = int(match.group(1))
                        await asyncio.sleep(seconds)

                elif 'click' in line:
                    # Extraer selector
                    import re
                    # Buscar algo entre comillas o después de "en"
                    match = re.search(r'["\']([^"\']+)["\']|en\s+([#.\w\-\[\]]+)', line)
                    if match:
                        selector = match.group(1) or match.group(2)
                        try:
                            await page.click(selector, timeout=5000)
                            await asyncio.sleep(1)
                        except Exception as e:
                            print(f"⚠️  No se pudo hacer click en {selector}: {e}")

            return True

        except Exception as e:
            print(f"⚠️  Error ejecutando instrucciones: {e}")
            return False

    async def run_lighthouse_audit(
        self,
        url: str,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecutar auditoría Lighthouse completa.

        Args:
            url: URL a auditar
            instructions: Instrucciones de navegación previas

        Returns:
            Dict con métricas de Lighthouse y HTML de la página
        """
        await self._init_browser()

        try:
            # Crear contexto y página
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            # Navegar a la URL
            print(f"🌐 Navegando a: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Ejecutar instrucciones si existen
            if instructions:
                print(f"📋 Ejecutando instrucciones de navegación...")
                await self.execute_navigation_instructions(page, instructions)

            # Capturar HTML
            html_content = await page.content()

            # Capturar métricas de performance usando Playwright
            performance_metrics = await page.evaluate("""() => {
                return {
                    timing: window.performance.timing,
                    navigation: window.performance.navigation,
                    memory: window.performance.memory || {}
                }
            }""")

            # Capturar Core Web Vitals si están disponibles
            web_vitals = await page.evaluate("""() => {
                return {
                    lcp: window.largestContentfulPaint || null,
                    fid: window.firstInputDelay || null,
                    cls: window.cumulativeLayoutShift || null
                }
            }""")

            # Analizar estructura SEO básica
            seo_analysis = await page.evaluate("""() => {
                return {
                    title: document.title,
                    metaDescription: document.querySelector('meta[name="description"]')?.content || null,
                    h1Count: document.querySelectorAll('h1').length,
                    imageCount: document.querySelectorAll('img').length,
                    imagesWithoutAlt: document.querySelectorAll('img:not([alt])').length,
                    linksCount: document.querySelectorAll('a').length,
                    hasCanonical: !!document.querySelector('link[rel="canonical"]'),
                    hasRobots: !!document.querySelector('meta[name="robots"]'),
                    hasViewport: !!document.querySelector('meta[name="viewport"]')
                }
            }""")

            # Simular scores de Lighthouse (en producción real usarías lighthouse npm)
            # Por ahora generamos scores estimados basados en análisis básico
            lighthouse_scores = self._estimate_lighthouse_scores(
                seo_analysis,
                performance_metrics,
                html_content
            )

            await context.close()

            # Construir resultado
            result = {
                'url': url,
                'timestamp': datetime.utcnow().isoformat(),
                'html_content': html_content[:10000],  # Limitar para no saturar DB
                'html_content_raw': html_content,
                'performance_score': lighthouse_scores['performance'],
                'seo_score': lighthouse_scores['seo'],
                'accessibility_score': lighthouse_scores['accessibility'],
                'best_practices_score': lighthouse_scores['best_practices'],
                'lcp': web_vitals.get('lcp'),
                'fid': web_vitals.get('fid'),
                'cls': web_vitals.get('cls'),
                'seo_analysis': seo_analysis,
                'performance_metrics': {
                    'loadTime': performance_metrics['timing']['loadEventEnd'] - performance_metrics['timing']['navigationStart']
                    if performance_metrics['timing']['loadEventEnd'] > 0 else None
                }
            }

            print(f"✅ Auditoría completada para {url}")
            return result

        except Exception as e:
            print(f"❌ Error en auditoría: {str(e)}")
            raise Exception(f"Error durante la auditoría: {str(e)}")

        finally:
            await self._close_browser()

    def _estimate_lighthouse_scores(
        self,
        seo_analysis: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        html_content: str
    ) -> Dict[str, float]:
        """
        Estimar scores de Lighthouse basados en análisis básico.
        En producción real, esto se reemplaza con Lighthouse real.
        """
        # SEO Score
        seo_score = 100.0
        if not seo_analysis.get('title'): seo_score -= 20
        if not seo_analysis.get('metaDescription'): seo_score -= 15
        if seo_analysis.get('h1Count', 0) == 0: seo_score -= 10
        if seo_analysis.get('h1Count', 0) > 1: seo_score -= 5
        if not seo_analysis.get('hasViewport'): seo_score -= 15
        if not seo_analysis.get('hasCanonical'): seo_score -= 5

        # Accessibility Score
        accessibility_score = 100.0
        if seo_analysis.get('imagesWithoutAlt', 0) > 0:
            ratio = seo_analysis['imagesWithoutAlt'] / max(seo_analysis['imageCount'], 1)
            accessibility_score -= min(ratio * 50, 30)

        # Performance Score (simplificado)
        load_time = performance_metrics.get('timing', {}).get('loadEventEnd', 0) - \
                   performance_metrics.get('timing', {}).get('navigationStart', 0)

        performance_score = 100.0
        if load_time > 5000: performance_score = 50.0
        elif load_time > 3000: performance_score = 70.0
        elif load_time > 2000: performance_score = 85.0

        # Best Practices
        best_practices_score = 85.0  # Base score
        if len(html_content) > 100000: best_practices_score -= 10  # HTML muy grande

        return {
            'performance': max(0, min(100, performance_score)),
            'seo': max(0, min(100, seo_score)),
            'accessibility': max(0, min(100, accessibility_score)),
            'best_practices': max(0, min(100, best_practices_score))
        }


# Singleton
_audit_engine: Optional[AuditEngine] = None


def get_audit_engine() -> AuditEngine:
    """Obtener instancia del motor de auditoría"""
    global _audit_engine
    if _audit_engine is None:
        _audit_engine = AuditEngine()
    return _audit_engine

