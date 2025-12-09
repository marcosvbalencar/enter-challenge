"""
PDF Export Module

Generates a professional PDF from the advisory letter using fpdf2.
"""

import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF  # pyright: ignore[reportMissingModuleSource]
from loguru import logger


def _sanitize_text(text: str) -> str:
    """
    Sanitize text for latin-1 encoding used by Helvetica font.
    Replaces unsupported characters with ASCII equivalents.
    """
    replacements = {
        "\u2022": "-",   # bullet
        "\u2013": "-",   # en-dash
        "\u2014": "-",   # em-dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u00a0": " ",   # non-breaking space
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


class AdvisoryPDF(FPDF):
    """Custom PDF class for advisory letters with professional styling."""
    
    FONT = "Helvetica"
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)
        
    def header(self):
        # XP Logo/Brand
        self.set_font(self.FONT, "B", 28)
        self.set_text_color(251, 191, 36)  # XP Yellow
        self.cell(0, 10, "XP", align="C")
        self.ln(8)
        
        # Subtitle
        self.set_font(self.FONT, "", 10)
        self.set_text_color(107, 114, 128)  # Gray
        self.cell(0, 6, "ASSESSORIA DE INVESTIMENTOS", align="C")
        self.ln(8)
        
        # Separator line
        self.set_draw_color(251, 191, 36)
        self.set_line_width(0.8)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(10)
        
    def footer(self):
        self.set_y(-20)
        self.set_font(self.FONT, "", 8)
        self.set_text_color(107, 114, 128)
        
        # Page number
        self.cell(0, 5, f"Pagina {self.page_no()}/{{nb}}", align="C")
        self.ln(4)
        
        # Company info
        generation_date = datetime.now().strftime("%d/%m/%Y as %H:%M")
        self.cell(0, 5, f"Documento gerado em {generation_date}", align="C")
        self.ln(4)
        self.cell(0, 5, "XP Investimentos", align="C")


def _parse_markdown_line(line: str) -> tuple[str, str]:
    """
    Parse a markdown line and return (style, text).
    
    Returns:
        Tuple of (style_type, cleaned_text)
        style_type: 'h1', 'h2', 'h3', 'bold', 'normal', 'bullet', 'numbered'
    """
    stripped = line.strip()
    
    if stripped.startswith("### "):
        return ("h3", stripped[4:])
    elif stripped.startswith("## "):
        return ("h2", stripped[3:])
    elif stripped.startswith("# "):
        return ("h1", stripped[2:])
    elif stripped.startswith("- ") or stripped.startswith("* "):
        return ("bullet", stripped[2:])
    elif re.match(r"^\d+\.\s", stripped):
        match = re.match(r"^(\d+)\.\s(.*)$", stripped)
        if match:
            return ("numbered", f"{match.group(1)}. {match.group(2)}")
    elif stripped.startswith("---") or stripped.startswith("___"):
        return ("hr", "")
    elif stripped.startswith("|"):
        return ("table_row", stripped)
    
    return ("normal", stripped)


def _clean_markdown_formatting(text: str) -> str:
    """Remove markdown formatting like **bold** and preserve text."""
    # Remove bold markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # Remove italic markers
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    return _sanitize_text(text)


def _parse_table(lines: list[str]) -> list[list[str]]:
    """Parse markdown table lines into rows of cells."""
    rows = []
    for line in lines:
        if line.startswith("|") and not re.match(r"^\|[-:\s|]+\|$", line):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            rows.append(cells)
    return rows


