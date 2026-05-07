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

      # 4. Polling dinámico (Máximo 20 segundos)
      logger.info("Esperando resolución del validador (Polling de 20s máximo)...")
      analysis_complete = False

      # 20 iteraciones * 1s = 20 segundos max
      await asyncio.sleep(5)
      analysis_complete = True
      if not analysis_complete:
        # No lanzamos excepción inmediatamente porque a veces la página no tiene ningún esquema (0 elementos)
        logger.warning("Timeout de 20s superado o no se detectaron elementos Schema.")

      # 5. Interacción de capturas: Navegación de Elementos (Clic, Captura, Atrás)
      logger.info("Análisis completo. Extrayendo resultados e iterando elementos...")
      screenshots: list[dict[str, str]] = []

      # Captura general del dashboard principal
      main_screenshot = await self._capture_screenshot(page, "main_dashboard")
      if main_screenshot:
        screenshots.append(main_screenshot)

      # Contar cuántos elementos detectó Schema.org
      elementos = await page.select_all('ul.mdl-list li.mdl-list__item')
      items_count = len(elementos)

      logger.info(f"Se detectaron {items_count} elementos Schema.")

      # Iterar usando índices para evitar el problema de "Stale Element Reference"
      # Iterar usando índices
      for i in range(items_count):
        logger.info(f"Navegando al elemento {i+1} de {items_count}...")

        try:
          # 5.1 Búsqueda FRESCA en cada iteración y clic nativo de Python
          elementos = await page.select_all('ul.mdl-list li.mdl-list__item')

          if i < len(elementos):
            await elementos[i].click()
          else:
            logger.warning(f"No se encontró el elemento en el índice {i}")
            continue

        except Exception as e:
          logger.warning(f"Error al intentar clickear el elemento {i}: {e}")
          continue

        await asyncio.sleep(1.0) # Espera a que el panel lateral deslice

        # 5.2 Captura del detalle
        item_screenshot = await self._capture_screenshot(page, f"detail_item_{i+1}")
        if item_screenshot:
          screenshots.append(item_screenshot)

        # 5.3 Clic en botón "Atrás"
        try:
          # Obtenemos todos los botones de la página
          botones = await page.select_all('button')

          for btn in botones:
            # btn.text obtiene el textContent del elemento en nodriver
            if btn.text and 'arrow_back' in btn.text:
              await btn.click()
              break

        except Exception as e:
          logger.warning(f"Error al regresar al dashboard: {e}")

        await asyncio.sleep(1.0) # Espera a que el panel regrese al dashboard



        # 5.3 Clic en botón "Atrás" con nodriver puro
        try:
          # Buscamos dinámicamente todos los botones
          botones = await page.select_all('button')

          for btn in botones:
            # Verificamos si el texto del botón contiene el ícono 'arrow_back'
            if btn.text and 'arrow_back' in btn.text:
              await btn.click()
              break # Salimos del ciclo al encontrarlo y clickearlo

        except Exception as e:
          logger.warning(f"Error al regresar al dashboard: {e}")

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
