#!/usr/bin/env python3
"""
build_report_pdf.py - Publication-Grade PDF Generator for SwayaLang Final Project Report
Uses ReportLab to render FINAL_PROJECT_REPORT.md into a high-quality IEEE/Academic style PDF.
Includes custom running headers/footers, cover page, styled tables, formula callouts, and diagrams.
"""

import os
import re
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count
    along with running header and running footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Suppress header and footer on cover page
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4A5568"))

        # Running Header
        self.drawString(54, 11 * inch - 36, "SWAYALANG: FINAL COMPILER DESIGN PROJECT REPORT")
        self.setFont("Helvetica", 8)
        self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "BCSE307P | REG NO: 24BCE0751")

        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Running Footer
        self.line(54, 45, 8.5 * inch - 54, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Vellore Institute of Technology — School of Computer Science & Engineering")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 32, page_str)

        self.restoreState()


def clean_markdown_inline(text: str) -> str:
    """Escapes XML special chars, cleans LaTeX artifacts, and translates markdown bold/italic/code to ReportLab tags."""
    # Translate common LaTeX symbols to Unicode math characters first
    text = text.replace(r"\times", "×")
    text = text.replace(r"\div", "÷")
    text = text.replace(r"\cdot", "·")
    text = text.replace(r"\alpha", "α")
    text = text.replace(r"\beta", "β")
    text = text.replace(r"\mu", "μ")
    text = text.replace(r"\sigma", "σ")
    text = text.replace(r"\tau", "τ")
    text = text.replace(r"\Delta", "Δ")
    text = text.replace(r"\Sigma", "Σ")
    text = text.replace(r"\sum", "Σ")
    text = text.replace(r"\le", "≤")
    text = text.replace(r"\ge", "≥")
    text = text.replace(r"\ne", "≠")
    text = text.replace(r"\in", "∈")
    text = text.replace(r"\notin", "∉")
    text = text.replace(r"\land", "∧")
    text = text.replace(r"\lor", "∨")
    text = text.replace(r"\cap", "∩")
    text = text.replace(r"\cup", "∪")
    text = text.replace(r"\emptyset", "∅")
    text = text.replace(r"\longrightarrow", "⟶")
    text = text.replace(r"\to", "→")
    text = text.replace(r"\approx", "≈")
    text = text.replace(r"\mathcal{O}", "O")
    text = text.replace(r"\mathcal{S}", "S")
    text = text.replace(r"\bar{r}", "r̄")
    text = text.replace(r"\dots", "...")
    text = text.replace(r"\max", "max")
    text = text.replace(r"\min", "min")

    # Clean \text{...} and \sqrt{...} and \frac{A}{B}
    text = re.sub(r"\\text\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\sqrt\{([^}]+)\}", r"√( \1 )", text)
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"( \1 / \2 )", text)

    # Strip math dollar signs
    text = text.replace("$$", "")
    text = text.replace("$", "")

    # Escape XML ampersands that aren't already part of an entity
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # Code: `code`
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" color="#0B1B3D" size="8"><b>\1</b></font>', text)
    # Bold: **bold** or __bold__
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # Italic: *italic* or _italic_
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)

    return text


