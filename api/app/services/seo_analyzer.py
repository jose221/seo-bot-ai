import json

import advertools as adv
import pandas as pd
import trafilatura
from bs4 import BeautifulSoup
from collections import Counter
from string import punctuation
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse


class SEOAnalyzer:
    """
    Motor de análisis SEO estático y técnico.
    Combina Advertools (Técnico), Trafilatura (Contenido) y BS4 (Estructura).
    """

    def __init__(self, url: str, html_content: Optional[str] = None):
        self.url = url
        self.domain = urlparse(url).netloc
        self.scheme = urlparse(url).scheme
        self.html = html_content
        self.soup = BeautifulSoup(html_content, 'lxml') if html_content else None

    def analyze_robots_txt(self) -> Dict[str, Any]:
        """
        Usa advertools para analizar el archivo robots.txt del dominio.
        """
        robots_url = f"{self.scheme}://{self.domain}/robots.txt"
        try:
            # advertools descarga y parsea el robots.txt en un DataFrame
            # output_file especifica donde guardar temporalmente, o podemos manejarlo en memoria
            df = adv.robotstxt_to_df(robots_url)

            if df.empty:
                return {"exists": False, "status": "No se encontró robots.txt o está vacío"}

            # Convertimos el DataFrame a un formato JSON amigable
            # Agrupamos por User-Agent para que sea legible
            # Procesar reglas por User-Agent
            grouped = {}
            current_ua = '*'  # Default user-agent

            for _, row in df.iterrows():
                directive = row['directive'].lower()
                content = row['content']

                if directive == 'user-agent':
                    current_ua = content
                    if current_ua not in grouped:
                        grouped[current_ua] = []
                elif directive not in ['sitemap']:
                    if current_ua not in grouped:
                        grouped[current_ua] = []
                    grouped[current_ua].append({
                        'directive': row['directive'],
                        'content': content
                    })

            response = {
                "exists": True,
                "url": robots_url,
                "sitemaps": df[df['directive'].str.lower() == 'sitemap']['content'].tolist(),
                "rules": grouped
            }

            return response
        except Exception as e:
            return {"exists": False, "error": str(e)}

    def analyze_onpage_structure(self) -> Dict[str, Any]:
        """
        Analiza etiquetas HTML críticas (Title, Description, H-tags).
        """
        if not self.soup:
            return {"error": "No HTML content provided"}

        # Title
        title = self.soup.title.string.strip() if self.soup.title else None
        title_length = len(title) if title else 0

        # Meta Description
        meta_desc_tag = self.soup.find('meta', attrs={'name': 'description'})
        meta_desc = meta_desc_tag.get('content').strip() if meta_desc_tag else None
        desc_length = len(meta_desc) if meta_desc else 0

        # Headers Hierarchy
        headers = {
            f"h{i}": len(self.soup.find_all(f"h{i}")) for i in range(1, 7)
        }

        # Links internos vs externos
        links = self.soup.find_all('a', href=True)
        internal_links = 0
        external_links = 0

        for link in links:
            href = link['href']
            if href.startswith('/') or self.domain in href:
                internal_links += 1
            elif href.startswith('http'):
                external_links += 1

        return {
            "title": {
                "content": title,
                "length": title_length,
                "status": "Good" if 30 <= title_length <= 60 else "Warning"
            },
            "meta_description": {
                "content": meta_desc,
                "length": desc_length,
                "status": "Good" if 120 <= desc_length <= 160 else "Warning"
            },
            "headers_structure": headers,
            "links_count": {
                "internal": internal_links,
                "external": external_links,
                "total": len(links)
            },
            "canonical": self._get_canonical()
        }

    def analyze_content_quality(self) -> Dict[str, Any]:
        """
        Usa Trafilatura para extraer texto limpio y analizar densidad de palabras.
        """
        if not self.html:
            return {}

        # Extraer solo el texto principal (sin menús, footer, ads)
        clean_text = trafilatura.extract(self.html) or ""

        if not clean_text:
            return {"word_count": 0, "status": "No main content found"}

        words = clean_text.split()
        word_count = len(words)

        # Análisis de Keywords (Top 10 palabras más usadas > 3 letras)
        clean_words = [
            w.lower().strip(punctuation)
            for w in words
            if len(w) > 3 and w.isalpha()
        ]

        # Filtramos stopwords básicos (aquí podrías agregar una lista más completa en español)
        stopwords = {'para', 'como', 'este', 'esta', 'pero', 'porque', 'sobre', 'todo', 'entre'}
        filtered_words = [w for w in clean_words if w not in stopwords]

        keyword_density = Counter(filtered_words).most_common(10)

        return {
            "word_count": word_count,
            "reading_time_minutes": round(word_count / 200, 2),  # Promedio 200 palabras/min
            "top_keywords": keyword_density,
            "thin_content": word_count < 300  # Flag si el contenido es muy pobre
        }

    def _get_canonical(self) -> Optional[str]:
        link = self.soup.find('link', rel='canonical')
        return link['href'] if link else None

    def analyze_structured_data(self) -> List[Dict[str, Any]]:
        """
        Busca y extrae bloques de JSON-LD, Microdata y RDFa.
        Usa la librería extruct para detectar esquemas definidos como atributos HTML o scripts.
        """
        if not self.html:
            return []

        extracted_schemas = []

        try:
            # Usar extruct para extraer todos los tipos de metadatos (JSON-LD, Microdata, RDFa)
            data = extruct.extract(
                self.html,
                base_url=self.url,
                syntaxes=['json-ld', 'microdata', 'rdfa'],
                uniform=True  # Normaliza la salida a formato dict estandar
            )

            # Combinar todos los formatos encontrados en una sola lista
            if 'json-ld' in data:
                extracted_schemas.extend(data['json-ld'])
            if 'microdata' in data:
                extracted_schemas.extend(data['microdata'])
            if 'rdfa' in data:
                extracted_schemas.extend(data['rdfa'])

        except Exception as e:
            print(f"⚠️ Error en extracción avanzada de schemas: {e}")
            # Fallback basico: extracción manual de JSON-LD si extruct falla
            if self.soup:
                scripts = self.soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        content = script.string
                        if content:
                            data = json.loads(content.strip())
                            extracted_schemas.append(data)
                    except:
                        pass

        return extracted_schemas

    def run_full_analysis(self) -> Dict[str, Any]:
        return {
            "technical_seo": self.analyze_robots_txt(),
            "onpage_seo": self.analyze_onpage_structure(),
            "content_seo": self.analyze_content_quality(),
            "schema_markup": self.analyze_structured_data()  # <--- NUEVO
        }
