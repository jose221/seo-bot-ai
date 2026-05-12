"""
Módulo centralizado de stealth/anti-detección para nodriver (Chromium).

Proporciona:
- Pool de User-Agents actualizados (Chrome 134–136, Brave-like, Edge)
- Args de Chrome que minimizan señales de automatización
- Script JS que se inyecta vía CDP antes que el JS de la página
- Helper async para inyectar todo en un page de nodriver

Uso:
    from app.core.stealth import StealthConfig

    cfg = StealthConfig()                # perfil aleatorio
    browser = await uc.start(headless=cfg.headless, browser_args=cfg.browser_args)

    page = await browser.get("about:blank")
    await cfg.inject(page)              # inyecta fingerprint antes de navegar

    page = await browser.get(real_url)
"""
from __future__ import annotations

import logging
import random
from typing import List

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User-Agent pool  — Chrome 134-136 (May 2026 baseline)
# ---------------------------------------------------------------------------
_USER_AGENTS: List[str] = [
    # Windows — Chrome 136
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # Windows — Chrome 135
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    # macOS — Chrome 136
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # macOS — Chrome 135
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    # macOS M-series — Chrome 136
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    # Linux — Chrome 135
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    # Windows — Brave (reports as Chrome)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Brave/136",
    # Windows — Edge 135
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
]

# Hardcoded pairings: (hw_concurrency, device_memory_gb, platform)
_HARDWARE_PROFILES = [
    (8,  8,  "Win32"),
    (12, 8,  "Win32"),
    (16, 16, "Win32"),
    (8,  8,  "MacIntel"),
    (10, 16, "MacIntel"),
    (4,  4,  "Linux x86_64"),
    (8,  8,  "Linux x86_64"),
]

# Realistic viewport sizes (width, height)
_VIEWPORTS = [
    (1920, 1080),
    (1440, 900),
    (1536, 864),
    (1366, 768),
    (2560, 1440),
]