def build_pdf(md_path: str, pdf_path: str):
    print(f"[*] Building publication-grade PDF from {md_path} -> {pdf_path}")
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file {md_path} not found.")

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    base_styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0B1B3D")    # Deep Navy
    SECONDARY = colors.HexColor("#00A896")  # Deep Teal
    ACCENT = colors.HexColor("#D97706")     # Amber
    DARK_TEXT = colors.HexColor("#1E293B")  # Slate 800
    MUTED_TEXT = colors.HexColor("#475569") # Slate 600
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Slate 50
    CODE_BG = colors.HexColor("#F1F5F9")    # Slate 100
    FORMULA_BG = colors.HexColor("#F8FAFC") # Soft formula box
    BORDER_COLOR = colors.HexColor("#CBD5E1")

    # Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        alignment=1, # Center
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=MUTED_TEXT,
        alignment=1,
        spaceAfter=24
    )

    meta_style = ParagraphStyle(
        "CoverMeta",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=DARK_TEXT,
        alignment=1
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=base_styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=11,
        spaceAfter=5,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        "Heading3_Custom",
        parent=base_styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=9.8,
        leading=13.5,
        textColor=DARK_TEXT,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=9.0,
        leading=13.0,
        textColor=DARK_TEXT,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-9,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=base_styles["Normal"],
        fontName="Courier",
        fontSize=7.8,
        leading=9.8,
        textColor=colors.HexColor("#0F172A")
    )

    formula_style = ParagraphStyle(
        "Formula_Custom",
        parent=base_styles["Normal"],
        fontName="Courier-Bold",
        fontSize=8.0,
        leading=10.2,
        textColor=colors.HexColor("#0F172A")
    )

    quote_style = ParagraphStyle(
        "Quote_Custom",
        parent=body_style,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#334155"),
        leftIndent=16,
        rightIndent=16,
        spaceBefore=5,
        spaceAfter=5
    )

    story = []

    # -------------------------------------------------------------
    # 1. FRONT COVER / TITLE PAGE
    # -------------------------------------------------------------
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("VELLORE INSTITUTE OF TECHNOLOGY", ParagraphStyle("VitHeader", fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=1, textColor=SECONDARY)))
    story.append(Paragraph("School of Computer Science & Engineering", ParagraphStyle("VitSub", fontName="Helvetica", fontSize=11, leading=15, alignment=1, textColor=MUTED_TEXT)))
    story.append(Spacer(1, 0.4 * inch))
    story.append(HRFlowable(width="80%", thickness=2, color=PRIMARY, spaceBefore=10, spaceAfter=20))
    story.append(Paragraph("SWAYALANG", title_style))
    story.append(Paragraph("A Domain-Specific Language, Optimizing Compiler & Execution Engine for Backtestable Stock Trading Strategies", subtitle_style))
    story.append(HRFlowable(width="80%", thickness=1, color=SECONDARY, spaceBefore=10, spaceAfter=25))
    story.append(Spacer(1, 0.3 * inch))

    cover_info = (
        "<b>Course:</b> BCSE307P — Compiler Design Laboratory<br/>"
        "<b>Project Phase:</b> Phase 3 — Final Implementation, Optimization & Testing<br/>"
        "<b>Evaluation:</b> Review 3 — Final Project Review<br/>"
        "<b>Author:</b> Swayam Shukla<br/>"
        "<b>Registration Number:</b> 24BCE0751<br/>"
        "<b>Faculty / Lab Instructor:</b> Department of Computer Science & Engineering<br/>"
        "<b>Date of Submission:</b> October 2026<br/>"
        "<b>Repository Status:</b> Production Ready (84/84 Automated Tests Passing, 100% Pass Rate)"
    )
    story.append(Paragraph(cover_info, meta_style))

    # Decorative status box on cover
    story.append(Spacer(1, 0.6 * inch))
    status_table_data = [
        ["Phase 1: Lexical, Recursive-Descent Parser & Typed AST", "PASSED / 100%"],
        ["Phase 2: Scoped Symbol Table, TAC Quadruples & Backtest Engine", "PASSED / 100%"],
        ["Phase 3: Multi-Pass TAC Optimizer, Risk Profiler & Web IDE", "PASSED / 100%"],
        ["Overall Test Suite (11 Test Modules in Pytest)", "84 / 84 Passed (100%)"]
    ]
    status_table = Table(status_table_data, colWidths=[4.0 * inch, 2.0 * inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 0), (0, -1), DARK_TEXT),
        ('TEXTCOLOR', (1, 0), (1, -1), SECONDARY),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(status_table)

    story.append(PageBreak())

    # -------------------------------------------------------------
    # 2. PARSE MARKDOWN BODY INTO REPORTLAB FLOWABLES
    # -------------------------------------------------------------
    lines = md_text.split("\n")
    i = 0
    total_lines = len(lines)

    # Skip initial markdown title and subtitle since we created a dedicated cover page
    while i < total_lines:
        line = lines[i].strip()
        if line.startswith("## Executive Summary") or line.startswith("## 1."):
            break
        i += 1

    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table(tbl_lines):
        if not tbl_lines:
            return None
        parsed_rows = []
        for raw_row in tbl_lines:
            cells = [c.strip() for c in raw_row.strip().strip("|").split("|")]
            # Filter out separator rows like |---|---|
            if all(re.match(r"^:?-+:?$", cell) for cell in cells if cell):
                continue
            parsed_rows.append(cells)

        if not parsed_rows:
            return None

        # Normalize column counts
        max_cols = max(len(r) for r in parsed_rows)
        normalized = []
        for r in parsed_rows:
            if len(r) < max_cols:
                r.extend([""] * (max_cols - len(r)))
            # Wrap text in Paragraph for auto cell wrapping
            wrapped = []
            for cell in r:
                clean_cell = clean_markdown_inline(cell)
                p = Paragraph(clean_cell, ParagraphStyle("TableCell", parent=body_style, fontSize=7.8, leading=10.0))
                wrapped.append(p)
            normalized.append(wrapped)

        col_width = (7.0 * inch) / max_cols
        t = Table(normalized, colWidths=[col_width] * max_cols)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7.8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4.5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4.5),
            ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
        ]))
        return t

    def flush_code(lines_list):
        if not lines_list:
            return None
        raw_code = "\n".join(lines_list)
        is_formula_box = any(marker in raw_code for marker in ["┌──", "└──", "Formula:", "Moving Average", "CAGR", "Drawdown", "Sharpe", "Sortino", "Portfolio State", "Three-Address Code"])

        escaped_code = raw_code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        if is_formula_box:
            p = Paragraph(f"<pre>{escaped_code}</pre>", formula_style)
            box = Table([[p]], colWidths=[7.0 * inch])
            box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), FORMULA_BG),
                ('LINELEFT', (0, 0), (0, -1), 3.5, SECONDARY),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 9),
                ('RIGHTPADDING', (0, 0), (-1, -1), 9),
            ]))
        else:
            p = Paragraph(f"<pre>{escaped_code}</pre>", code_style)
            box = Table([[p]], colWidths=[7.0 * inch])
            box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
                ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
        return box

    while i < total_lines:
        line = lines[i]
        stripped = line.strip()

        # Handle Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                # End of code block
                box = flush_code(code_lines)
                if box:
                    story.append(box)
                    story.append(Spacer(1, 5))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Handle Markdown Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            # End of table
            t = flush_table(table_lines)
            if t:
                story.append(t)
                story.append(Spacer(1, 6))
            table_lines = []
            in_table = False

        # Blank line
        if not stripped:
            i += 1
            continue

        # Horizontal Rule
        if stripped == "---":
            story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER_COLOR, spaceBefore=7, spaceAfter=7))
            i += 1
            continue

        # Headings
        if stripped.startswith("#### "):
            h_text = clean_markdown_inline(stripped[5:].strip())
            story.append(Paragraph(h_text, h3_style))
            i += 1
            continue
        elif stripped.startswith("### "):
            h_text = clean_markdown_inline(stripped[4:].strip())
            story.append(Paragraph(h_text, h2_style))
            i += 1
            continue
        elif stripped.startswith("## "):
            h_text = clean_markdown_inline(stripped[3:].strip())
            # For major chapters, insert a clean page break for academic visual balance
            if any(h_text.startswith(prefix) for prefix in ["3. ", "5. ", "8. ", "11. "]):
                story.append(PageBreak())
            story.append(Paragraph(h_text, h1_style))
            story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=5))
            i += 1
            continue
        elif stripped.startswith("# "):
            h_text = clean_markdown_inline(stripped[2:].strip())
            story.append(Paragraph(h_text, title_style))
            i += 1
            continue

        # Bullet List
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = clean_markdown_inline(stripped[2:].strip())
            p = Paragraph(f"• &nbsp; {bullet_text}", bullet_style)
            story.append(p)
            i += 1
            continue

        # Numbered List
        num_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if num_match:
            num = num_match.group(1)
            num_text = clean_markdown_inline(num_match.group(2))
            p = Paragraph(f"<b>{num}.</b> &nbsp; {num_text}", bullet_style)
            story.append(p)
            i += 1
            continue

        # Blockquote
        if stripped.startswith("> "):
            quote_text = clean_markdown_inline(stripped[2:].strip())
            p = Paragraph(quote_text, quote_style)
            box = Table([[p]], colWidths=[7.0 * inch])
            box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
                ('LINELEFT', (0, 0), (0, -1), 3, SECONDARY),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(box)
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Regular Body Paragraph
        p_text = clean_markdown_inline(stripped)
        story.append(Paragraph(p_text, body_style))
        i += 1

    # Cleanup any trailing table
    if in_table and table_lines:
        t = flush_table(table_lines)
        if t:
            story.append(t)

    # Embed generated presentation assets at end of report as Appendix Visual Evidence
    story.append(PageBreak())
    story.append(Paragraph("Appendix: Output Screenshots & Execution Evidence", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    evidence_items = [
        ("presentation_assets/benchmark_scaling_chart.png", "Empirical Execution Scaling & Latency Curve across Dataset Sizes (100 to 10,000 Bars)"),
        ("presentation_assets/terminal_step4_tac_opt.png", "Pass 1 & Pass 2 TAC Optimization Engine: Algebraic Simplification & Value Numbering CSE"),
        ("presentation_assets/terminal_step5_report.png", "Quantitative Financial Risk & Profiling Engine: Sharpe, Sortino, Drawdown, Profit Factor"),
        ("presentation_assets/terminal_step8_pytest.png", "Automated Pytest Validation Suite: 84 / 84 Tests Passing (100% Pass Rate)")
    ]

    for img_path, caption in evidence_items:
        if os.path.exists(img_path):
            try:
                img = Image(img_path, width=6.6 * inch, height=3.3 * inch)
                cap = Paragraph(f"<b>Figure:</b> {caption}", ParagraphStyle("Cap", parent=body_style, fontSize=7.8, textColor=MUTED_TEXT, alignment=1))
                box = Table([[img], [cap]], colWidths=[6.8 * inch])
                box.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
                    ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(KeepTogether([box, Spacer(1, 8)]))
            except Exception as e:
                print(f"[!] Warning: Could not embed image {img_path}: {e}")

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    file_size_kb = os.path.getsize(pdf_path) / 1024
    print(f"[+] Successfully generated {pdf_path} ({file_size_kb:.1f} KB)")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(base_dir, "FINAL_PROJECT_REPORT.md")
    pdf_file = os.path.join(base_dir, "FINAL_PROJECT_REPORT.pdf")
    build_pdf(md_file, pdf_file)