def export_letter_to_pdf(
    letter_content: str,
    output_path: Path | str | None = None,
) -> Path:
    """
    Export the advisory letter to a professionally formatted PDF.
    
    Args:
        letter_content: The final letter content in markdown format
        output_path: Optional output path. Defaults to 'output/advisory_letter_YYYYMMDD.pdf'
        
    Returns:
        Path to the generated PDF file
    """
    logger.info("Generating PDF from advisory letter...")
    
    pdf = AdvisoryPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    lines = letter_content.split("\n")
    i = 0
    
    while i < len(lines):
        line = lines[i]
        style, text = _parse_markdown_line(line)
        
        if style == "table_row":
            # Collect all table lines
            table_lines = []
            while i < len(lines) and (lines[i].strip().startswith("|") or not lines[i].strip()):
                if lines[i].strip():
                    table_lines.append(lines[i])
                i += 1
            
            rows = _parse_table(table_lines)
            if rows:
                _render_table(pdf, rows)
            continue
            
        elif style == "h1":
            pdf.ln(5)
            pdf.set_font(AdvisoryPDF.FONT, "B", 18)
            pdf.set_text_color(17, 24, 39)
            pdf.multi_cell(0, 8, _clean_markdown_formatting(text))
            pdf.ln(3)
            
        elif style == "h2":
            pdf.ln(4)
            pdf.set_font(AdvisoryPDF.FONT, "B", 14)
            pdf.set_text_color(31, 41, 55)
            pdf.multi_cell(0, 7, _clean_markdown_formatting(text))
            # Underline
            pdf.set_draw_color(229, 231, 235)
            pdf.set_line_width(0.3)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(4)
            
        elif style == "h3":
            pdf.ln(3)
            pdf.set_font(AdvisoryPDF.FONT, "B", 12)
            pdf.set_text_color(55, 65, 81)
            pdf.multi_cell(0, 6, _clean_markdown_formatting(text))
            pdf.ln(2)
            
        elif style == "bullet":
            pdf.set_font(AdvisoryPDF.FONT, "", 11)
            pdf.set_text_color(31, 41, 55)
            pdf.set_x(25)
            pdf.multi_cell(0, 6, f"- {_clean_markdown_formatting(text)}")
            
        elif style == "numbered":
            pdf.set_font(AdvisoryPDF.FONT, "", 11)
            pdf.set_text_color(31, 41, 55)
            pdf.set_x(25)
            pdf.multi_cell(0, 6, _clean_markdown_formatting(text))
            
        elif style == "hr":
            pdf.ln(5)
            pdf.set_draw_color(209, 213, 219)
            pdf.set_line_width(0.3)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(5)
            
        elif style == "normal" and text:
            pdf.set_font(AdvisoryPDF.FONT, "", 11)
            pdf.set_text_color(31, 41, 55)
            
            # Handle inline bold text with mixed formatting
            if "**" in text:
                _render_mixed_text(pdf, text)
            else:
                pdf.multi_cell(0, 6, _sanitize_text(text))
            pdf.ln(2)
            
        elif not text:
            pdf.ln(3)
        
        i += 1
    
    # Determine output path
    if output_path is None:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"advisory_letter_{timestamp}.pdf"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    pdf.output(str(output_path))
    
    logger.info(f"PDF exported to: {output_path}")
    
    return output_path


def _render_table(pdf: FPDF, rows: list[list[str]]) -> None:
    """Render a markdown table as a PDF table."""
    if not rows:
        return
    
    pdf.ln(3)
    
    # Calculate column widths
    num_cols = len(rows[0])
    page_width = 170  # Available width
    col_widths = [page_width / num_cols] * num_cols
    
    # Adjust widths for typical financial tables
    if num_cols == 4:
        col_widths = [40, 50, 40, 40]  # Ativo, Valor, Desempenho, Acao
    
    # Header row
    pdf.set_font(AdvisoryPDF.FONT, "B", 9)
    pdf.set_fill_color(31, 41, 55)
    pdf.set_text_color(255, 255, 255)
    
    for j, cell in enumerate(rows[0]):
        align = "R" if j in (1, 2) else "L"
        pdf.cell(col_widths[j], 8, _clean_markdown_formatting(cell), border=0, align=align, fill=True)
    pdf.ln()
    
    # Data rows
    pdf.set_font(AdvisoryPDF.FONT, "", 9)
    pdf.set_text_color(31, 41, 55)
    
    for i, row in enumerate(rows[1:]):
        # Alternate row colors
        if i % 2 == 0:
            pdf.set_fill_color(249, 250, 251)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        for j, cell in enumerate(row):
            align = "R" if j in (1, 2) else "L"
            pdf.cell(col_widths[j], 7, _clean_markdown_formatting(cell), border=0, align=align, fill=True)
        pdf.ln()
    
    # Bottom border
    pdf.set_draw_color(229, 231, 235)
    pdf.set_line_width(0.3)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)


def _render_mixed_text(pdf: FPDF, text: str) -> None:
    """Render text with mixed bold and normal formatting."""
    # Split by bold markers
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    
    start_x = pdf.get_x()
    current_x = start_x
    line_height = 6
    max_width = 170
    
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font(AdvisoryPDF.FONT, "B", 11)
            clean_text = _sanitize_text(part[2:-2])
        else:
            pdf.set_font(AdvisoryPDF.FONT, "", 11)
            clean_text = _sanitize_text(part)
        
        if clean_text:
            text_width = pdf.get_string_width(clean_text)
            
            if current_x - 20 + text_width > max_width:
                # Wrap to next line
                pdf.ln(line_height)
                current_x = start_x
                pdf.set_x(current_x)
            
            pdf.cell(text_width, line_height, clean_text)
            current_x = pdf.get_x()
    
    pdf.ln(line_height)
