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

from pydantic import BaseModel, Field

import nodriver as uc
import nodriver.cdp.input_ as cdp_input
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
  blocked_by_schema: bool = False
  screenshots: list[dict[str, str]] = Field(default_factory=list)

class SchemaOrgValidatorEngine:
  # Candado estático a nivel de clase para evitar Race Conditions
  # al mutar la variable de entorno os.environ['DISPLAY']
  _startup_lock = asyncio.Lock()

  def __init__(
    self,
    proxy_settings: Optional[ProxySettings] = None,
    screenshots_dir: str = "storage/images/schema_org",
    storage_url_prefix: str = "/storage/images/schema_org",
    max_concurrent_tasks: int = 3,
    artifact_storage: Optional[PublicAssetStorage] = None,
    storage_folder: str = "images/schema_org",
    headless: bool = False,
  ):
    """
    Inicializa el motor de validación para validator.schema.org.
    """
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
    self.target_url = "https://validator.schema.org/"
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

  async def _get_result_item_count(self, page) -> int:
    """Cuenta los items de resultado via CDP query_selector_all (sin evaluate)."""
    try:
      items = await page.query_selector_all("ul.mdl-list li.mdl-list__item")
      return len(items) if items else 0
    except Exception:
      return 0

  async def _wait_for_results_ready(self, page, timeout_seconds: int = 30) -> int:
    dashboard_ready_streak = 0
    for _ in range(timeout_seconds):
      item_count = await self._get_result_item_count(page)
      if item_count > 0:
        return item_count

      # Detectar dashboard listo via CDP query_selector + get_content (sin evaluate)
      try:
        dashboard_ready = bool(
          await page.query_selector(".sKfxWe-BeDmAc")
          or await page.query_selector(".mdl-list")
        )
        if not dashboard_ready:
          html = await page.get_content()
          if html:
            dashboard_ready = any(
              kw in html for kw in ("ELEMENTO", "ERRORES", "ADVERTENCIAS")
            )
      except Exception:
        dashboard_ready = False

      if dashboard_ready:
        dashboard_ready_streak += 1
        if dashboard_ready_streak >= 3:
          return 0
      else:
        dashboard_ready_streak = 0

      await asyncio.sleep(1.0)

    logger.warning("Timeout esperando resultados de Schema.org")
    return await self._get_result_item_count(page)

  async def _click_result_item(self, page, index: int) -> bool:
    """Hace click en un item de resultado via CDP query_selector_all (sin evaluate)."""
    try:
      items = await page.query_selector_all("ul.mdl-list li.mdl-list__item")
      if not items or index >= len(items):
        return False
      await items[index].click()
      return True
    except Exception as exc:
      logger.warning("Error al hacer click en el elemento %s: %s", index, exc)
      return False

  async def _wait_for_item_detail(self, page, timeout_seconds: int = 10) -> bool:
    """Espera el botón 'arrow_back' usando find() de nodriver (CDP puro, sin evaluate)."""
    for _ in range(timeout_seconds * 2):
      try:
        back_btn = await page.find("arrow_back", timeout=0.5)
        if back_btn:
          return True
      except Exception:
        pass
      await asyncio.sleep(0.5)
    return False

  async def _go_back_to_dashboard(self, page, timeout_seconds: int = 10) -> None:
    """Regresa al dashboard haciendo click en el botón 'arrow_back' via CDP (sin evaluate)."""
    try:
      back_btn = await page.find("arrow_back", timeout=3)
      if back_btn:
        await back_btn.click()
    except Exception as exc:
      logger.warning("Error al regresar al dashboard: %s", exc)
      return

    for _ in range(timeout_seconds * 2):
      if await self._get_result_item_count(page) > 0:
        return
      await asyncio.sleep(0.5)

  async def _capture_screenshot(self, page, label: str) -> Optional[dict[str, str]]:
    if page is None:
      return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"schema_org_{label}_{timestamp}.png"

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

  async def validate(self, input_type: InputType, content: str) -> ValidationResult:
    """Punto de entrada seguro para concurrencia."""
    async with self._semaphore:
      return await self._validate_internal(input_type, content)

  async def _validate_internal(self, input_type: InputType, content: str) -> ValidationResult:
    """Lógica central de validación interactiva con stealth mejorado."""
    logger.info(f"Starting Schema.org validation for {input_type.value}...")
    browser = None
    display = None
    page = None
    current_url = self.target_url

    stealth = StealthConfig(
      headless=self._headless,
      proxy_server=self._proxy_server,
      proxy_bypass=self._proxy_bypass_list,
    )

    try:
      async with self._startup_lock:
        if not self._headless and sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
          try:
            from pyvirtualdisplay import Display
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ['DISPLAY'] = display.new_display_var
          except ImportError:
            logger.warning("pyvirtualdisplay not found.")

        browser = await uc.start(headless=stealth.headless_mode, browser_args=stealth.browser_args)

      # Inyectar stealth en about:blank antes de navegar al sitio objetivo
      page = await browser.get("about:blank")
      await stealth.inject(page)
      await stealth.simulate_mouse_move(page)
      await stealth.human_delay(0.5, 1.2)

      # Navegar al validador con el fingerprint ya activo
      page = await browser.get(self.target_url)
      current_url = self.target_url
      await stealth.human_delay(1.5, 3.0)
      await stealth.simulate_mouse_move(page)

      # 2. Interacción con los Tabs e Ingreso de Datos
      if input_type == InputType.HTML:
        logger.info("Switching to 'Fragmento de código' tab...")

        try:
          code_tab = await page.select("#new-test-code")
          await code_tab.click()
        except Exception as e:
          logger.warning(f"Error clickeando tab de código: {e}")

        await stealth.human_delay(1.0, 2.0)

        logger.info("Pegando contenido HTML masivo vía CDP...")
        # Focus via CDP query_selector + click nativo (sin evaluate)
        try:
          cm_input = await page.query_selector(".CodeMirror textarea")
          if cm_input:
            await cm_input.click()
        except Exception:
          pass
        await page.send(cdp_input.insert_text(text=content))
        await stealth.human_delay(1.0, 2.0)

      else:
        logger.info("Usando tab por defecto (URL) e ingresando dirección...")
        # Focus via CDP query_selector + click nativo (sin evaluate)
        try:
          url_input = await page.query_selector("#new-test-url-input")
          if url_input:
            await url_input.click()
        except Exception:
          pass
        await page.send(cdp_input.insert_text(text=content))
        await stealth.human_delay(1.0, 2.0)

      # 3. Ejecutar Prueba
      logger.info("Clickeando 'Ejecutar prueba'...")
      try:
        submit_btn = await page.select("#new-test-submit-button")
        await submit_btn.click()
      except Exception as e:
        logger.warning(f"Fallo click físico en submit, intentando query_selector: {e}")
        try:
          submit_btn = await page.query_selector("#new-test-submit-button")
          if submit_btn:
            await submit_btn.click()
        except Exception as e2:
          logger.warning(f"query_selector submit también falló: {e2}")

      await stealth.human_delay(1.5, 3.0)

      # 4. Esperar a que el dashboard realmente termine de renderizar
      logger.info("Esperando resolución del validador y render del dashboard...")
      items_count = await self._wait_for_results_ready(page, timeout_seconds=30)

      # 5. Interacción de capturas: Navegación de Elementos (Clic, Captura, Atrás)
      logger.info("Análisis completo. Extrayendo resultados e iterando elementos...")
      screenshots: list[dict[str, str]] = []

      # Captura general del dashboard principal
      main_screenshot = await self._capture_screenshot(page, "main_dashboard")
      if main_screenshot:
        screenshots.append(main_screenshot)

      logger.info(f"Se detectaron {items_count} elementos Schema.")

      for i in range(items_count):
        logger.info(f"Navegando al elemento {i+1} de {items_count}...")

        clicked = await self._click_result_item(page, i)
        if not clicked:
          logger.warning(f"No se pudo abrir el elemento {i}")
          continue

        detail_ready = await self._wait_for_item_detail(page, timeout_seconds=10)
        if not detail_ready:
          logger.warning(f"El detalle del elemento {i+1} no se renderizó a tiempo")
          continue

        # 5.2 Captura del detalle
        item_screenshot = await self._capture_screenshot(page, f"detail_item_{i+1}")
        if item_screenshot:
          screenshots.append(item_screenshot)

        await self._go_back_to_dashboard(page, timeout_seconds=10)

      # page.url es la propiedad nativa de nodriver (sin evaluate)
      current_url = page.url if hasattr(page, "url") else self.target_url
      final_html = await page.get_content()

      return ValidationResult(
        is_success=True,
        result_url=current_url,
        html_content=final_html,
        method_used="nodriver",
        screenshots=screenshots
      )

    except Exception as e:
      error_message = str(e)
      logger.error(f"Schema Validation failed: {error_message}")
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
        blocked_by_schema=False,
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
