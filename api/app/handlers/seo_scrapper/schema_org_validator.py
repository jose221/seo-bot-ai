import asyncio
import json
import logging
import os
import random
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

import nodriver as uc
import nodriver.cdp.input_ as cdp_input

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
    proxy_server: Optional[str] = None,
    screenshots_dir: str = "storage/images/schema_org",
    storage_url_prefix: str = "/storage/images/schema_org",
    max_concurrent_tasks: int = 3
  ):
    """
    Inicializa el motor de validación para validator.schema.org.
    """
    self._proxy_server = proxy_server
    self.target_url = "https://validator.schema.org/"
    self.screenshots_dir = Path(screenshots_dir)
    self.storage_url_prefix = storage_url_prefix.rstrip("/")
    self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

  def _build_screenshot_artifact(self, filename: str) -> dict[str, str]:
    return {
      "path": str(self.screenshots_dir / filename),
      "url": f"{self.storage_url_prefix}/{filename}"
    }

  async def _get_result_item_count(self, page) -> int:
    try:
      count = await page.evaluate("""
                () => document.querySelectorAll('ul.mdl-list li.mdl-list__item').length
            """)
      return int(count or 0)
    except Exception:
      return 0

  async def _wait_for_results_ready(self, page, timeout_seconds: int = 30) -> int:
    dashboard_ready_streak = 0
    for _ in range(timeout_seconds):
      item_count = await self._get_result_item_count(page)
      if item_count > 0:
        return item_count

      try:
        dashboard_ready = await page.evaluate("""
                    () => Boolean(
                        document.querySelector('.sKfxWe-BeDmAc')
                        || document.querySelector('.mdl-list')
                        || document.body.innerText.includes('ELEMENTO')
                        || document.body.innerText.includes('ERRORES')
                        || document.body.innerText.includes('ADVERTENCIAS')
                    )
                """)
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
    try:
      clicked = await page.evaluate(
        f"""
                (() => {{
                    const items = Array.from(document.querySelectorAll('ul.mdl-list li.mdl-list__item'));
                    const target = items[{index}];
                    if (!target) return false;
                    target.click();
                    return true;
                }})()
            """,
      )
      return bool(clicked)
    except Exception as exc:
      logger.warning("Error al hacer click en el elemento %s: %s", index, exc)
      return False

  async def _wait_for_item_detail(self, page, timeout_seconds: int = 10) -> bool:
    for _ in range(timeout_seconds):
      try:
        has_back = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('button'))
                        .some((btn) => (btn.textContent || '').includes('arrow_back'))
                """)
      except Exception:
        has_back = False

      if has_back:
        return True
      await asyncio.sleep(0.5)
    return False

  async def _go_back_to_dashboard(self, page, timeout_seconds: int = 10) -> None:
    try:
      await page.evaluate("""
                () => {
                    const backButton = Array.from(document.querySelectorAll('button'))
                        .find((btn) => (btn.textContent || '').includes('arrow_back'));
                    if (backButton) backButton.click();
                }
            """)
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
    target_path = self.screenshots_dir / filename

    try:
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
    """Lógica central de validación interactiva."""
    logger.info(f"Starting Schema.org validation for {input_type.value}...")
    browser = None
    display = None
    page = None

    try:
      # 1. Configuración de Display Virtual seguro para concurrencia
      async with self._startup_lock:
        if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
          try:
            from pyvirtualdisplay import Display
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ['DISPLAY'] = display.new_display_var
          except ImportError:
            logger.warning("pyvirtualdisplay not found.")

        browser_args = [
          "--window-size=1920,1080",
          "--no-sandbox",
          "--disable-blink-features=AutomationControlled"
        ]

        if self._proxy_server:
          browser_args.append(f"--proxy-server={self._proxy_server}")

        browser = await uc.start(headless=False, browser_args=browser_args)

      # --- FIN DEL BLOQUE PROTEGIDO ---

      page = await browser.get(self.target_url)
      await asyncio.sleep(random.uniform(1.5, 3.0))

      # 2. Interacción con los Tabs e Ingreso de Datos
      if input_type == InputType.HTML:
        logger.info("Switching to 'Fragmento de código' tab...")

        try:
          code_tab = await page.select("#new-test-code")
          await code_tab.click()
        except Exception as e:
          logger.warning(f"Error clickeando tab de código: {e}")

        await asyncio.sleep(1.5)

        logger.info("Pegando contenido HTML masivo vía CDP...")
        # Aprovechamos el autofocus que notaste, pero reforzamos enfocando el textarea interno por seguridad
        await page.evaluate("""
                    () => {
                        const cmInput = document.querySelector('.CodeMirror textarea');
                        if(cmInput) cmInput.focus();
                    }
                """)
        await page.send(cdp_input.insert_text(text=content))
        await asyncio.sleep(1.5)

      else:
        logger.info("Usando tab por defecto (URL) e ingresando dirección...")
        # Para URL, el input nativo tiene autofocus, pero es buena práctica forzar el focus
        await page.evaluate("""
                    () => {
                        const urlInput = document.querySelector('#new-test-url-input');
                        if(urlInput) urlInput.focus();
                    }
                """)
        await page.send(cdp_input.insert_text(text=content))
        await asyncio.sleep(1.5)

      # 3. Ejecutar Prueba
      logger.info("Clickeando 'Ejecutar prueba'...")
      try:
        submit_btn = await page.select("#new-test-submit-button")
        await submit_btn.click()
      except Exception as e:
        logger.warning(f"Fallo click físico en submit, usando JS fallback: {e}")
        await page.evaluate("""
                    () => {
                        const btn = document.getElementById("new-test-submit-button");
                        if (btn) btn.click();
                    }
                """)

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

      current_url = await page.evaluate("window.location.href")
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
      if display:
        try:
          display.stop()
        except Exception as e:
          logger.warning(f"Error stopping Xvfb display: {e}")
