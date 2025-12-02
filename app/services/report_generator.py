import re
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Union, Any

# Importamos tu modelo (ajusta la ruta según tu estructura)
from app.models.audit import AuditReport

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted
)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

class ReportGenerator:
    def __init__(self, audit: AuditReport):
        """
        :param audit: Instancia del modelo SQLModel AuditReport.
        """
        self.audit = audit

        # 1. Extracción segura de datos
        self.lh_data = self.audit.lighthouse_data or {}
        self.seo_data = self.audit.seo_analysis or {}
        self.ai_data = self.audit.ai_suggestions or {}

        # 2. Determinar URL y Dominio
        self.url = self.lh_data.get('url') or self.seo_data.get('onpage_seo', {}).get('canonical') or f"audit-{self.audit.id}"

        # Limpieza de dominio para nombre de carpeta
        clean_domain = self.url.replace('https://', '').replace('http://', '').split('/')[0]
        clean_domain = re.sub(r'[^\w\-_\.]', '_', clean_domain)

        # 3. Configurar rutas
        self.base_dir = Path("storage/reports") / clean_domain
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # 4. Inicializar estilos
        self._setup_pdf_styles()

    def _setup_pdf_styles(self):
        """Define los estilos visuales para el PDF."""
        self.styles = getSampleStyleSheet()

        # Estilo Justificado estándar
        self.styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=12, fontSize=10))

        # Estilo para Listas (Markdown bullets)
        self.styles.add(ParagraphStyle(
            name='MarkdownList',
            parent=self.styles['Normal'],
            leftIndent=20,      # Indentación a la izquierda
            firstLineIndent=0,  # Primera línea alineada
            spaceAfter=5,
            bulletIndent=10     # Indentación de la viñeta
        ))

        # Estilo para bloques de código
        self.styles.add(ParagraphStyle(name='CodeBlock', fontName='Courier', fontSize=8, leading=10,
                                       backColor=colors.whitesmoke, borderPadding=6, leftIndent=10))

        # Estilo para los números grandes de scores
        self.styles.add(ParagraphStyle(name='ScoreVal', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=14))

        # Títulos de sección
        self.styles.add(ParagraphStyle(name='SectionTitle', fontSize=14, fontName='Helvetica-Bold',
                                       spaceAfter=10, textColor=colors.HexColor("#2c3e50")))

    def _get_score_color(self, score: Union[float, None]):
        """Retorna color verde/naranja/rojo según el score."""
        if score is None: return colors.grey
        if score >= 90: return colors.HexColor("#27ae60") # Verde
        if score >= 50: return colors.HexColor("#f39c12") # Naranja
        return colors.HexColor("#c0392b") # Rojo

    def _parse_markdown_to_flowables(self, text: str) -> List:
        """
        Convierte el Markdown de la IA en elementos visuales PDF.
        INCLUYE PROTECCIÓN CONTRA TAGS HTML/XML MAL FORMADOS.
        """
        if not text: return []

        flowables = []
        lines = text.split('\n')
        in_code = False
        code_buff = []

        # Función auxiliar para limpiar texto antes de pasarlo a ReportLab
        def clean_xml(raw_text):
            # 1. Escapar caracteres XML reservados (<, >, &)
            # Esto convierte "<img>" en "&lt;img&gt;" para que se vea como texto y no rompa el parser
            safe_text = raw_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            # 2. Re-aplicar formato de negritas (Markdown ** -> ReportLab <b>)
            # Como ya escapamos los <, ahora podemos insertar nuestros propios tags <b> seguros
            return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_text)

        for line in lines:
            # --- Bloques de Código ---
            if line.strip().startswith("```"):
                if in_code:
                    # Cerrar bloque y renderizar
                    content = "\n".join(code_buff)
                    # Escapar contenido del código también
                    content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    flowables.append(Preformatted(content, self.styles["CodeBlock"]))
                    flowables.append(Spacer(1, 6))
                    code_buff = []
                    in_code = False
                else:
                    in_code = True
                continue

            if in_code:
                code_buff.append(line)
                continue

            # --- Texto Normal ---
            line = line.strip()
            if not line: continue

            # Detectar Headers
            if line.startswith("###"):
                txt = line.replace("###", "").strip()
                # Limpiamos el texto del título
                processed_txt = clean_xml(txt)
                flowables.append(Paragraph(f"<b><font size=11 color='#34495e'>{processed_txt}</font></b>", self.styles["Normal"]))

            elif line.startswith("##"):
                txt = line.replace("##", "").strip()
                processed_txt = clean_xml(txt)
                flowables.append(Spacer(1, 8))
                flowables.append(Paragraph(f"<b><font size=13 color='#2980b9'>{processed_txt}</font></b>", self.styles["Normal"]))
                flowables.append(Spacer(1, 4))

            # Detectar Listas
            elif line.startswith("- ") or line.startswith("* "):
                txt = line[2:]
                # Limpiamos el texto de la lista
                processed_txt = clean_xml(txt)
                flowables.append(Paragraph(f"&bull; {processed_txt}", self.styles["MarkdownList"]))

            # Párrafo Normal
            else:
                processed_txt = clean_xml(line)
                flowables.append(Paragraph(processed_txt, self.styles["Justify"]))

        return flowables

    def generate_pdf(self) -> str:
        filename = self.base_dir / f"Reporte_SEO_{self.timestamp}.pdf"
        doc = SimpleDocTemplate(str(filename), pagesize=LETTER, topMargin=40, bottomMargin=40)
        story = []

        # --- 1. ENCABEZADO ---
        story.append(Paragraph("Reporte de Auditoría SEO Integral", self.styles["Title"]))
        story.append(Paragraph(f"<b>URL Objetivo:</b> <font color='blue'>{self.url}</font>", self.styles["Normal"]))
        story.append(Paragraph(f"<b>ID Reporte:</b> {self.audit.id}", self.styles["Normal"]))
        story.append(Paragraph(f"<b>Generado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles["Normal"]))
        story.append(Spacer(1, 20))

        # --- 2. PUNTAJES ---
        scores = [
            self.audit.performance_score,
            self.audit.seo_score,
            self.audit.accessibility_score,
            self.audit.best_practices_score
        ]

        data_scores = [
            ['Performance', 'SEO', 'Accessibility', 'Best Practices'],
            [
                Paragraph(f"<font color={self._get_score_color(scores[0]).hexval()}>{scores[0] or 'N/A'}</font>",
                          self.styles["ScoreVal"]),
                Paragraph(f"<font color={self._get_score_color(scores[1]).hexval()}>{scores[1] or 'N/A'}</font>",
                          self.styles["ScoreVal"]),
                Paragraph(f"<font color={self._get_score_color(scores[2]).hexval()}>{scores[2] or 'N/A'}</font>",
                          self.styles["ScoreVal"]),
                Paragraph(f"<font color={self._get_score_color(scores[3]).hexval()}>{scores[3] or 'N/A'}</font>",
                          self.styles["ScoreVal"]),
            ]
        ]

        t = Table(data_scores, colWidths=[1.8 * inch] * 4)
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#ecf0f1")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # --- 3. CORE WEB VITALS ---
        story.append(Paragraph("Métricas Core Web Vitals & Rendimiento", self.styles["SectionTitle"]))

        lcp = self.audit.lcp
        cls = self.audit.cls
        fid = self.audit.fid

        vitals_data = [
            ['Métrica', 'Valor', 'Evaluación'],
            ['LCP (Largest Contentful Paint)', f"{lcp} ms" if lcp else "N/A",
             'Good' if lcp and lcp < 2500 else 'Poor/Analizar'],
            ['CLS (Layout Shift)', f"{cls}" if cls is not None else "N/A",
             'Good' if cls and cls < 0.1 else 'Poor/Analizar'],
            ['FID (First Input Delay)', f"{fid} ms" if fid else "N/A",
             'Good' if fid and fid < 100 else 'Poor/Analizar'],
        ]
        t_vitals = Table(vitals_data, colWidths=[3 * inch, 2 * inch, 2 * inch], hAlign='LEFT')
        t_vitals.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        story.append(t_vitals)
        story.append(Spacer(1, 20))

        # --- 4. DETALLES ON-PAGE ---
        onpage = self.seo_data.get('onpage_seo', {})
        headers = onpage.get('headers_structure', {})
        links = onpage.get('links_count', {})

        story.append(Paragraph("Estructura On-Page SEO", self.styles["SectionTitle"]))

        struct_data = [
            ['Elemento', 'Detalle', 'Estado / Cantidad'],
            ['Title Tag', (onpage.get('title', {}).get('content') or "")[:50] + "...",
             onpage.get('title', {}).get('status', '-')],
            ['Meta Description', (onpage.get('meta_description', {}).get('content') or "")[:50] + "...",
             onpage.get('meta_description', {}).get('status', '-')],
            ['Canonical', onpage.get('canonical', 'No definido'), 'Info'],
            ['H1 Tags', 'Debe ser exactamente 1', str(headers.get('h1', 0))],
            ['H2 Tags', 'Subtítulos principales', str(headers.get('h2', 0))],
            ['Total Links', f"Int: {links.get('internal', 0)} / Ext: {links.get('external', 0)}",
             str(links.get('total', 0))],
        ]

        t_struct = Table(struct_data, colWidths=[2 * inch, 3.5 * inch, 1.5 * inch], hAlign='LEFT')
        t_struct.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d5dbdb")),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        story.append(t_struct)
        story.append(PageBreak())

        # --- 5. ANÁLISIS IA ---
        model_name = self.ai_data.get('model', 'IA')
        story.append(Paragraph(f"Análisis Inteligente ({model_name})", self.styles["SectionTitle"]))

        analysis_text = self.ai_data.get('analysis', '')
        if analysis_text:
            story.extend(self._parse_markdown_to_flowables(analysis_text))
        else:
            story.append(
                Paragraph("<i>No se generó análisis cualitativo para este reporte.</i>", self.styles["Normal"]))

        story.append(PageBreak())

        # --- 6. SCHEMAS JSON-LD ---
        schemas = self.seo_data.get('schema_markup', [])

        story.append(Paragraph(f"Datos Estructurados ({len(schemas)} encontrados)", self.styles["SectionTitle"]))

        if not schemas:
            story.append(Paragraph("⚠️ <b>ADVERTENCIA:</b> No se detectaron bloques JSON-LD en la página.",
                                   self.styles["Normal"]))
        else:
            for idx, schema in enumerate(schemas, 1):
                s_type = schema.get('@type', 'Unknown Type')
                story.append(Paragraph(f"Schema #{idx}: <b>{s_type}</b>", self.styles["Normal"]))

                json_str = json.dumps(schema, indent=2, ensure_ascii=False)
                # Escapar también aquí por si acaso
                json_str = json_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                story.append(Preformatted(json_str, self.styles["CodeBlock"]))
                story.append(Spacer(1, 10))

        doc.build(story)
        return str(filename)

    def generate_excel(self) -> str:
        filename = self.base_dir / f"Analitica_{self.timestamp}.xlsx"

        # Helper para limpiar zonas horarias (Fix para Excel)
        def _clean_dt(dt):
            if not dt: return None
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja 1: Dashboard
            summary = {
                'ID': [str(self.audit.id)],
                'URL': [self.url],
                'Status': [self.audit.status.value],
                'Created At': [_clean_dt(self.audit.created_at)],
                'Completed At': [_clean_dt(self.audit.completed_at)],
                'Performance': [self.audit.performance_score],
                'SEO': [self.audit.seo_score],
                'Accessibility': [self.audit.accessibility_score],
                'Best Practices': [self.audit.best_practices_score],
                'LCP (ms)': [self.audit.lcp],
                'CLS': [self.audit.cls],
                'FID (ms)': [self.audit.fid]
            }
            pd.DataFrame(summary).to_excel(writer, sheet_name='Dashboard', index=False)

            # Hoja 2: SEO OnPage
            onpage = self.seo_data.get('onpage_seo', {})
            headers = onpage.get('headers_structure', {})

            flat_onpage = {
                'Canonical': [onpage.get('canonical')],
                'Title': [onpage.get('title', {}).get('content')],
                'Title Length': [onpage.get('title', {}).get('length')],
                'Meta Desc': [onpage.get('meta_description', {}).get('content')],
                'H1 Count': [headers.get('h1')],
                'Total Links': [onpage.get('links_count', {}).get('total')]
            }
            pd.DataFrame(flat_onpage).to_excel(writer, sheet_name='SEO OnPage', index=False)

            # Hoja 3: Schemas
            schemas = self.seo_data.get('schema_markup', [])
            if schemas:
                pd.json_normalize(schemas).to_excel(writer, sheet_name='Schemas_JSON-LD', index=False)
            else:
                pd.DataFrame({'Info': ['No schemas detected']}).to_excel(writer, sheet_name='Schemas_JSON-LD')

            # Hoja 4: Keywords
            keywords = self.seo_data.get('content_seo', {}).get('top_keywords', [])
            if keywords:
                try:
                    pd.DataFrame(keywords, columns=['Keyword', 'Frequency']).to_excel(writer, sheet_name='Keywords', index=False)
                except:
                    pass

            # Hoja 5: Technical
            tech = self.seo_data.get('technical_seo', {})
            if tech:
                pd.json_normalize(tech).to_excel(writer, sheet_name='Technical', index=False)

        return str(filename)

    def generate_all(self):
        return {
            "pdf_path": self.generate_pdf(),
            "xlsx_path": self.generate_excel()
        }