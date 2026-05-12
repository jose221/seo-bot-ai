import asyncio
import logging
import os
import random
import sys
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import nodriver as uc
import nodriver.cdp.input_ as cdp_input
from pydantic import BaseModel, Field

from app.core.proxy import ProxySettings
from app.core.stealth import StealthConfig
from app.core.storage import PublicAssetStorage

logger = logging.getLogger(__name__)


class InputType(str, Enum):
  URL = "url"
  HTML = "html"


class ValidationResult(BaseModel):
  is_success: bool
  result_url: Optional[str] = None
  html_content: Optional[str] = None
  error_message: Optional[str] = None
  method_used: str = "nodriver"
  blocked_by_google: bool = False
  proxy_used: bool = False
  screenshots: list[dict[str, str]] = Field(default_factory=list)


class GoogleRichResultsEngine:
  _startup_lock = asyncio.Lock()

  def __init__(
    self,
    proxy_settings: Optional[ProxySettings] = None,
    screenshots_dir: str = "storage/images",
    storage_url_prefix: str = "/storage/images",
    max_concurrent_tasks: int = 3,
    artifact_storage: Optional[PublicAssetStorage] = None,
    storage_folder: str = "images",
    headless: bool = False,
    hide_window: bool = False,
  ):
    self._proxy_settings = proxy_settings
    self._proxy_forwarder = (
      proxy_settings.create_nodriver_forwarder()
      if proxy_settings and proxy_settings.has_auth
      else None
    )
    self._proxy_server = (
      self._proxy_forwarder.proxy_server
      if self._proxy_forwarder is not None
      else proxy_settings.server if proxy_settings else None
    )
    self._proxy_bypass_list = proxy_settings.chrome_bypass_list if proxy_settings else None
    self._headless = headless
    self._hide_window = hide_window
    self.target_url = "https://search.google.com/test/rich-results?hl=es"
    self.artifact_storage = artifact_storage
    self.storage_folder = storage_folder.strip("/")
    self.screenshots_dir = Path(screenshots_dir)
    self.storage_url_prefix = storage_url_prefix.rstrip("/")
    if not self.artifact_storage or not self.artifact_storage.uses_remote_storage():
      self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

  def _build_screenshot_artifact(self, filename: str) -> dict[str, str]:
    return {
      "path": str(self.screenshots_dir / filename),
      "url": f"{self.storage_url_prefix}/{filename}"
    }

  async def _capture_screenshot(self, page, label: str) -> Optional[dict[str, str]]:
    if page is None:
      return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"rich_results_{label}_{timestamp}.png"

    try:
      if self.artifact_storage and self.artifact_storage.uses_remote_storage():
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
          target_path = Path(tmp_file.name)
        try:
          await page.save_screenshot(str(target_path))
          stored = self.artifact_storage.upload_public_file(
            target_path,
            folder=self.storage_folder,
            filename=filename,
            content_type="image/png",
            remove_local=True,
          )
          return {"path": stored["path"], "url": stored["url"]}
        finally:
          try:
            if target_path.exists():
              target_path.unlink()
          except OSError:
            pass

      target_path = self.screenshots_dir / filename
      await page.save_screenshot(str(target_path))
      return self._build_screenshot_artifact(filename)
    except Exception as exc:
      logger.warning("Could not save screenshot %s: %s", label, exc)
      return None

  async def validate(self, input_type: InputType, content: str, worker_id: str = "default") -> ValidationResult:
    """
    Punto de entrada seguro para concurrencia.
    worker_id: ID único del hilo/worker (ej. '1', '2') para aislar el caché del navegador.
    """
    async with self._semaphore:
      return await self._validate_internal(input_type, content, worker_id)

  async def _validate_internal(self, input_type: InputType, content: str, worker_id: str) -> ValidationResult:
    """Lógica central de validación con stealth mejorado y optimización de red."""
    logger.info(f"[Worker {worker_id}] Starting validation for {input_type.value}...")
    browser = None
    display = None
    page = None
    current_url = self.target_url

    # Ruta de caché persistente y aislada por worker
    cache_path = os.path.abspath(f"storage/browser_cache/worker_{worker_id}")

    # Perfil de fingerprint aleatorio y consistente por sesión
    stealth = StealthConfig(
      headless=self._headless,
      proxy_server=self._proxy_server,
      proxy_bypass=self._proxy_bypass_list,
      hide_window=self._hide_window,
    )

    # Inyección de optimizaciones para ahorro masivo de ancho de banda
    optimization_args = [
      "--blink-settings=imagesEnabled=false",
      "--disable-background-networking",
      "--disable-component-update",
      "--safebrowsing-disable-auto-update",
      "--disable-sync",
      "--disable-default-apps",
      "--disable-extensions",
      "--enable-features=NetworkService,NetworkServiceInProcess",
      f"--disk-cache-size={100 * 1024 * 1024}"
    ]
    stealth.browser_args.extend(optimization_args)

    try:
      async with self._startup_lock:
        if not self._headless and sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
          try:
            from pyvirtualdisplay import Display
            logger.info("Starting Xvfb virtual display...")
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ['DISPLAY'] = display.new_display_var
          except ImportError:
            logger.warning("pyvirtualdisplay not found. Browsing might fail on headless server.")

        browser = await uc.start(
          headless=stealth.headless_mode,
          browser_args=stealth.browser_args,
          user_data_dir=cache_path
        )

      # Inyectar stealth en about:blank ANTES de navegar al sitio objetivo
      page = await browser.get("about:blank")
      await stealth.inject(page)
      await stealth.simulate_mouse_move(page)
      await stealth.human_delay(0.5, 1.2)

      logger.info(f"[Worker {worker_id}] Navigating to: {self.target_url}")
      page = await browser.get(self.target_url)
      current_url = self.target_url

      # Espera humana para que Google procese el fingerprint
      await stealth.human_delay(2.5, 4.5)
      await stealth.simulate_mouse_move(page)

      # 3. Interacción con la UI de Google
      if input_type == InputType.HTML:
        logger.info("Switching to 'Código' tab...")

        try:
          codigo_tab = await page.select("div[aria-controls='fmefR']")
          if codigo_tab:
            await codigo_tab.click()
          else:
            raise Exception("Tab 'Código' (aria-controls) not found")
        except Exception as e:
          logger.warning(f"aria-controls tab no encontrado, usando fallback de clases: {e}")
          codigo_tab = await page.select("div.ThdJC.kaAt2.Y8xidc.RPhebf.KKjvXb.j7nIZb")
          if codigo_tab:
            await codigo_tab.click()
          else:
            raise Exception("Tab 'Código' no encontrado con ningún selector — Google cambió su UI")

        await stealth.human_delay(1.5, 2.5)

        logger.info("Enfocando el textarea oculto de CodeMirror...")
        textarea = await page.select(".CodeMirror.cm-s-search-console-code-input textarea")
        if not textarea:
          raise Exception("CodeMirror textarea no encontrado — Google cambió su UI")
        await textarea.click()
        await stealth.human_delay(0.5, 1.0)

        logger.info("Inyectando HTML vía CDP insert_text...")
        await textarea.send_keys("<!--Proyecto-->")
        await page.send(cdp_input.insert_text(text=content))
        await stealth.human_delay(1.5, 2.5)

        logger.info("Clicking 'probar código' button...")
        try:
          submit_btn = await page.select("div[jsname='oe2Hje']")
          if not submit_btn:
            raise Exception("Botón 'probar código' no encontrado")
          await stealth.simulate_mouse_move(page)
          await submit_btn.click()
        except Exception as e:
          logger.warning(f"Fallo el clic físico, usando JS fallback: {e}")
          await page.evaluate("""
            () => {
              const btn = document.querySelector("div[jsname='oe2Hje']");
              if (btn) btn.click();
            }
          """)

      else:
        # Flujo de URL
        url_input = await page.select("input[type='url']")
        if not url_input:
          raise Exception("Campo URL no encontrado — Google cambió su UI")
        await stealth.simulate_mouse_move(page)
        await url_input.send_keys(content)

        await stealth.human_delay(2.0, 3.5)

        submit_btn = await page.select("div[jsname='LZQqje']")
        if not submit_btn:
          raise Exception("Botón 'probar URL' no encontrado — Google cambió su UI")
        await submit_btn.click()
        logger.info("Clicked 'probar URL' button")

      # 4. Polling con detección nativa de reCAPTCHA
      logger.info("Polling for URL change indicating analysis completion...")
      current_url = ""

      for _ in range(80):
        current_url = await page.evaluate("window.location.href")

        if "sorry" in current_url.lower():
          raise Exception("Google explicitly blocked the request (429/Sorry).")

        # Detección instantánea de Iframe de reCAPTCHA (sin Timeouts)
        recaptcha_frames = await page.select_all('iframe[src*="recaptcha"]')
        if recaptcha_frames:
          raise Exception("Google explicitly blocked the request (reCAPTCHA detected).")

        if "/result?id=" in current_url:
          break

        await asyncio.sleep(1.5)

      if "/result?id=" not in current_url:
        raise Exception("Timeout esperando que Google procese la URL. El modal no finalizó a tiempo.")

      # 5. Extracción de resultados
      logger.info("Analysis complete. Extracting final HTML...")
      await stealth.human_delay(1.5, 2.5)
      final_html = await page.get_content()

      screenshots: list[dict[str, str]] = []
      screenshot = await self._capture_screenshot(page, "success")
      if screenshot:
        screenshots.append(screenshot)

      return ValidationResult(
        is_success=True,
        result_url=current_url,
        html_content=final_html,
        method_used="nodriver",
        proxy_used=bool(self._proxy_server),
        screenshots=screenshots
      )

    except Exception as e:
      error_message = str(e)
      logger.error(f"[Worker {worker_id}] Validation failed: {error_message}")
      screenshots: list[dict[str, str]] = []

      if page:
        screenshot = await self._capture_screenshot(page, "error")
        if screenshot:
          screenshots.append(screenshot)

      return ValidationResult(
        is_success=False,
        result_url=current_url or self.target_url,
        error_message=error_message,
        method_used="nodriver",
        blocked_by_google="block" in error_message.lower() or "captcha" in error_message.lower() or "sorry" in error_message.lower() or "recaptcha" in error_message.lower(),
        proxy_used=bool(self._proxy_server),
        screenshots=screenshots
      )

    finally:
      if browser:
        try:
          browser.stop()
        except Exception as e:
          logger.warning(f"Error stopping browser: {e}")
      if self._proxy_forwarder and getattr(self._proxy_forwarder, "server", None):
        self._proxy_forwarder.server.close()
        await self._proxy_forwarder.server.wait_closed()
      if display:
        try:
          display.stop()
        except Exception as e:
          logger.warning(f"Error stopping Xvfb display: {e}")
