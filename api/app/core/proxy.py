from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote, unquote, urlparse

from nodriver.core.util import ProxyForwarder


@dataclass(frozen=True)
class ProxySettings:
    raw_url: str
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    bypass_list: tuple[str, ...] = ()

    @property
    def has_auth(self) -> bool:
        return bool(self.username or self.password)

    @property
    def chrome_bypass_list(self) -> Optional[str]:
        if not self.bypass_list:
            return None
        return ";".join(self.bypass_list)

    @property
    def playwright_bypass_list(self) -> Optional[str]:
        if not self.bypass_list:
            return None
        return ",".join(self.bypass_list)

    def as_playwright_proxy(self) -> dict[str, str]:
        proxy: dict[str, str] = {"server": self.server}
        if self.username:
            proxy["username"] = self.username
        if self.password:
            proxy["password"] = self.password
        if self.playwright_bypass_list:
            proxy["bypass"] = self.playwright_bypass_list
        return proxy

    def create_nodriver_forwarder(self) -> ProxyForwarder | None:
        if not self.has_auth:
            return None
        return ProxyForwarder(self.raw_url)


def normalize_proxy_url(raw_proxy: Optional[str], *, default_scheme: str = "http") -> Optional[str]:
    raw_value = (raw_proxy or "").strip()
    if not raw_value:
        return None

    if "://" in raw_value:
        return raw_value

    parts = raw_value.split(":")
    if len(parts) >= 4:
        host = parts[0].strip()
        port = parts[1].strip()
        username = quote(parts[2].strip(), safe="")
        password = quote(":".join(parts[3:]).strip(), safe="")
        return f"{default_scheme}://{username}:{password}@{host}:{port}"

    if len(parts) == 2:
        host = parts[0].strip()
        port = parts[1].strip()
        return f"{default_scheme}://{host}:{port}"

    return f"{default_scheme}://{raw_value}"


def parse_no_proxy(raw_no_proxy: Optional[str]) -> tuple[str, ...]:
    if not raw_no_proxy:
        return ()
    return tuple(
        item.strip()
        for item in raw_no_proxy.split(",")
        if item and item.strip()
    )


def resolve_proxy_settings(
    raw_proxy: Optional[str],
    *,
    no_proxy: Optional[str] = None,
    default_scheme: str = "http",
) -> Optional[ProxySettings]:
    normalized_url = normalize_proxy_url(raw_proxy, default_scheme=default_scheme)
    if not normalized_url:
        return None

    parsed = urlparse(normalized_url)
    if not parsed.hostname:
        return None

    server = f"{parsed.scheme}://{parsed.hostname}"
    if parsed.port:
        server = f"{server}:{parsed.port}"

    return ProxySettings(
        raw_url=normalized_url,
        server=server,
        username=unquote(parsed.username) if parsed.username else None,
        password=unquote(parsed.password) if parsed.password else None,
        bypass_list=parse_no_proxy(no_proxy),
    )
