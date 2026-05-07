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
import nodriver.cdp.input_ as cdp_input

from pydantic import BaseModel, Field

import nodriver as uc

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
  screenshots: list[dict[str, str]] = Field(default_factory=list)

class GoogleRichResultsEngine:
  # Candado estático a nivel de clase para evitar Race Conditions
  # al mutar la variable de entorno os.environ['DISPLAY']
  _startup_lock = asyncio.Lock()

  def __init__(
    self,
    proxy_server: Optional[str] = None,
    screenshots_dir: str = "storage/images",
    storage_url_prefix: str = "/storage/images",
    max_concurrent_tasks: int = 3 # Límite de navegadores simultáneos
  ):
    """
    Inicializa el motor de validación exclusivo con Nodriver.
    Nota: proxy_server debe ser un string con el formato "http://ip:port"
    """
    self._proxy_server = proxy_server
    self.target_url = "https://search.google.com/test/rich-results?hl=es"
    self.screenshots_dir = Path(screenshots_dir)
    self.storage_url_prefix = storage_url_prefix.rstrip("/")
    self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Semáforo para controlar cuánta RAM le exigimos al servidor
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
    target_path = self.screenshots_dir / filename

    try:
      await page.save_screenshot(str(target_path))
      return self._build_screenshot_artifact(filename)
    except Exception as exc:
      logger.warning("Could not save screenshot %s: %s", label, exc)
      return None

  async def validate(self, input_type: InputType, content: str) -> ValidationResult:
    """Punto de entrada seguro para concurrencia."""
    # El semáforo pone en cola las peticiones si llegan más de 'max_concurrent_tasks'
    async with self._semaphore:
      return await self._validate_internal(input_type, content)

  async def _validate_internal(self, input_type: InputType, content: str) -> ValidationResult:
    """Lógica central de validación."""
    logger.info(f"Starting validation for {input_type.value}...")
    browser = None
    display = None
    page = None

    try:
      # BLOQUE PROTEGIDO: Solo un proceso a la vez puede crear un display virtual y abrir Chrome
      # Esto evita que las peticiones paralelas se roben la variable os.environ['DISPLAY']
      async with self._startup_lock:
        if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
          try:
            from pyvirtualdisplay import Display
            logger.info("Starting Xvfb virtual display...")
            display = Display(visible=False, size=(1920, 1080))
            display.start()
            os.environ['DISPLAY'] = display.new_display_var
          except ImportError:
            logger.warning("pyvirtualdisplay not found. Browsing might fail on headless server.")

        browser_args = [
          "--window-size=1920,1080",
          "--no-sandbox",
          "--disable-blink-features=AutomationControlled"
        ]

        if self._proxy_server:
          browser_args.append(f"--proxy-server={self._proxy_server}")

        # Lanzamos el navegador heredando el entorno seguro
        browser = await uc.start(headless=False, browser_args=browser_args)

      # --- FIN DEL BLOQUE PROTEGIDO ---

      page = await browser.get(self.target_url)
      await asyncio.sleep(random.uniform(2.0, 4.0))

      # 3. Interacción con la UI de Google
      if input_type == InputType.HTML:
        logger.info("Switching to 'Código' tab...")

        # 3.1 Clic literal apuntando al contenedor div principal
        try:
          codigo_tab = await page.select("div[aria-controls='fmefR']")
          await codigo_tab.click()
        except Exception as e:
          logger.warning(f"No se encontró el aria-controls exacto, usando fallback de clases: {e}")
          codigo_tab = await page.select("div.ThdJC.kaAt2.Y8xidc.RPhebf.KKjvXb.j7nIZb")
          if codigo_tab:
            await codigo_tab.click()

        await asyncio.sleep(2)

        # 3.2 Enfocar el textarea para asegurar el cursor
        logger.info("Enfocando el textarea oculto de CodeMirror...")
        textarea = await page.select(".CodeMirror.cm-s-search-console-code-input textarea")
        await textarea.click()
        await asyncio.sleep(1)

        # 3.3 Simular evento de Pegado (Paste) a nivel del motor del navegador
        logger.info("Inyectando HTML masivo vía document.execCommand('insertText')...")
        await textarea.send_keys("<!--Proyecto-->")
        await page.send(cdp_input.insert_text(text=content))
        await asyncio.sleep(1)
        # 3.4 Asegurar validadores tecleando y borrando un espacio (Redundancia de seguridad)
        logger.info("Asegurando validación del framework enviando tecla de espacio...")

        logger.info("HTML injected and validated. Waiting 3 seconds...")
        await asyncio.sleep(2)

        # 3.5 Clic en el botón "probar código" (jsname oe2Hje)
        logger.info("Clicking 'probar código' button...")
        try:
          submit_btn = await page.select("div[jsname='oe2Hje']")
          await submit_btn.click()
        except Exception as e:
          logger.warning(f"Fallo el clic físico en el botón, usando JS fallback: {e}")
          await page.evaluate("""
                        () => {
                            const btn = document.querySelector("div[jsname='oe2Hje']");
                            if (btn) btn.click();
                        }
                    """)

      else:
        # Flujo de URL
        url_input = await page.select("input[type='url']")
        await url_input.send_keys(content)

        logger.info("URL typed. Waiting 3 seconds for Google event listeners to catch up...")
        await asyncio.sleep(3)

        # Seleccionamos el botón "probar URL" (jsname LZQqje)
        submit_btn = await page.select("div[jsname='LZQqje']")
        await submit_btn.click()
        logger.info("Clicked 'probar URL' button")

      # 4. Polling manual para captura de redirección (El modal "Probando URL...")
      logger.info("Polling for URL change indicating analysis completion...")
      current_url = ""

      # 80 iteraciones * 1.5s = 120 segundos máximo de espera
      for _ in range(80):
        current_url = await page.evaluate("window.location.href")

        # Detección temprana de bloqueos o captchas
        if "sorry" in current_url.lower():
          raise Exception("Google explicitly blocked the request (429/Captcha).")

        if "/result?id=" in current_url:
          break

        await asyncio.sleep(1.5)

      if "/result?id=" not in current_url:
        raise Exception("Timeout esperando que Google procese la URL. El modal no finalizó a tiempo.")

      # 5. Extracción de resultados
      logger.info("Analysis complete. Extracting final HTML...")
      await asyncio.sleep(2)
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
        screenshots=screenshots
      )

    except Exception as e:
      error_message = str(e)
      logger.error(f"Validation failed: {error_message}")
      screenshots: list[dict[str, str]] = []

      if page:
        screenshot = await self._capture_screenshot(page, "error")
        if screenshot:
          screenshots.append(screenshot)

      return ValidationResult(
        is_success=False,
        error_message=error_message,
        method_used="nodriver",
        blocked_by_google="block" in error_message.lower() or "captcha" in error_message.lower() or "sorry" in error_message.lower(),
        screenshots=screenshots
      )

    finally:
      # Limpieza segura de recursos
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
