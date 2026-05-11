from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.config import settings


@dataclass(frozen=True)
class BrowserModeDefinition:
    code: str
    name: str
    description: str
    headless: bool
    available_web: bool = True
    available_desktop: bool = True


class BrowserModeRegistryService:
    _MODES: tuple[BrowserModeDefinition, ...] = (
        BrowserModeDefinition(
            code="web_chrome",
            name="Chrome view",
            description="Abre Chrome visible mientras corre la validación.",
            headless=False,
            available_web=False,
            available_desktop=True,
        ),
        BrowserModeDefinition(
            code="no_display",
            name="No display mode",
            description="Ejecuta el navegador sin interfaz visible.",
            headless=True,
            available_web=True,
            available_desktop=True,
        ),
    )

    def _is_available(self, mode: BrowserModeDefinition) -> bool:
        if settings.APP_MODE == "desktop":
            return mode.available_desktop
        return mode.available_web

    def list_available_modes(self) -> list[BrowserModeDefinition]:
        return [mode for mode in self._MODES if self._is_available(mode)]

    def get_mode(self, code: str) -> Optional[BrowserModeDefinition]:
        normalized_code = (code or "").strip()
        if not normalized_code:
            return None
        return next((mode for mode in self._MODES if mode.code == normalized_code), None)

    def resolve_mode(self, code: Optional[str]) -> Optional[BrowserModeDefinition]:
        normalized_code = (code or "").strip()
        if not normalized_code:
            return None

        mode = self.get_mode(normalized_code)
        if not mode:
            raise ValueError(f"Modo de navegador no soportado: {normalized_code}")
        if not self._is_available(mode):
            raise ValueError(
                f"Modo de navegador '{normalized_code}' no disponible cuando APP_MODE={settings.APP_MODE}"
            )
        return mode


_browser_mode_registry_service: BrowserModeRegistryService | None = None


def get_browser_mode_registry_service() -> BrowserModeRegistryService:
    global _browser_mode_registry_service
    if _browser_mode_registry_service is None:
        _browser_mode_registry_service = BrowserModeRegistryService()
    return _browser_mode_registry_service
