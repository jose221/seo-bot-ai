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

from playwright.async_api import async_playwright, Page, Browser
import nodriver as uc

# Manejo de playwright-stealth
stealth_async = None
try:
  from playwright_stealth import stealth_async
except ImportError:
  try:
    from playwright_stealth import Stealth
    _stealth_instance = Stealth()
    stealth_async = _stealth_instance.apply_stealth_async
  except ImportError:
    pass

logger = logging.getLogger(__name__)

class InputType(str, Enum):
  URL = "url"
  HTML = "html"

class ValidationResult(BaseModel):
  is_success: bool
  result_url: Optional[str] = None
  html_content: Optional[str] = None
  error_message: Optional[str] = None
  method_used: str
  blocked_by_google: bool = False
  screenshots: list[dict[str, str]] = Field(default_factory=list)

class GoogleRichResultsEngine:
  def __init__(
    self,
    proxy_config: Optional[Dict[str, str]] = None,
    proxy_server: Optional[str] = None,
    screenshots_dir: str = "storage/images",
    storage_url_prefix: str = "/storage/images"
  ):
    self._proxy_config = proxy_config
    self._proxy_server = proxy_server
    self.target_url = "https://search.google.com/test/rich-results?hl=es"
    self.screenshots_dir = Path(screenshots_dir)
    self.storage_url_prefix = storage_url_prefix.rstrip("/")
    self.screenshots_dir.mkdir(parents=True, exist_ok=True)

  def _build_screenshot_artifact(self, filename: str) -> dict[str, str]:
    return {
      "path": str(self.screenshots_dir / filename),
      "url": f"{self.storage_url_prefix}/{filename}"
    }

  async def _capture_playwright_screenshot(self, page: Optional[Page], label: str) -> Optional[dict[str, str]]:
    if page is None:
      return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"rich_results_{label}_{timestamp}.png"
    target_path = self.screenshots_dir / filename

    try:
      await page.screenshot(path=str(target_path), full_page=True)
      return self._build_screenshot_artifact(filename)
    except Exception as exc:
      logger.warning("Could not save Playwright screenshot %s: %s", label, exc)
      return None

  async def _capture_nodriver_screenshot(self, page, label: str) -> Optional[dict[str, str]]:
    if page is None:
      return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"rich_results_{label}_{timestamp}.png"
    target_path = self.screenshots_dir / filename

    try:
      await page.save_screenshot(str(target_path))
      return self._build_screenshot_artifact(filename)
    except Exception as exc:
      logger.warning("Could not save Nodriver screenshot %s: %s", label, exc)
      return None

  async def _collect_playwright_block_state(
    self,
    page: Optional[Page],
    error_message: str
  ) -> ValidationResult:
    screenshots: list[dict[str, str]] = []
    screenshot = await self._capture_playwright_screenshot(page, "playwright_error")
    if screenshot:
      screenshots.append(screenshot)

    return ValidationResult(
      is_success=False,
      error_message=error_message,
      method_used="playwright",
      blocked_by_google="block" in error_message.lower() or "captcha" in error_message.lower(),
      screenshots=screenshots
    )

  async def validate(self, input_type: InputType, content: str) -> ValidationResult:
    logger.info("Starting validation via Playwright...")
    result = await self._run_playwright(input_type, content)

    if not result.is_success and "block" in str(result.error_message).lower():
      logger.warning("Playwright blocked by Google. Initiating Nodriver fallback...")
      return await self._run_nodriver(input_type, content)

    return result

  async def _run_playwright(self, input_type: InputType, content: str) -> ValidationResult:
    browser = None
    page = None
    try:
      async with async_playwright() as p:
        launch_args = {
          "headless": True,
          "args": ['--disable-blink-features=AutomationControlled', '--no-sandbox']
        }

        if self._proxy_config:
          launch_args["proxy"] = self._proxy_config

        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
          user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(10000)
        # Ampliamos el timeout global de navegación porque Google toma su tiempo analizando
        page.set_default_navigation_timeout(90000)

        if stealth_async:
          await stealth_async(page)

        response = await page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
        try:
          await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
          pass

        if (response and response.status == 429) or "sorry" in page.url.lower():
          screenshot = await self._capture_playwright_screenshot(page, "playwright_blocked")
          return ValidationResult(
            is_success=False,
            error_message="block: Google explicitly blocked the request (429/Captcha).",
            method_used="playwright",
            blocked_by_google=True,
            screenshots=[screenshot] if screenshot else []
          )

        result_url = await self._interact_with_ui_playwright(page, input_type, content)

        await page.wait_for_selector("div[data-record-element]", timeout=30000)
        final_html = await page.content()

        screenshots: list[dict[str, str]] = []
        screenshot = await self._capture_playwright_screenshot(page, "playwright_result")
        if screenshot:
          screenshots.append(screenshot)

        return ValidationResult(
          is_success=True,
          result_url=result_url,
          html_content=final_html,
          method_used="playwright",
          screenshots=screenshots
        )

    except Exception as e:
      logger.error(f"Playwright execution failed: {e}")
      return await self._collect_playwright_block_state(page, f"block: {str(e)}")

    finally:
      if browser:
        await browser.close()

  async def _interact_with_ui_playwright(self, page: Page, input_type: InputType, content: str) -> str:
    if input_type == InputType.HTML:
      await page.get_by_text("Código", exact=True).click()
      editor_area = page.locator(".CodeMirror")
      await editor_area.click()
      await page.keyboard.press("Control+A")
      await page.keyboard.press("Backspace")
      await page.keyboard.insert_text(content)
      await page.get_by_role("button", name="Probar código").click()
    else:
      url_input = page.locator("input[type='url']")
      await url_input.wait_for(state="visible", timeout=10000)

      await page.keyboard.press("Backspace")
      await self._type_text_like_keyboard(url_input, content)

      # Requisito explícito: Esperar mínimo 3 segundos
      logger.info("URL typed. Waiting 3 seconds before submission...")
      await asyncio.sleep(3)

      # Click explicitly using the provided DOM structure
      submit_btn = page.locator("div[role='button'][jsname='LZQqje']")
      await submit_btn.click()
      logger.info("Submit button clicked")

    logger.info("Waiting for Google processing modal to finish...")
    # Esperar a que la URL cambie al patrón result?id=. El timeout es alto porque el análisis tarda.
    await page.wait_for_url("**/test/rich-results/result?id=*", timeout=90000)
    return page.url

  async def _type_text_like_keyboard(self, url_input, text: str) -> None:
    for char in text:
      await url_input.type(char, delay=random.randint(50, 80))

  async def _run_nodriver(self, input_type: InputType, content: str) -> ValidationResult:
    browser = None
    display = None
    page = None

    try:
      if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
        try:
          from pyvirtualdisplay import Display
          display = Display(visible=False, size=(1920, 1080))
          display.start()
          os.environ['DISPLAY'] = display.new_display_var
        except ImportError:
          pass

      browser_args = [
        "--window-size=1920,1080",
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled"
      ]

      if self._proxy_server:
        browser_args.append(f"--proxy-server={self._proxy_server}")

      browser = await uc.start(headless=False, browser_args=browser_args)
      page = await browser.get(self.target_url)

      await asyncio.sleep(random.uniform(2.0, 4.0))

      if input_type == InputType.HTML:
        code_tab = await page.find("text=Código", best_match=True)
        await code_tab.click()
        await asyncio.sleep(1)

        content_json = json.dumps(content)
        await page.evaluate(f"""
                    () => {{
                        const cm = document.querySelector('.CodeMirror').CodeMirror;
                        const value = {content_json};
                        cm.setValue(value);
                    }}
                """)

        test_btn = await page.find("text=Probar código", best_match=True)
        await test_btn.click()
      else:
        url_input = await page.select("input[type='url']")
        await url_input.send_keys(content)

        # Requisito explícito: Esperar mínimo 3 segundos antes de accionar
        logger.info("URL typed in nodriver. Waiting 3 seconds...")
        await asyncio.sleep(3)

        # Usar el selector proporcionado jsname="LZQqje" en lugar de simular Enter
        submit_btn = await page.select("div[jsname='LZQqje']")
        await submit_btn.click()
        logger.info("Clicked 'probar URL' button in nodriver")

      # Polling manual para captura de redirección
      logger.info("Polling for URL change indicating analysis completion...")
      current_url = ""
      # Aumentamos los intentos de polling (80 iteraciones * 1.5s = 120 segundos máximo)
      # para dar tiempo a que el modal de "Probando la URL" desaparezca.
      for _ in range(80):
        current_url = await page.evaluate("window.location.href")
        if "/result?id=" in current_url:
          break
        await asyncio.sleep(1.5)

      if "/result?id=" not in current_url:
        raise Exception("Timeout esperando que Google procese la URL. El modal no finalizó a tiempo.")

      final_html = await page.get_content()
      screenshots: list[dict[str, str]] = []
      screenshot = await self._capture_nodriver_screenshot(page, "nodriver_result")
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
      logger.error(f"Nodriver fallback failed: {e}")
      screenshots: list[dict[str, str]] = []

      if page:
        screenshot = await self._capture_nodriver_screenshot(page, "nodriver_error")
        if screenshot:
          screenshots.append(screenshot)

      error_message = str(e)
      return ValidationResult(
        is_success=False,
        error_message=error_message,
        method_used="nodriver",
        blocked_by_google="block" in error_message.lower() or "captcha" in error_message.lower(),
        screenshots=screenshots
      )

    finally:
      if browser:
        browser.stop()
      if display:
        display.stop()
