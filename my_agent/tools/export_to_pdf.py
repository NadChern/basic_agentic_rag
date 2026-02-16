"""PDF export tool for the agent."""

import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF


EXPORTS_DIR = Path(__file__).parent.parent.parent / "exports"
FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"


def export_to_pdf(content: str, title: str = "Sales Report") -> dict:
    """Export report content to a PDF file.

    Use this tool when the user explicitly requests a PDF, report export,
    or asks to "generate a report". The content should be the complete
    report text including any tables in markdown format.

    Args:
        content: The report content to export (supports markdown tables)
        title: Title for the PDF report

    Returns:
        dict with status and file_path to the generated PDF
    """
    try:
        EXPORTS_DIR.mkdir(exist_ok=True)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Register DejaVu fonts for Unicode support
        pdf.add_font("DejaVu", "", str(FONTS_DIR / "DejaVuSans.ttf"))
        pdf.add_font("DejaVu", "B", str(FONTS_DIR / "DejaVuSans-Bold.ttf"))

        # Header with title
        pdf.set_font("DejaVu", "B", 16)
        pdf.cell(0, 10, title, ln=True, align="C")

        # Timestamp
        pdf.set_font("DejaVu", "", 10)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.cell(0, 8, f"Generated: {timestamp}", ln=True, align="C")

        # Separator line
        pdf.ln(5)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

        # Render content with table support
        _render_content(pdf, content)

        # Save PDF
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = EXPORTS_DIR / filename

        pdf.output(str(filepath))

        return {
            "status": "success",
            "file_path": str(filepath),
            "message": f"PDF report saved to {filepath}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create PDF: {str(e)}"
        }


def _render_content(pdf: FPDF, content: str) -> None:
    """Render content to PDF, handling markdown tables."""
    # Split content into sections (table vs non-table)
    sections = _split_into_sections(content)

    for section_type, section_content in sections:
        if section_type == "table":
            _render_table(pdf, section_content)
        else:
            _render_text(pdf, section_content)


def _split_into_sections(content: str) -> list[tuple[str, str]]:
    """Split content into table and text sections."""
    sections = []
    lines = content.split("\n")
    current_section = []
    in_table = False

    for line in lines:
        is_table_line = _is_table_line(line)

        if is_table_line and not in_table:
            # Starting a table - save any accumulated text
            if current_section:
                text = "\n".join(current_section).strip()
                if text:
                    sections.append(("text", text))
                current_section = []
            in_table = True
            current_section.append(line)
        elif is_table_line and in_table:
            # Continuing a table
            current_section.append(line)
        elif not is_table_line and in_table:
            # Ending a table - save it
            if current_section:
                sections.append(("table", "\n".join(current_section)))
                current_section = []
            in_table = False
            current_section.append(line)
        else:
            # Regular text
            current_section.append(line)

    # Don't forget the last section
    if current_section:
        content_str = "\n".join(current_section).strip()
        if content_str:
            section_type = "table" if in_table else "text"
            sections.append((section_type, content_str))

    return sections


def _is_table_line(line: str) -> bool:
    """Check if a line is part of a markdown table."""
    stripped = line.strip()
    if not stripped:
        return False
    # Table lines start and contain pipe characters
    return "|" in stripped


def _render_text(pdf: FPDF, text: str) -> None:
    """Render plain text to PDF."""
    if not text.strip():
        return
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 6, text)
    pdf.ln(2)


def _render_table(pdf: FPDF, table_text: str) -> None:
    """Render a markdown table to PDF."""
    lines = [l.strip() for l in table_text.split("\n") if l.strip()]

    if not lines:
        return

    # Parse table rows
    rows = []
    for line in lines:
        # Skip separator lines (|---|---|)
        if re.match(r"^\|[-:\s|]+\|$", line):
            continue
        # Parse cells
        cells = [c.strip() for c in line.split("|")]
        # Remove empty first/last cells from leading/trailing pipes
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if cells:
            rows.append(cells)

    if not rows:
        return

    # Calculate column widths
    num_cols = max(len(row) for row in rows)
    page_width = pdf.w - 20  # 10mm margins on each side
    col_width = page_width / num_cols

    pdf.set_font("DejaVu", "", 10)
    pdf.ln(3)

    for i, row in enumerate(rows):
        # Pad row to have consistent column count
        while len(row) < num_cols:
            row.append("")

        # First row is header - make it bold
        if i == 0:
            pdf.set_font("DejaVu", "B", 10)
            pdf.set_fill_color(240, 240, 240)
            fill = True
        else:
            pdf.set_font("DejaVu", "", 10)
            fill = False

        # Calculate row height based on content
        row_height = 7

        for cell in row:
            x = pdf.get_x()
            y = pdf.get_y()
            # Draw cell border
            pdf.rect(x, y, col_width, row_height)
            if fill:
                pdf.set_xy(x, y)
                pdf.cell(col_width, row_height, "", fill=True)
                pdf.set_xy(x, y)
            # Add cell text with small padding
            pdf.set_xy(x + 1, y + 1)
            pdf.cell(col_width - 2, row_height - 2, cell[:30], align="L")  # Truncate long text
            pdf.set_xy(x + col_width, y)

        pdf.ln(row_height)

    pdf.ln(5)