def _build_stealth_js(hw_concurrency: int, device_memory: int, platform: str, ua: str) -> str:
    """
    Builds the stealth script injected via
    CDP add_script_to_evaluate_on_new_document — runs BEFORE any page JS.

    Covers:
    - navigator.webdriver → undefined
    - navigator.plugins → realistic 5-element list
    - navigator.languages
    - navigator.hardwareConcurrency / deviceMemory / platform
    - window.chrome  (full runtime object Google checks)
    - Permissions API (notifications)
    - WebGL renderer — masks software renderer
    - canvas toDataURL — tiny per-session noise to vary fingerprint
    - screen colorDepth
    """
    # Small random offset for canvas noise — baked into the script at generation time
    r_noise = random.randint(1, 10)
    g_noise = random.randint(1, 10)
    b_noise = random.randint(1, 10)

    return f"""
(function() {{
  // --- navigator.webdriver ---
  Object.defineProperty(navigator, 'webdriver', {{
    get: () => undefined,
    configurable: true,
  }});

  // --- plugins (5 realistic entries) ---
  const makePlugin = (name, desc, fn, mt) => {{
    const plugin = Object.create(Plugin.prototype);
    Object.defineProperty(plugin, 'name',        {{ value: name }});
    Object.defineProperty(plugin, 'description', {{ value: desc }});
    Object.defineProperty(plugin, 'filename',    {{ value: fn }});
    const mime = Object.create(MimeType.prototype);
    Object.defineProperty(mime, 'type',          {{ value: mt }});
    Object.defineProperty(mime, 'suffixes',      {{ value: '' }});
    Object.defineProperty(mime, 'description',   {{ value: '' }});
    Object.defineProperty(mime, 'enabledPlugin', {{ value: plugin }});
    Object.defineProperty(plugin, '0',           {{ value: mime }});
    Object.defineProperty(plugin, 'length',      {{ value: 1 }});
    return plugin;
  }};
  const fakePlugins = [
    makePlugin('Chrome PDF Plugin', 'Portable Document Format', 'internal-pdf-viewer', 'application/x-google-chrome-pdf'),
    makePlugin('Chrome PDF Viewer', '', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', 'application/pdf'),
    makePlugin('Native Client', '', 'internal-nacl-plugin', 'application/x-nacl'),
    makePlugin('WebKit built-in PDF', '', 'WebKit built-in PDF', 'application/pdf'),
    makePlugin('Microsoft Edge PDF Viewer', '', 'edge-pdf-viewer', 'application/pdf'),
  ];
  const pluginArray = Object.create(PluginArray.prototype);
  fakePlugins.forEach((p, i) => Object.defineProperty(pluginArray, i, {{ value: p }}));
  Object.defineProperty(pluginArray, 'length', {{ value: fakePlugins.length }});
  pluginArray.item = (i) => fakePlugins[i] || null;
  pluginArray.namedItem = (name) => fakePlugins.find(p => p.name === name) || null;
  pluginArray.refresh = () => {{}};
  Object.defineProperty(navigator, 'plugins', {{ get: () => pluginArray, configurable: true }});
  Object.defineProperty(navigator, 'mimeTypes', {{ get: () => {{
    const arr = Object.create(MimeTypeArray.prototype);
    const mt = fakePlugins[0][0];
    Object.defineProperty(arr, '0', {{ value: mt }});
    Object.defineProperty(arr, 'length', {{ value: 1 }});
    return arr;
  }}, configurable: true }});

  // --- languages ---
  Object.defineProperty(navigator, 'languages', {{
    get: () => ['es-MX', 'es', 'en-US', 'en'],
    configurable: true,
  }});

  // --- hardware ---
  Object.defineProperty(navigator, 'hardwareConcurrency', {{ value: {hw_concurrency}, configurable: true }});
  Object.defineProperty(navigator, 'deviceMemory',        {{ value: {device_memory},  configurable: true }});
  Object.defineProperty(navigator, 'platform',            {{ value: '{platform}',     configurable: true }});

  // --- window.chrome (full object, Google checks this) ---
  if (!window.chrome) {{
    const handler = {{
      get(target, prop) {{
        if (prop === 'webstore') return undefined;
        return Reflect.get(target, prop);
      }}
    }};
    window.chrome = new Proxy({{
      app: {{
        isInstalled: false,
        InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }},
        RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }},
        getDetails: () => null,
        getIsInstalled: () => false,
        installState: () => 'not_installed',
        runningState: () => 'cannot_run',
      }},
      runtime: {{
        OnInstalledReason: {{ CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' }},
        OnRestartRequiredReason: {{ APP_UPDATE: 'app_update', GC: 'gc', OS_UPDATE: 'os_update' }},
        PlatformArch: {{ ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' }},
        PlatformNacl: {{ ARM: 'arm', MIPS: 'mips', X86_32: 'x86-32', X86_64: 'x86-64' }},
        PlatformOs: {{ ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' }},
        RequestUpdateCheckStatus: {{ NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' }},
        connect: () => {{}},
        sendMessage: () => {{}},
      }},
      csi: () => {{}},
      loadTimes: () => ({{
        commitLoadTime: Date.now() / 1000 - Math.random() * 0.5,
        connectionInfo: 'h2',
        finishDocumentLoadTime: 0,
        finishLoadTime: 0,
        firstPaintAfterLoadTime: 0,
        firstPaintTime: 0,
        navigationType: 'Other',
        npnNegotiatedProtocol: 'h2',
        requestTime: Date.now() / 1000 - Math.random(),
        startLoadTime: Date.now() / 1000 - Math.random() * 0.8,
        wasAlternateProtocolAvailable: false,
        wasFetchedViaSpdy: true,
        wasNpnNegotiated: true,
      }}),
    }}, handler);
  }}

  // --- Permissions API ---
  const originalQuery = window.navigator.permissions && window.navigator.permissions.query
    ? window.navigator.permissions.query.bind(window.navigator.permissions)
    : null;
  if (originalQuery) {{
    window.navigator.permissions.query = (parameters) => {{
      if (parameters.name === 'notifications') {{
        return Promise.resolve({{ state: Notification.permission, onchange: null }});
      }}
      return originalQuery(parameters);
    }};
  }}

  // --- WebGL: mask software renderer ---
  const getParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function(parameter) {{
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter.call(this, parameter);
  }};
  if (typeof WebGL2RenderingContext !== 'undefined') {{
    const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
      if (parameter === 37445) return 'Intel Inc.';
      if (parameter === 37446) return 'Intel Iris OpenGL Engine';
      return getParameter2.call(this, parameter);
    }};
  }}

  // --- Canvas fingerprint noise (tiny, per-session, consistent) ---
  const toDataURL = HTMLCanvasElement.prototype.toDataURL;
  HTMLCanvasElement.prototype.toDataURL = function(type, ...args) {{
    const ctx = this.getContext('2d');
    if (ctx) {{
      const imgData = ctx.getImageData(0, 0, this.width || 1, this.height || 1);
      if (imgData && imgData.data.length > 3) {{
        imgData.data[0] = Math.min(255, imgData.data[0] + {r_noise});
        imgData.data[1] = Math.min(255, imgData.data[1] + {g_noise});
        imgData.data[2] = Math.min(255, imgData.data[2] + {b_noise});
        ctx.putImageData(imgData, 0, 0);
      }}
    }}
    return toDataURL.call(this, type, ...args);
  }};

  // --- screen ---
  Object.defineProperty(screen, 'colorDepth', {{ value: 24, configurable: true }});
  Object.defineProperty(screen, 'pixelDepth',  {{ value: 24, configurable: true }});
}})();
""".strip()


