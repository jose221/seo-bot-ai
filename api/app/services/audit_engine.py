import asyncio
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

# Playwright Imports
from playwright.async_api import async_playwright, Page, Browser

# Adaptador para soporte de versiones 1.x y 2.x de playwright-stealth
stealth_async = None
try:
    # Intento 1: Versión antigua (función directa)
    from playwright_stealth import stealth_async
except ImportError:
    try:
        # Intento 2: Versión nueva/Clase (v2.x)
        from playwright_stealth import Stealth
        _stealth_instance = Stealth()
        stealth_async = _stealth_instance.apply_stealth_async
        logging.getLogger(__name__).info("✅ Using playwright-stealth v2 (Class-based strategy)")
    except ImportError:
        # Log warning and set to None if not available
        logging.getLogger(__name__).warning("⚠️ playwright-stealth not found or incompatible. Using custom stealth only.")
        stealth_async = None

# Nodriver Import (Fallback)
import nodriver as uc

from app.core.config import get_settings

# Configurar Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuditEngine:
    """
    Web Audit Engine with Hybrid Strategy:
    1. Primary: Playwright (Optimized for speed/resources)
    2. Fallback: Nodriver (Optimized for evasion against DataDome/Cloudflare)
    """

    def __init__(self):
        self.settings = get_settings()
        self.browser: Optional[Browser] = None

    async def _init_browser(self):
        """Initialize Playwright browser with stealth arguments."""
        if self.browser is None:
            playwright = await async_playwright().start()

            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--disable-extensions',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]

            self.browser = await playwright.chromium.launch(
                headless=True,
                args=browser_args
            )

    async def _close_browser(self):
        """Clean up Playwright resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

    async def _apply_playwright_stealth(self, page: Page):
        """Manual stealth injection for Playwright."""
        # Aplicar stealth de la librería (más robusto)
        if stealth_async:
            try:
                await stealth_async(page)
            except Exception as e:
                logger.warning(f"⚠️ Error aplicando playwright-stealth: {e}")

        # Refuerzos manuales adicionales
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        await page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        await page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    def _deserialize_nodriver_data(self, data: Any) -> Any:
        """
        Deserializa recursivamente la estructura cruda de CDP (Chrome DevTools Protocol)
        que nodriver devuelve a veces (listas de pares clave-valor y wrappers).
        """
        # Caso 0: Manejo explícito de tipos null/undefined de CDP (que a veces no traen 'value')
        if isinstance(data, dict) and data.get('type') in ('null', 'undefined'):
            return None

        # Caso 1: Wrapper de valor {'type': '...', 'value': ...}
        if isinstance(data, dict) and 'type' in data and 'value' in data:
            if data['type'] == 'object':
                return self._deserialize_nodriver_data(data['value'])
            return data['value']

        # Caso 2: Listas (pueden ser objetos serializados como listas de pares KV)
        if isinstance(data, list):
            # Heurística: Si es una lista donde todos los elementos son listas de 2 items [str, any]
            # asumimos que es un objeto (diccionario)
            is_kv_list = True
            if not data:
                return []

            for item in data:
                if not (isinstance(item, list) and len(item) == 2 and isinstance(item[0], str)):
                    is_kv_list = False
                    break

            if is_kv_list:
                return {item[0]: self._deserialize_nodriver_data(item[1]) for item in data}

            # Si no es KV list, es una lista normal, procesamos sus elementos
            return [self._deserialize_nodriver_data(item) for item in data]

        # Caso Base: Primitivos
        return data

    async def _execute_nodriver_audit(self, url: str) -> Dict[str, Any]:
        """
        Fallback Method: Executes audit using 'nodriver' (Chrome CDP).
        Used when Playwright is detected by DataDome.
        """
        logger.info(f"🛡️ Activating Fallback Protocol (nodriver) for: {url}")
        browser = None
        display = None

        try:
            # --- Virtual Display Logic for Ubuntu Server ---
            # Detect if running on Linux without a physical display
            if sys.platform.startswith('linux'):
                # Check if DISPLAY is already set (optimized for Docker CMD)
                if os.environ.get('DISPLAY'):
                    logger.info(f"🖥️  Using existing DISPLAY environment: {os.environ['DISPLAY']}")
                else:
                    try:
                        from pyvirtualdisplay import Display
                        logger.info("🖥️  Starting Xvfb (Virtual Display) for nodriver evasion...")
                        display = Display(visible=0, size=(1920, 1080))
                        display.start()
                    except ImportError:
                        logger.warning("⚠️  Warning: pyvirtualdisplay not installed. Nodriver might fail on headless server.")
                        logger.info("ℹ️  Fix: pip install pyvirtualdisplay && sudo apt-get install xvfb")

            # Start real Chrome instance (High evasion success rate)
            # headless=False is CRITICAL for DataDome bypass.
            # On Ubuntu Server, Xvfb handles the GUI requirement.

            # Common Anti-Detect Args for Docker/Linux
            browser_args = [
                "--window-size=1920,1080",
                "--no-first-run",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]

            browser = await uc.start(
                headless=False,
                browser_args=browser_args
            )

            page = await browser.get(url)

            # Smart wait for body instead of fixed sleep
            await page.wait_for("body", timeout=60)

            # Double check if even nodriver was blocked
            content = await page.get_content()
            if "captcha-delivery" in content or "DataDome" in content:
                # Intento de debug: Guardar screenshot y HTML parcial
                try:
                    debug_dir = "/app/storage/reports"
                    if not os.path.exists(debug_dir):
                        os.makedirs(debug_dir, exist_ok=True)

                    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"{debug_dir}/BLOCK_DEBUG_{timestamp}.jpg"
                    await page.save_screenshot(screenshot_path)
                    logger.error(f"📸 Screenshot de bloqueo guardado en: {screenshot_path}")
                except Exception as dbg_err:
                    logger.error(f"No se pudo guardar evidencias del bloqueo: {dbg_err}")

                raise Exception("Nodriver also blocked by DataDome.")

            # Extract metrics using JS evaluation via nodriver
            metrics_data_raw = await page.evaluate("""
                (function() {
                    const nav = performance.getEntriesByType("navigation")[0] || {};
                    return {
                        timing: window.performance.timing.toJSON(),
                        web_vitals: {
                            lcp: window.largestContentfulPaint || null,
                            fid: window.firstInputDelay || null,
                            cls: window.cumulativeLayoutShift || null
                        },
                        seo: {
                            title: document.title,
                            metaDescription: document.querySelector('meta[name="description"]')?.content || null,
                            h1Count: document.querySelectorAll('h1').length,
                            imageCount: document.querySelectorAll('img').length,
                            imagesWithoutAlt: document.querySelectorAll('img:not([alt])').length,
                            linksCount: document.querySelectorAll('a').length,
                            hasCanonical: !!document.querySelector('link[rel="canonical"]'),
                            hasViewport: !!document.querySelector('meta[name="viewport"]')
                        },
                        loadDuration: nav.loadEventEnd - nav.startTime || 0
                    }
                })()
            """)

            # CRITICAL FIX: Parse raw CDP structure to Python Dict
            metrics_data = self._deserialize_nodriver_data(metrics_data_raw)

            # Asegurar que sea un dict (fallback por seguridad)
            if not isinstance(metrics_data, dict):
                logger.warning(f"⚠️ Warning: metrics_data structure unexpected: {type(metrics_data)}")
                metrics_data = {'seo': {}, 'web_vitals': {}, 'loadDuration': 0, 'timing': {}}

            # Construct the result dictionary matching Playwright's output structure
            scores = self._estimate_lighthouse_scores(
                metrics_data.get('seo', {}),
                {'loadDuration': metrics_data.get('loadDuration', 0)},
                content
            )

            return {
                'url': url,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status_code': 200, # Nodriver handles connection errors via exception
                'html_content': content[:15000],
                'html_content_raw': content,
                'performance_score': scores['performance'],
                'seo_score': scores['seo'],
                'accessibility_score': scores['accessibility'],
                'best_practices_score': scores['best_practices'],
                'lcp': metrics_data.get('web_vitals', {}).get('lcp'),
                'cls': metrics_data.get('web_vitals', {}).get('cls'),
                'seo_analysis': metrics_data.get('seo', {}),
                'performance_metrics': metrics_data.get('timing', {}),
                'method': 'nodriver_fallback'
            }

        except Exception as e:
            logger.error(f"❌ Fallback (nodriver) failed: {e}")
            return {
                "error": True,
                "message": f"Bloqueo Anti-Bot Persistente (DataDome). Falló Playwright y Nodriver. Error: {str(e)}",
                "url": url
            }
        finally:
            if browser:
                try:
                    browser.stop()
                except:
                    pass
            # Clean up virtual display
            if display:
                try:
                    display.stop()
                except:
                    pass

    async def run_lighthouse_audit(
            self,
            url: str,
            instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for auditing.
        Tries Playwright first, switches to Nodriver if blocked.
        """
        await self._init_browser()
        context = None

        try:
            # 1. Playwright Execution Strategy
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='es-MX',
                timezone_id='America/Mexico_City',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = await context.new_page()
            await self._apply_playwright_stealth(page)

            logger.info(f"🌐 [Playwright] Navigating to: {url}")

            try:
                response = await page.goto(url, wait_until='networkidle', timeout=450000)
            except Exception:
                response = None

            # 2. Block Detection & Fallback Trigger
            await asyncio.sleep(2) # Allow JS redirects to happen
            content_check = await page.content()

            if "captcha-delivery" in content_check or "DataDome" in content_check:
                logger.warning("🚨 DataDome Block detected in Playwright.")

                # Cleanup Playwright context before switching
                await context.close()
                await self._close_browser()

                # TRIGGER FALLBACK
                return await self._execute_nodriver_audit(url)

            # 3. Standard Playwright Extraction (If not blocked)
            if instructions:
                pass

            html_content = await page.content()

            # JS Injection for metrics
            performance_metrics = await page.evaluate("""() => {
                const nav = performance.getEntriesByType("navigation")[0] || {};
                return {
                    timing: window.performance.timing,
                    loadDuration: nav.loadEventEnd - nav.startTime || 0
                }
            }""")

            web_vitals = await page.evaluate("""() => ({
                lcp: window.largestContentfulPaint || null,
                cls: window.cumulativeLayoutShift || null
            })""")

            seo_analysis = await page.evaluate("""() => ({
                title: document.title,
                metaDescription: document.querySelector('meta[name="description"]')?.content || null,
                h1Count: document.querySelectorAll('h1').length,
                imageCount: document.querySelectorAll('img').length,
                imagesWithoutAlt: document.querySelectorAll('img:not([alt])').length,
                hasViewport: !!document.querySelector('meta[name="viewport"]')
            })""")

            lighthouse_scores = self._estimate_lighthouse_scores(
                seo_analysis,
                performance_metrics,
                html_content
            )

            return {
                'url': url,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status_code': response.status if response else 0,
                'html_content': html_content[:15000],
                'html_content_raw': html_content,
                'performance_score': lighthouse_scores['performance'],
                'seo_score': lighthouse_scores['seo'],
                'accessibility_score': lighthouse_scores['accessibility'],
                'best_practices_score': lighthouse_scores['best_practices'],
                'lcp': web_vitals.get('lcp'),
                'cls': web_vitals.get('cls'),
                'seo_analysis': seo_analysis,
                'performance_metrics': performance_metrics,
                'method': 'playwright_stealth'
            }

        except Exception as e:
            logger.error(f"❌ Critical Error in Playwright Audit: {str(e)}")
            # Try fallback one last time if it was a generic error that looks like a timeout/block
            if "Timeout" in str(e) or "Target closed" in str(e):
                return await self._execute_nodriver_audit(url)

            return {
                "error": True,
                "message": str(e),
                "url": url
            }

        finally:
            if context:
                try: await context.close()
                except: pass
            await self._close_browser()

    def _estimate_lighthouse_scores(
            self,
            seo_analysis: Dict[str, Any],
            performance_metrics: Dict[str, Any],
            html_content: str
    ) -> Dict[str, float]:
        """
        Shared logic to calculate scores, used by both Playwright and Nodriver methods.
        """
        # SEO Calculation
        seo_score = 100.0
        if not seo_analysis.get('title'): seo_score -= 20
        if not seo_analysis.get('metaDescription'): seo_score -= 15
        if seo_analysis.get('h1Count', 0) == 0: seo_score -= 10
        if seo_analysis.get('h1Count', 0) > 1: seo_score -= 5
        if not seo_analysis.get('hasViewport'): seo_score -= 15

        # Accessibility Calculation
        accessibility_score = 100.0
        img_count = seo_analysis.get('imageCount', 0)
        if img_count > 0:
            bad_imgs = seo_analysis.get('imagesWithoutAlt', 0)
            ratio = bad_imgs / img_count
            accessibility_score -= (ratio * 40)

        # Performance Calculation
        load_time = performance_metrics.get('loadDuration', 0)
        performance_score = 100.0

        if load_time > 6000: performance_score = 40.0
        elif load_time > 4000: performance_score = 60.0
        elif load_time > 2000: performance_score = 80.0
        elif load_time > 0: performance_score = 95.0

        # Best Practices
        best_practices_score = 90.0
        if len(html_content) > 200000: best_practices_score -= 15

        return {
            'performance': round(max(0, min(100, performance_score)), 1),
            'seo': round(max(0, min(100, seo_score)), 1),
            'accessibility': round(max(0, min(100, accessibility_score)), 1),
            'best_practices': round(max(0, min(100, best_practices_score)), 1)
        }

# Singleton Pattern
_audit_engine: Optional[AuditEngine] = None

def get_audit_engine() -> AuditEngine:
    global _audit_engine
    if _audit_engine is None:
        _audit_engine = AuditEngine()
    return _audit_engine
