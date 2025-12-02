# Python
from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """
    Devuelve la URL con el esquema y dominio (sin ruta ni query).
    Ejemplos:
      - "https://www.pricetravel.com/index.html" -> "https://www.pricetravel.com"
      - "http://example.org/path/page" -> "http://example.org"
      - "www.example.com/page" -> "https://www.example.com"
    """
    if not url:
        raise ValueError("URL no puede estar vacía")

    parsed = urlparse(url)
    # Si no hay esquema, asumir https
    if not parsed.scheme:
        parsed = urlparse("https://" + url)

    # Construir y retornar el dominio con esquema
    domain = f"{parsed.scheme}://{parsed.netloc}"
    return domain