# ---------------------------------------------------------------------------
# Chrome launch args
# ---------------------------------------------------------------------------
def _build_browser_args(
    viewport_w: int,
    viewport_h: int,
    user_agent: str,
    proxy_server: str | None = None,
    proxy_bypass: str | None = None,
    hide_window: bool = False,
) -> list[str]:
    args = [
        f"--window-size={viewport_w},{viewport_h}",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-ipc-flooding-protection",
        "--no-first-run",
        "--no-default-browser-check",
        "--password-store=basic",
        "--use-mock-keychain",
        "--disable-extensions",
        "--lang=es-MX",
        f"--user-agent={user_agent}",
    ]
    if proxy_server:
        args.append(f"--proxy-server={proxy_server}")
    if proxy_bypass:
        args.append(f"--proxy-bypass-list={proxy_bypass}")
    if hide_window:
        args.extend([
            "--window-position=-32000,-32000",
            "--start-minimized",
        ])
    return args


# ---------------------------------------------------------------------------
# StealthConfig — one instance per browser session
# ---------------------------------------------------------------------------
class StealthConfig:
    """
    Generates a random but internally-consistent browser fingerprint.

    Usage:
        cfg = StealthConfig()
        browser = await uc.start(headless=cfg.headless_mode, browser_args=cfg.browser_args)
        page = await browser.get("about:blank")
        await cfg.inject(page)
        page = await browser.get(real_url)
    """

    def __init__(
        self,
        headless: bool = False,
        proxy_server: str | None = None,
        proxy_bypass: str | None = None,
        hide_window: bool = False,
    ) -> None:
        self.user_agent = random.choice(_USER_AGENTS)
        hw_concurrency, device_memory, platform = random.choice(_HARDWARE_PROFILES)
        self.viewport_w, self.viewport_h = random.choice(_VIEWPORTS)
        self.headless_mode = headless

        self._stealth_js = _build_stealth_js(
            hw_concurrency=hw_concurrency,
            device_memory=device_memory,
            platform=platform,
            ua=self.user_agent,
        )
        self.browser_args = _build_browser_args(
            viewport_w=self.viewport_w,
            viewport_h=self.viewport_h,
            user_agent=self.user_agent,
            proxy_server=proxy_server,
            proxy_bypass=proxy_bypass,
            hide_window=hide_window,
        )

        logger.debug(
            "StealthConfig: ua=%s hw=%d mem=%d platform=%s viewport=%dx%d",
            self.user_agent[:60],
            hw_concurrency,
            device_memory,
            platform,
            self.viewport_w,
            self.viewport_h,
        )

    async def inject(self, page) -> None:
        """
        Injects the stealth script via CDP add_script_to_evaluate_on_new_document.
        Must be called on about:blank BEFORE navigating to the real URL.
        """
        import nodriver.cdp.page as cdp_page
        import nodriver.cdp.network as cdp_network
        try:
            await page.send(cdp_page.add_script_to_evaluate_on_new_document(
                source=self._stealth_js
            ))
        except Exception as exc:
            logger.warning("stealth: add_script_to_evaluate_on_new_document failed: %s", exc)

        # Override UA at the network layer too (handles fetch/XHR headers)
        try:
            await page.send(cdp_network.set_user_agent_override(
                user_agent=self.user_agent,
                accept_language="es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
                platform="MacIntel" if "Macintosh" in self.user_agent else "Win32",
            ))
        except Exception as exc:
            logger.warning("stealth: setUserAgentOverride failed: %s", exc)

    @staticmethod
    async def human_delay(min_s: float = 0.8, max_s: float = 2.2) -> None:
        """Sleep for a random human-like delay."""
        import asyncio
        await asyncio.sleep(random.uniform(min_s, max_s))

    @staticmethod
    async def simulate_mouse_move(page, x: int | None = None, y: int | None = None) -> None:
        """
        Dispatches a mousemove event at a random position to warm up mouse tracking.
        Uses nodriver's CDP input dispatch (no evaluate).
        """
        import nodriver.cdp.input_ as cdp_input
        import asyncio
        rx = x if x is not None else random.randint(200, 900)
        ry = y if y is not None else random.randint(100, 600)
        try:
            await page.send(cdp_input.dispatch_mouse_event(
                type_="mouseMoved",
                x=float(rx),
                y=float(ry),
            ))
            await asyncio.sleep(random.uniform(0.05, 0.15))
        except Exception:
            pass
