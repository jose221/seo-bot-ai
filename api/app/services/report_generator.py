import re
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Union, Any, Dict
import openpyxl # Importar openpyxl para estilos

# Importamos tu modelo (ajusta la ruta según tu estructura)
from app.models.audit import AuditReport

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted, Image
)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

class ReportGenerator:
    def __init__(self, audit: AuditReport):
        self.audit = audit

        # 1. Datos
        self.lh_data = self.audit.lighthouse_data or {}
        self.seo_data = self.audit.seo_analysis or {}
        self.ai_data = self.audit.ai_suggestions or {}

        # 2. URL y Directorios
        self.url = self.lh_data.get('url') or self.seo_data.get('onpage_seo', {}).get('canonical') or f"audit-{self.audit.id}"

        clean_domain = self.url.replace('https://', '').replace('http://', '').split('/')[0]
        clean_domain = re.sub(r'[^\w\-_\.]', '_', clean_domain)

        self.base_dir = Path("storage/reports") / clean_domain
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # 3. Estilos
        self._setup_pdf_styles()

    def _setup_pdf_styles(self):
        """Define estilos visuales profesionales y sobrios (Corporate/Executive)."""
        self.styles = getSampleStyleSheet()

        # Colores Corporativos Sobrios (Dark Navy & Grey scales)
        self.color_primary = colors.HexColor("#102A43")   # Azul marino oscuro profundo
        self.color_secondary = colors.HexColor("#334E68") # Azul acero
        self.color_accent = colors.HexColor("#D32F2F")    # Rojo oscuro para alertas
        self.color_bg_light = colors.HexColor("#F0F4F8")  # Gris azulado muy claro

        # Estilo Normal Justificado
        self.styles.add(ParagraphStyle(
            name='Justify',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            alignment=TA_JUSTIFY,
            leading=15,             # Interlineado más aireado
            fontSize=11,            # Letra más legible
            textColor=colors.HexColor("#243B53"),
            spaceAfter=8
        ))

        # Listas Markdown
        self.styles.add(ParagraphStyle(
            name='MarkdownList',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            leftIndent=24,
            firstLineIndent=0,
            spaceAfter=6,
            bulletIndent=12,
            leading=14,
            fontSize=11,
            textColor=colors.HexColor("#243B53")
        ))

        # Bloques de Código (JSON/Code) - Estilo terminal limpio
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            fontName='Courier',
            fontSize=9,
            leading=11,
            backColor=colors.HexColor("#F5F7FA"),
            borderPadding=10,
            leftIndent=6,
            rightIndent=6,
            textColor=colors.HexColor("#102A43"),
            spaceBefore=10,
            spaceAfter=10,
            borderColor=colors.HexColor("#D9E2EC"),
            borderWidth=0.5
        ))

        # Títulos
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=28,
            fontName='Helvetica-Bold',
            spaceBefore=40,
            spaceAfter=50,
            leading=36,
            textColor=self.color_primary,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='H1',
            fontSize=18,
            fontName='Helvetica-Bold',
            spaceBefore=24,
            spaceAfter=12,
            leading=22,
            textColor=self.color_primary,
            borderPadding=0,
            borderWidth=0
        ))

        self.styles.add(ParagraphStyle(
            name='H2',
            fontSize=15,
            fontName='Helvetica-Bold',
            spaceBefore=18,
            spaceAfter=10,
            leading=20,
            textColor=self.color_secondary
        ))

        self.styles.add(ParagraphStyle(
            name='H3',
            fontSize=13,
            fontName='Helvetica-BoldOblique',
            spaceBefore=12,
            spaceAfter=6,
            leading=16,
            textColor=colors.HexColor("#486581")
        ))

        # Estilos para celdas de tabla
        self.styles.add(ParagraphStyle(
            name='CellHeader',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=12
        ))

        self.styles.add(ParagraphStyle(
            name='CellBody',
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.HexColor("#102A43"),
            alignment=TA_LEFT,
            leading=13
        ))

        # Estilo para valores de scores
        self.styles.add(ParagraphStyle(
            name='ScoreVal',
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            alignment=TA_CENTER,
            leading=20
        ))

    def _get_score_color(self, score: Union[float, None]):
        if score is None: return colors.grey
        if score >= 90: return colors.HexColor("#107C10") # Verde corporativo
        if score >= 50: return colors.HexColor("#D83B01") # Naranja oscuro
        return colors.HexColor("#A80000") # Rojo oscuro

    def _extract_json_blocks(self, text: str) -> List[Dict]:
        """Extrae bloques de código JSON del texto markdown."""
        if not text: return []

        json_blocks = []

        # 1. Buscar bloques ```json
        pattern = r"```json\s*([\s\S]*?)\s*```"
        matches = re.findall(pattern, text)

        for match in matches:
            try:
                clean_json = match.strip()
                parsed = json.loads(clean_json)
                json_blocks.append(parsed)
            except json.JSONDecodeError:
                pass

        # 2. Si no hay bloques explicito, buscar bloques de codigo genericos
        if not json_blocks:
            pattern_gen = r"```\s*([\s\S]*?)\s*```"
            matches_gen = re.findall(pattern_gen, text)
            for match in matches_gen:
                try:
                    clean_json = match.strip()
                    if clean_json.startswith('{') or clean_json.startswith('['):
                        parsed = json.loads(clean_json)
                        json_blocks.append(parsed)
                except:
                    pass

        return json_blocks

    def _parse_markdown_to_flowables(self, text: str) -> List:
        """
        Parser Avanzado: Convierte Markdown a elementos PDF.
        Soporta: Headers, Listas, Bloques de Código y **TABLAS**.
        """
        if not text: return []

        flowables = []
        lines = text.split('\n')

        # Buffers para estados
        in_code = False
        code_buffer = []

        in_table = False
        table_buffer = []
        table_headers = []

        # --- Helpers ---
        def clean_and_format(raw_text):
            """Limpia XML y aplica formato inline (negritas, itálicas, código)."""
            # 1. Escapar XML básico
            safe = raw_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            # 2. Negritas: **texto** -> <b>texto</b>
            safe = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe)

            # 3. Código inline: `texto` -> <font name="Courier">texto</font>
            safe = re.sub(r'`(.*?)`', r'<font name="Courier" backColor="#f0f0f0">\1</font>', safe)

            return safe

        def flush_table(buffer):
            """Convierte el buffer de texto de tabla en una ReportLab Table bonita."""
            if not buffer: return None

            # Procesar filas
            data = []
            for row_str in buffer:
                # Eliminar barras iniciales/finales y separar
                # Ejemplo: "| Col1 | Col2 |" -> ["Col1", "Col2"]
                cols = [c.strip() for c in row_str.strip('|').split('|')]

                # Renderizar contenido de celda como Párrafo para permitir wrapping
                formatted_cols = []
                for idx, col in enumerate(cols):
                    style = self.styles['CellHeader'] if (len(data) == 0) else self.styles['CellBody']
                    formatted_cols.append(Paragraph(clean_and_format(col), style))

                data.append(formatted_cols)

            if not data: return None

            # Calcular ancho dinámico (asumiendo ancho página LETTER - margenes 0.4 inch cada lado)
            # Ancho disponible aprox 7.7 inch
            col_count = len(data[0])
            available_width = 7.7 * inch
            col_width = available_width / col_count # Distribuir equitativamente

            t = Table(data, colWidths=[col_width] * col_count)

            # Estilo visual de la tabla
            t_style = [
                ('BACKGROUND', (0, 0), (-1, 0), self.color_primary), # Header oscuro
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]

            # Filas alternas (Zebra striping)
            for i in range(1, len(data)):
                bg = self.color_bg_light if i % 2 == 0 else colors.white
                t_style.append(('BACKGROUND', (0, i), (-1, i), bg))

            t.setStyle(TableStyle(t_style))
            return t

        # --- Loop Principal ---
        for line in lines:
            stripped = line.strip()

            # 1. Detección de Bloques de Código
            if stripped.startswith("```"):
                if in_code:
                    # Fin del bloque
                    content = "\n".join(code_buffer)
                    # Escapar caracteres para preformatted
                    content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    flowables.append(Preformatted(content, self.styles["CodeBlock"]))
                    flowables.append(Spacer(1, 10))
                    code_buffer = []
                    in_code = False
                else:
                    # Inicio del bloque
                    # Si estábamos en tabla, cerrarla antes
                    if in_table:
                        t = flush_table(table_buffer)
                        if t: flowables.append(t)
                        flowables.append(Spacer(1, 10))
                        table_buffer = []
                        in_table = False

                    in_code = True
                continue

            if in_code:
                code_buffer.append(line)
                continue

            # 2. Detección de Tablas (Líneas que empiezan y terminan con |)
            # Regex básico: empieza con |, tiene contenido, termina con opcional |
            is_table_row = stripped.startswith('|') and '|' in stripped[1:]

            if is_table_row:
                # Detectar fila separadora Markdown (ej: |---|---|)
                if re.match(r'\|?[\s-]+\|[\s-]+\|?', stripped):
                    continue # Ignorar la línea separadora

                if not in_table:
                    in_table = True
                    table_buffer = []

                table_buffer.append(stripped)
                continue

            # Si no es tabla pero estábamos en una, FLUSH
            if in_table:
                t = flush_table(table_buffer)
                if t:
                    flowables.append(t)
                    flowables.append(Spacer(1, 12))
                table_buffer = []
                in_table = False

            if not stripped: continue

            # 3. Headers
            if stripped.startswith("#"):
                level = stripped.count('#')
                txt = clean_and_format(stripped.strip('# ').strip())

                if level == 1:
                    style = self.styles["H1"]
                elif level == 2:
                    style = self.styles["H2"]
                else:
                    style = self.styles["H3"]

                flowables.append(Paragraph(txt, style))

            # 4. Listas
            elif stripped.startswith("- ") or stripped.startswith("* "):
                txt = clean_and_format(stripped[2:])
                flowables.append(Paragraph(f"&bull; {txt}", self.styles["MarkdownList"]))

            # 5. Párrafo Normal
            else:
                txt = clean_and_format(stripped)
                flowables.append(Paragraph(txt, self.styles["Justify"]))

        # Limpieza final (por si el texto termina en código o tabla)
        if in_table and table_buffer:
            t = flush_table(table_buffer)
            if t: flowables.append(t)

        if in_code and code_buffer:
            content = "\n".join(code_buffer).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            flowables.append(Preformatted(content, self.styles["CodeBlock"]))

        return flowables

    def _extract_tables_from_text(self, text: str) -> List[pd.DataFrame]:
        """Extrae tablas Markdown de un texto y devuelve una lista de DataFrames."""
        if not text: return []

        tables = []
        lines = text.split('\n')
        current_table = []
        in_table = False
        headers = None

        for line in lines:
            stripped = line.strip()
            # Detectar fila de tabla
            if stripped.startswith('|') and '|' in stripped[1:]:
                # Detectar separador |---|---|
                if re.match(r'\|?[\s-]+\|[\s-]+\|?', stripped):
                    continue

                # Limpiar celdas
                cells = [c.strip() for c in stripped.strip('|').split('|')]

                if not in_table:
                    # Nueva tabla encontrada
                    in_table = True
                    headers = cells
                else:
                    # Fila de datos
                    if headers and len(cells) != len(headers):
                        if len(cells) < len(headers):
                            cells.extend([''] * (len(headers) - len(cells)))
                        else:
                            cells = cells[:len(headers)]
                    current_table.append(cells)
            else:
                if in_table:
                    # Fin de tabla
                    if headers:
                        try:
                            df = pd.DataFrame(current_table, columns=headers)
                            if not df.empty:
                                tables.append(df)
                        except Exception as e:
                            print(f"Error creando tabla excel: {e}")

                    in_table = False
                    current_table = []
                    headers = None

        if in_table and headers:
            try:
                df = pd.DataFrame(current_table, columns=headers)
                if not df.empty:
                    tables.append(df)
            except:
                pass

        return tables

    def _write_dfs_to_sheet(self, writer, dfs: List[pd.DataFrame], sheet_name: str):
        """Escribe múltiples dataframes en una misma hoja, uno debajo del otro."""
        startrow = 0
        for i, df in enumerate(dfs):
            try:
                df.to_excel(writer, sheet_name=sheet_name, startrow=startrow, index=False)
                startrow += len(df) + 3
            except Exception as e:
                print(f"Error escribiendo tabla en hoja {sheet_name}: {e}")

    # =========================================================================
    #  METODOS DE GENERACIÓN (Integrados)
    # =========================================================================

    def generate_pdf(self) -> str:
        """Genera el reporte individual de Auditoría."""
        filename = self.base_dir / f"Reporte_SEO_{self.timestamp}.pdf"
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=LETTER,
            topMargin=40,
            bottomMargin=40,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        story = []

        # --- Encabezado ---
        story.append(Paragraph("Reporte de Auditoría SEO Integral", self.styles["ReportTitle"]))

        # Meta info en una tabla invisible para alinear bien
        meta_data = [
            [Paragraph(f"<b>URL Objetivo:</b> {self.url}", self.styles["Justify"]),
             Paragraph(f"<b>ID:</b> {self.audit.id}", self.styles["Justify"])],
            [Paragraph(f"<b>Generado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles["Justify"]), ""]
        ]
        t_meta = Table(meta_data, colWidths=[4*inch, 3*inch])
        t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(t_meta)
        story.append(Spacer(1, 20))

        # --- Score Cards ---
        scores = [
            self.audit.performance_score, self.audit.seo_score,
            self.audit.accessibility_score, self.audit.best_practices_score
        ]

        # Crear celdas de colores para los scores
        def create_score_cell(label, score):
            color = self._get_score_color(score)
            return [
                Paragraph(label, self.styles["CellHeader"]),
                Paragraph(f"<font color='{color.hexval()}'>{score or 'N/A'}</font>", self.styles["ScoreVal"])
            ]

        # Tabla de scores simplificada
        data_scores = [
            ['Performance', 'SEO', 'Accessibility', 'Best Practices'],
            [
                Paragraph(f"<font color={self._get_score_color(scores[0]).hexval()}>{scores[0] or 'N/A'}</font>", self.styles["ScoreVal"]),
                Paragraph(f"<font color={self._get_score_color(scores[1]).hexval()}>{scores[1] or 'N/A'}</font>", self.styles["ScoreVal"]),
                Paragraph(f"<font color={self._get_score_color(scores[2]).hexval()}>{scores[2] or 'N/A'}</font>", self.styles["ScoreVal"]),
                Paragraph(f"<font color={self._get_score_color(scores[3]).hexval()}>{scores[3] or 'N/A'}</font>", self.styles["ScoreVal"]),
            ]
        ]

        t = Table(data_scores, colWidths=[1.8 * inch] * 4)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.color_primary),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # --- Análisis IA ---
        story.append(Paragraph(f"Análisis de Inteligencia Artificial", self.styles["H1"]))
        analysis_text = self.ai_data.get('analysis', '')
        if analysis_text:
            story.extend(self._parse_markdown_to_flowables(analysis_text))
        else:
            story.append(Paragraph("<i>No disponible.</i>", self.styles["Justify"]))

        story.append(PageBreak())

        # --- Schemas ---
        schemas = self.seo_data.get('schema_markup', [])
        story.append(Paragraph(f"Datos Estructurados ({len(schemas)})", self.styles["H1"]))

        if schemas:
            for idx, schema in enumerate(schemas, 1):
                s_type = schema.get('@type', 'Unknown')
                story.append(Paragraph(f"{idx}. {s_type}", self.styles["H3"]))

                # Convertir JSON a string formateado
                json_str = json.dumps(schema, indent=2, ensure_ascii=False)
                # Escapado simple manual porque va a Preformatted
                json_str = json_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Preformatted(json_str, self.styles["CodeBlock"]))
                story.append(Spacer(1, 10))

        doc.build(story)
        return str(filename)

    def generate_excel(self) -> str:
        filename = self.base_dir / f"Analitica_{self.timestamp}.xlsx"
        # (Tu lógica de Excel existente se mantiene igual)
        def _clean_dt(dt):
            return dt.replace(tzinfo=None) if dt and dt.tzinfo else dt

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            summary = {
                'ID': [str(self.audit.id)], 'URL': [self.url],
                'Created At': [_clean_dt(self.audit.created_at)],
                'Performance': [self.audit.performance_score]
            }
            pd.DataFrame(summary).to_excel(writer, sheet_name='Dashboard', index=False)

            schemas = self.seo_data.get('schema_markup', [])
            if schemas:
                pd.json_normalize(schemas).to_excel(writer, sheet_name='Schemas', index=False)

        return str(filename)

    def generate_all(self):
        return {"pdf_path": self.generate_pdf(), "xlsx_path": self.generate_excel()}

    # =========================================================================
    #  COMPARATIVOS (Benchmarking)
    # =========================================================================

    def generate_comparison_reports(self, comparison_data: Union[Dict, Any]) -> Dict[str, str]:
        # 1. Normalización
        if hasattr(comparison_data, 'model_dump'):
            data = comparison_data.model_dump()
        elif hasattr(comparison_data, 'dict'):
            data = comparison_data.dict()
        else:
            data = comparison_data

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        pdf_path = self.base_dir / f"Benchmark_Report_{ts}.pdf"
        xlsx_path = self.base_dir / f"Benchmark_Data_{ts}.xlsx"

        self._create_comparison_pdf(data, pdf_path)
        # Reutilizamos tu lógica de excel existente, o puedes pegarla aquí
        self._create_comparison_excel(data, xlsx_path)

        return {"pdf_path": str(pdf_path), "xlsx_path": str(xlsx_path)}

    def _create_comparison_pdf(self, data: dict, filename: Path):
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=LETTER,
            topMargin=40,
            bottomMargin=40,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        story = []

        base_url = data.get('base_url', 'Unknown URL')

        # Titulo
        story.append(Paragraph("Reporte de Benchmarking SEO", self.styles["ReportTitle"]))

        # Meta Info
        story.append(Paragraph(f"<b>Base:</b> <font color='#2980b9'>{base_url}</font>", self.styles["Justify"]))
        story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", self.styles["Justify"]))

        # Separator Line
        line_data = [[" "]]
        t_line = Table(line_data, colWidths=[7.5*inch], rowHeights=[5])
        t_line.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 2, self.color_secondary),
        ]))
        story.append(t_line)

        story.append(Spacer(1, 25))

        # Overall Summary
        overall = data.get('overall_summary', {})
        if overall:
            story.append(Paragraph("Resumen Ejecutivo", self.styles["H1"]))
            # Formateamos el resumen como una tabla pequeña para que se vea limpio
            summ_data = [
                ["Total Competidores", str(overall.get('total_competitors', 0))],
                ["Ranking Performance", str(overall.get('performance_rank', '-'))],
                ["Ranking SEO", str(overall.get('seo_rank', '-'))]
            ]
            t = Table(summ_data, colWidths=[2.5*inch, 2*inch], hAlign='LEFT')
            t.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

        # Markdown de IA (Aquí es donde la magia del nuevo parser actúa)
        ai_schema_md = data.get('ai_schema_comparison', '')
        if ai_schema_md:
            story.append(Spacer(1, 10))
            # Esto ahora detectará las tablas Markdown y las pintará bonitas
            story.extend(self._parse_markdown_to_flowables(ai_schema_md))
            story.append(PageBreak())

        # Comparaciones individuales
        comparisons = data.get('comparisons', [])
        for comp in comparisons:
            comp_url = comp.get('compare_url', 'N/A')
            story.append(Paragraph(f"VS: {comp_url}", self.styles["H1"]))

            # Tabla Cara a Cara
            scores = comp.get('performance', {}).get('scores', {})
            table_data = [['Métrica', 'Base', 'Competidor', 'Dif.']]

            metrics_map = {
                'performance_score': 'Performance',
                'seo_score': 'SEO',
                'accessibility_score': 'Accesibilidad',
                'best_practices_score': 'Best Practices'
            }

            for key, label in metrics_map.items():
                s_data = scores.get(key, {})
                base_val = s_data.get('base', 0)
                comp_val = s_data.get('compare', 0)
                diff = s_data.get('difference', 0)

                c_diff = "green" if diff >= 0 else "red"
                diff_char = "+" if diff >= 0 else ""

                table_data.append([
                    label,
                    f"{base_val:.1f}",
                    f"{comp_val:.1f}",
                    Paragraph(f"<font color='{c_diff}'><b>{diff_char}{diff:.1f}</b></font>", self.styles["CellBody"])
                ])

            t = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), self.color_primary),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('PADDING', (0,0), (-1,-1), 8),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

            # IA Analysis del competidor
            ai_analysis = comp.get('ai_analysis', '')
            if ai_analysis:
                story.append(Paragraph("Análisis Detallado", self.styles["H2"]))
                story.extend(self._parse_markdown_to_flowables(ai_analysis))

            story.append(PageBreak())

        doc.build(story)

    def _create_comparison_excel(self, data: dict, filename: Path):
        """Genera un Excel rico con múltiples hojas y tablas extraídas de la IA."""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 1. Hoja de Resumen (Dashboard)
            summary_data = []

            # Datos Generales
            base_url = data.get('base_url', 'Unknown')
            overall = data.get('overall_summary', {})

            summary_data.append({'Metric': 'Base URL', 'Value': base_url})
            summary_data.append({'Metric': 'Fecha Reporte', 'Value': datetime.now().strftime("%Y-%m-%d %H:%M")})
            summary_data.append({'Metric': 'Total Competidores', 'Value': overall.get('total_competitors', 0)})
            summary_data.append({'Metric': 'Ranking Performance', 'Value': overall.get('performance_rank', '-')})
            summary_data.append({'Metric': 'Ranking SEO', 'Value': overall.get('seo_rank', '-')})

            # Espacio
            summary_data.append({'Metric': '', 'Value': ''})

            # Tabla comparativa de scores principales
            comparisons = data.get('comparisons', [])
            for comp in comparisons:
                c_url = comp.get('compare_url', 'N/A')
                scores = comp.get('performance', {}).get('scores', {})

                # Performance
                p_s = scores.get('performance_score', {})
                summary_data.append({
                    'Metric': f"VS {c_url} - Performance",
                    'Value': f"Base: {p_s.get('base')} | Comp: {p_s.get('compare')} ({p_s.get('difference'):+})"
                })

                # SEO
                s_s = scores.get('seo_score', {})
                summary_data.append({
                    'Metric': f"VS {c_url} - SEO",
                    'Value': f"Base: {s_s.get('base')} | Comp: {s_s.get('compare')} ({s_s.get('difference'):+})"
                })

            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Dashboard', index=False)

            # Ajustar ancho de columnas en Dashboard
            try:
                worksheet = writer.sheets['Dashboard']
                worksheet.column_dimensions['A'].width = 30
                worksheet.column_dimensions['B'].width = 50
            except: pass

            # 2. Propuesta de Schemas (Global IA Comparison)
            ai_schema_txt = data.get('ai_schema_comparison', '')
            schema_tables = self._extract_tables_from_text(ai_schema_txt)
            proposed_schemas_global = self._extract_json_blocks(ai_schema_txt)

            if proposed_schemas_global:
                 prop_data = []
                 for idx, sc in enumerate(proposed_schemas_global, 1):
                    prop_data.append({
                        'Origen': 'Análisis Comparativo Global',
                        'Type': sc.get('@type', 'Unknown'),
                        'JSON-LD': json.dumps(sc, indent=2, ensure_ascii=False)
                    })
                 pd.DataFrame(prop_data).to_excel(writer, sheet_name='Propuesta Schemas', index=False)
                 try:
                     ws = writer.sheets['Propuesta Schemas']
                     ws.column_dimensions['C'].width = 70
                 except: pass

            if schema_tables:
                self._write_dfs_to_sheet(writer, schema_tables, 'Schema Analysis')

            # 3. Hojas por Competidor (Tablas de su análisis)
            for idx, comp in enumerate(comparisons, 1):
                comp_url = comp.get('compare_url', 'Unknown')
                # Limpiar nombre hoja (max 31 chars)
                sheet_name = f"Comp {idx}"

                # Extraer tablas del análisis individual
                ai_analysis_txt = comp.get('ai_analysis', '')
                comp_tables = self._extract_tables_from_text(ai_analysis_txt)

                if comp_tables:
                    self._write_dfs_to_sheet(writer, comp_tables, sheet_name)
                else:
                    pd.DataFrame({'Info': [f'No se detectaron tablas para {comp_url}']}).to_excel(writer, sheet_name=sheet_name, index=False)

