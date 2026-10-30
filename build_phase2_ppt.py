"""
build_phase2_ppt.py
Generates a 14-slide widescreen presentation for SwayaLang Phase 2 Review.
Preserves the dark-mode aesthetic of Phase 1 while embedding real screenshots
from demonstrate_phase2.py and the test suite.
"""

import os
from pathlib import Path
from PIL import Image

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# Colors & Theme Constants
# ---------------------------------------------------------------------------
COLOR_BG_DARK = RGBColor(11, 15, 23)       # #0b0f17
COLOR_CARD_BG = RGBColor(22, 27, 34)       # #161b22
COLOR_CARD_BG_ALT = RGBColor(21, 28, 40)   # #151c28
COLOR_BORDER = RGBColor(48, 54, 61)        # #30363d
COLOR_BORDER_CYAN = RGBColor(14, 116, 144) # #0e7490

COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_TEXT_PRIMARY = RGBColor(240, 246, 252)
COLOR_TEXT_MUTED = RGBColor(148, 163, 184) # #94a3b8
COLOR_TEXT_DIM = RGBColor(100, 116, 139)   # #64748b

COLOR_CYAN = RGBColor(56, 189, 248)        # #38bdf8
COLOR_NEON_CYAN = RGBColor(0, 242, 254)    # #00f2fe
COLOR_GREEN = RGBColor(34, 197, 94)        # #22c55e
COLOR_EMERALD = RGBColor(16, 185, 129)     # #10b981
COLOR_PURPLE = RGBColor(168, 85, 247)      # #a855f7
COLOR_AMBER = RGBColor(245, 158, 11)       # #f59e0b
COLOR_RED = RGBColor(239, 68, 68)          # #ef4444

TOTAL_SLIDES = 14
ASSETS_DIR = Path("presentation_assets")


def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_base_slide(prs):
    """Creates a blank slide with deep dark background."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Full screen background rectangle
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_BG_DARK
    bg.line.fill.background()
    return slide


def add_header(slide, category: str, title: str, subtitle: str, slide_num: int):
    """Adds standard header bar matching Phase 1 presentation."""
    # Category kicker
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8.0), Inches(0.35))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_CYAN

    # Slide number top right
    num_box = slide.shapes.add_textbox(Inches(10.5), Inches(0.4), Inches(2.0), Inches(0.35))
    tf_num = num_box.text_frame
    tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = f"{slide_num:02d} / {TOTAL_SLIDES:02d}"
    p_num.font.size = Pt(11)
    p_num.font.bold = True
    p_num.font.color.rgb = COLOR_TEXT_DIM

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.0), Inches(0.6))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE

    # Subtitle
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.5), Inches(0.4))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = subtitle
    p_sub.font.size = Pt(12.5)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED


def add_footer(slide, slide_num: int):
    """Adds bottom brand bar."""
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(8.0), Inches(0.3))
    tf_foot = footer_box.text_frame
    tf_foot.margin_left = tf_foot.margin_right = tf_foot.margin_top = tf_foot.margin_bottom = 0
    p_foot = tf_foot.paragraphs[0]
    p_foot.text = "SWAYALANG // COMPILER DESIGN LAB (BCSE307P) — REVIEW 2"
    p_foot.font.size = Pt(9.5)
    p_foot.font.color.rgb = COLOR_TEXT_DIM

    # Bottom right indicator
    num_box = slide.shapes.add_textbox(Inches(10.5), Inches(7.05), Inches(2.0), Inches(0.3))
    tf_num = num_box.text_frame
    tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = f"{slide_num:02d} / {TOTAL_SLIDES:02d}"
    p_num.font.size = Pt(9.5)
    p_num.font.bold = True
    p_num.font.color.rgb = COLOR_TEXT_DIM


def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER):
    """Adds a container card with subtle border."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
    return card


def add_badge(slide, left, top, width, height, text, bg_color, text_color=COLOR_WHITE):
    """Adds a rounded status badge."""
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    badge.fill.solid()
    badge.fill.fore_color.rgb = bg_color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = text
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = text_color
    return badge


def insert_image_fit(slide, img_path: Path, left, top, max_width, max_height):
    """Inserts an image preserving aspect ratio within bounding box."""
    if not img_path.is_file():
        print(f"Warning: image not found: {img_path}")
        return None

    with Image.open(img_path) as im:
        orig_w, orig_h = im.size

    aspect = orig_w / orig_h
    box_aspect = max_width / max_height

    if aspect > box_aspect:
        # Width constrained
        final_w = max_width
        final_h = max_width / aspect
    else:
        # Height constrained
        final_h = max_height
        final_w = max_height * aspect

    # Center horizontally and vertically within bounding box
    final_left = left + (max_width - final_w) / 2
    final_top = top + (max_height - final_h) / 2

    pic = slide.shapes.add_picture(
        str(img_path),
        Inches(final_left),
        Inches(final_top),
        width=Inches(final_w),
        height=Inches(final_h)
    )
    return pic


# ===========================================================================
# SLIDE BUILDERS
# ===========================================================================

def build_slide_1_title(prs):
    """Slide 1: Title & Review 2 Overview"""
    slide = add_base_slide(prs)

    # Top category
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(10.0), Inches(0.4))
    tf_cat = cat_box.text_frame
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = "COMPILER DESIGN LABORATORY · BCSE307P"
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_CYAN

    # Title
    t_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.05), Inches(6.5), Inches(0.9))
    tf_t = t_box.text_frame
    p_t = tf_t.paragraphs[0]
    p_t.text = "SwayaLang"
    p_t.font.size = Pt(40)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_WHITE

    # Subtitle
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.95), Inches(6.5), Inches(0.8))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = "A Domain-Specific Language & Compiler for Stock-Trading Strategies"
    p_sub.font.size = Pt(17)
    p_sub.font.bold = True
    p_sub.font.color.rgb = COLOR_CYAN

    # GitHub link
    git_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.75), Inches(6.5), Inches(0.35))
    tf_git = git_box.text_frame
    p_git = tf_git.paragraphs[0]
    p_git.text = "GitHub Repository: https://github.com/shuklaswayam/SwayaLang"
    p_git.font.size = Pt(11)
    p_git.font.color.rgb = COLOR_TEXT_MUTED

    # Badges
    add_badge(slide, 0.8, 3.25, 2.9, 0.35, "● PHASE 2: CORE IMPLEMENTATION", RGBColor(5, 150, 105), COLOR_WHITE)
    add_badge(slide, 3.8, 3.25, 2.5, 0.35, "● 63/63 TESTS PASSING", RGBColor(14, 116, 144), COLOR_WHITE)

    # Student metadata card
    add_card(slide, Inches(0.8), Inches(3.85), Inches(5.8), Inches(1.35))
    meta_box = slide.shapes.add_textbox(Inches(1.0), Inches(3.95), Inches(5.4), Inches(1.15))
    tf_meta = meta_box.text_frame
    tf_meta.word_wrap = True
    p1 = tf_meta.paragraphs[0]
    p1.text = "STUDENT                          REG. NO.                     INSTITUTION"
    p1.font.size = Pt(9.5)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_DIM

    p2 = tf_meta.add_paragraph()
    p2.text = "Swayam Shukla             24BCE0751             SCOPE, VIT Vellore"
    p2.font.size = Pt(12)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_WHITE
    p2.space_before = Pt(6)

    # Pipeline arrow card
    add_card(slide, Inches(0.8), Inches(5.4), Inches(5.8), Inches(1.2))
    pipe_box = slide.shapes.add_textbox(Inches(0.95), Inches(5.5), Inches(5.5), Inches(1.0))
    tf_pipe = pipe_box.text_frame
    tf_pipe.word_wrap = True
    pp1 = tf_pipe.paragraphs[0]
    pp1.text = "COMPLETE COMPILER PIPELINE OPERATIONAL"
    pp1.font.size = Pt(9.5)
    pp1.font.bold = True
    pp1.font.color.rgb = COLOR_EMERALD

    pp2 = tf_pipe.add_paragraph()
    pp2.text = "Source (.strat) → Tokens → AST → Scoped SymTab → Semantics → TAC Quadruples → Interpreter & Backtest"
    pp2.font.size = Pt(10.5)
    pp2.font.color.rgb = COLOR_TEXT_PRIMARY
    pp2.space_before = Pt(4)

    # Right Column: Code screenshot & Project Overview
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_code_momentum.png",
        left=7.0, top=0.8, max_width=5.5, max_height=3.1
    )

    add_card(slide, Inches(7.0), Inches(4.1), Inches(5.5), Inches(2.5))
    ov_box = slide.shapes.add_textbox(Inches(7.2), Inches(4.25), Inches(5.1), Inches(2.2))
    tf_ov = ov_box.text_frame
    tf_ov.word_wrap = True
    po0 = tf_ov.paragraphs[0]
    po0.text = "PHASE 2 REVIEW OBJECTIVES & DELIVERABLES"
    po0.font.size = Pt(11)
    po0.font.bold = True
    po0.font.color.rgb = COLOR_CYAN

    bullets = [
        "▸ Front-to-back compilation: .strat specification executes against real historical data.",
        "▸ Scoped Symbol Table: Parent-pointer tree with strict cross-strategy scope isolation.",
        "▸ Semantic Analysis: Two-type system (NUMERIC, BOOLEAN) with 4 compile-time error traps.",
        "▸ Intermediate Representation: Three-Address Code (TAC) with short-circuit branching.",
        "▸ Backtest Execution Engine: Quantitative proof of correctness (win rate, return %, drawdown).",
    ]
    for b in bullets:
        p = tf_ov.add_paragraph()
        p.text = b
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p.space_before = Pt(4)

    add_footer(slide, 1)


def build_slide_2_scope_contrast(prs):
    """Slide 2: Milestone Contrast (Phase 1 vs Phase 2)"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Milestone Comparison",
        "Phase 1 (Prototype) vs. Phase 2 (Core Implementation)",
        "Transforming a preliminary syntactic prototype into an end-to-end executable compiler toolchain.",
        2
    )

    # Top Summary Stat Cards
    stat_data = [
        ("Lexer & Parser", "Full LL(1) Grammar", "30 Token Types & AST Hierarchy"),
        ("Scoped Symbol Table", "Hierarchical Scopes", "Global Builtins + Strategy Scopes"),
        ("Semantic Validation", "Type & Invariant Checks", "NUMERIC/BOOLEAN & 4 Error Traps"),
        ("Execution Engine", "Backtest Simulation", "TAC Quadruples + 63 Passing Tests"),
    ]
    for i, (head, title, desc) in enumerate(stat_data):
        left = 0.8 + i * 2.95
        add_card(slide, Inches(left), Inches(1.85), Inches(2.8), Inches(1.05), COLOR_CARD_BG_ALT, COLOR_BORDER_CYAN)
        tb = slide.shapes.add_textbox(Inches(left + 0.15), Inches(1.95), Inches(2.5), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = head.upper()
        p0.font.size = Pt(8.5)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_CYAN
        p1 = tf.add_paragraph()
        p1.text = title
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.space_before = Pt(2)
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = COLOR_TEXT_MUTED
        p2.space_before = Pt(2)

    # 6 Comparison Dimension Cards (2 columns x 3 rows)
    dimensions = [
        (
            "01  Lexical Analysis",
            "Phase 1: Basic keyword/literal token scanning without line/col tracking.",
            "Phase 2: Maximal-munch DFA scanner, 30 token types, exact (line, col) tracking, LexError recovery with source position highlighting."
        ),
        (
            "02  Syntax Analysis & AST",
            "Phase 1: Single-strategy prototype parser handling basic ENTRY rule.",
            "Phase 2: Full LL(1) recursive-descent parser, multi-strategy files, indicator decls, ENTRY/EXIT/STOP_LOSS/TAKE_PROFIT rules, precedence climbing."
        ),
        (
            "03  Symbol Table Management",
            "Phase 1: Not implemented (grammar prototype only).",
            "Phase 2: Hierarchical parent-pointer symbol table (Global + Strategy child scopes), scope isolation guarantees, forward reference support."
        ),
        (
            "04  Semantic Analysis & Typing",
            "Phase 1: Not implemented.",
            "Phase 2: Two-type system (NUMERIC, BOOLEAN), indicator signature & period validation, compile-time detection of undeclared vars, /0, invalid periods."
        ),
        (
            "05  Intermediate Code (IR)",
            "Phase 1: Not implemented.",
            "Phase 2: Three-Address Code (TAC) Quadruples with temporaries (t0..tn), jump labels (L0..Ln), and boolean short-circuit branching."
        ),
        (
            "06  Execution Engine & Testing",
            "Phase 1: Manual testing, 27 prototype unit tests.",
            "Phase 2: Bar-by-bar interpreter, vector math (SMA/EMA/RSI), portfolio state machine, backtest report, 63 automated tests (100% pass rate)."
        ),
    ]

    for idx, (title, p1_desc, p2_desc) in enumerate(dimensions):
        col = idx % 2
        row = idx // 2
        c_left = 0.8 + col * 5.9
        c_top = 3.1 + row * 1.25

        add_card(slide, Inches(c_left), Inches(c_top), Inches(5.7), Inches(1.15))
        tb = slide.shapes.add_textbox(Inches(c_left + 0.2), Inches(c_top + 0.1), Inches(5.3), Inches(0.95))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_CYAN

        p_p1 = tf.add_paragraph()
        p_p1.text = f"✕ {p1_desc}"
        p_p1.font.size = Pt(8.5)
        p_p1.font.color.rgb = COLOR_TEXT_MUTED
        p_p1.space_before = Pt(2)

        p_p2 = tf.add_paragraph()
        p_p2.text = f"✓ {p2_desc}"
        p_p2.font.size = Pt(8.5)
        p_p2.font.bold = True
        p_p2.font.color.rgb = COLOR_TEXT_PRIMARY
        p_p2.space_before = Pt(2)

    add_footer(slide, 2)


def build_slide_3_pipeline_architecture(prs):
    """Slide 3: System Architecture & Staged Pipeline"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "System Architecture",
        "Compiler System Architecture: Staged Pipeline",
        "Strict module boundaries and unidirectional dataflow from source text to backtest analytics.",
        3
    )

    # 7 Stage Pipeline Cards
    stages = [
        ("01", "Lexer", "lexer.py", ".strat → Tokens", "COMPLETED"),
        ("02", "Parser", "parser.py", "Tokens → AST", "COMPLETED"),
        ("03", "Symbol Table", "symbol_table.py", "AST → Scoped Table", "PHASE 2"),
        ("04", "Semantic Analyzer", "semantic.py", "Type & Domain Checks", "PHASE 2"),
        ("05", "IR Generator", "ir.py", "AST → TAC Quadruples", "PHASE 2"),
        ("06", "Interpreter", "interpreter.py", "TAC + Data → Trades", "PHASE 2"),
        ("07", "Reporter", "interpreter.py", "Trades → Analytics", "PHASE 2"),
    ]

    card_w = 1.55
    spacing = 0.15
    for i, (num, name, file, flow, status) in enumerate(stages):
        left = 0.8 + i * (card_w + spacing)
        top = 2.0
        bg_col = COLOR_CARD_BG_ALT if status == "PHASE 2" else COLOR_CARD_BG
        border_col = COLOR_BORDER_CYAN if status == "PHASE 2" else COLOR_BORDER

        add_card(slide, Inches(left), Inches(top), Inches(card_w), Inches(2.2), bg_col, border_col)

        # Status badge top of card
        badge_col = RGBColor(14, 116, 144) if status == "PHASE 2" else RGBColor(5, 150, 105)
        add_badge(slide, left + 0.15, top + 0.15, card_w - 0.3, 0.25, status, badge_col)

        tb = slide.shapes.add_textbox(Inches(left + 0.1), Inches(top + 0.5), Inches(card_w - 0.2), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.alignment = PP_ALIGN.CENTER
        p0.text = num
        p0.font.size = Pt(20)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_CYAN

        p1 = tf.add_paragraph()
        p1.alignment = PP_ALIGN.CENTER
        p1.text = name
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.space_before = Pt(3)

        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        p2.text = file
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = COLOR_TEXT_MUTED
        p2.space_before = Pt(2)

        p3 = tf.add_paragraph()
        p3.alignment = PP_ALIGN.CENTER
        p3.text = flow
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = COLOR_EMERALD
        p3.space_before = Pt(4)

    # 3 Architecture Guarantees Cards across the bottom
    guarantees = [
        (
            "Strict Unidirectional Flow",
            "Each module consumes solely the output of the prior stage with zero cross-module state leakage or hidden dependencies."
        ),
        (
            "Headless Testability",
            "The parser operates on in-memory tokens; semantic analysis requires no market data; every phase is tested in absolute isolation."
        ),
        (
            "Compile-Time vs. Runtime Decoupling",
            "The symbol table records compile-time formulas and types; the interpreter binds dynamic prices and live rolling indicators."
        ),
    ]

    for j, (g_title, g_desc) in enumerate(guarantees):
        g_left = 0.8 + j * 3.95
        g_top = 4.6
        add_card(slide, Inches(g_left), Inches(g_top), Inches(3.8), Inches(2.1))

        tb = slide.shapes.add_textbox(Inches(g_left + 0.2), Inches(g_top + 0.2), Inches(3.4), Inches(1.7))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = f"GUARANTEE {j+1}: {g_title.upper()}"
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_CYAN

        p1 = tf.add_paragraph()
        p1.text = g_desc
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = COLOR_TEXT_PRIMARY
        p1.space_before = Pt(8)

    add_footer(slide, 3)


def build_slide_4_frontend_ast(prs):
    """Slide 4: Front-End Completion (Lexer & AST)"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Front-End Engineering",
        "Lexical Analysis & Recursive-Descent AST",
        "Deterministic maximal-munch scanner and LL(1) recursive-descent parser producing frozen AST nodes.",
        4
    )

    # Left Column: Technical details & Tokens screenshot
    add_card(slide, Inches(0.8), Inches(1.85), Inches(5.8), Inches(2.2))
    tb_left = slide.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.4), Inches(2.0))
    tf_l = tb_left.text_frame
    tf_l.word_wrap = True

    p0 = tf_l.paragraphs[0]
    p0.text = "FRONT-END ARCHITECTURE & DESIGN HIGHLIGHTS"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    bullets = [
        "• 30 Distinct Token Types: Keywords, price fields (CLOSE, OPEN, PRICE), operators, and delimiters.",
        "• Exact Source Position: Every token retains (line, column) origin for precise diagnostics.",
        "• Precedence Climbing: Resolves arithmetic (*, /, +, -) and boolean (AND, OR) without left-recursion.",
        "• Immutable Typed AST: Built with Python @dataclass(frozen=True) rooted at ASTNode base.",
    ]
    for b in bullets:
        p = tf_l.add_paragraph()
        p.text = b
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p.space_before = Pt(4)

    # Step 1 Tokens Screenshot (bottom left)
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_step1_tokens.png",
        left=0.8, top=4.2, max_width=5.8, max_height=2.65
    )

    # Right Column: Step 2 AST Screenshot (right side)
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_step2_ast.png",
        left=6.9, top=1.85, max_width=5.6, max_height=5.0
    )

    add_footer(slide, 4)


def build_slide_5_symbol_table(prs):
    """Slide 5: Scoped Symbol Table Management"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Symbol Table Management",
        "Hierarchical Scopes & Lexical Scoping Guarantees",
        "Parent-pointer tree enforcing cross-strategy scope isolation and built-in symbol resolution.",
        5
    )

    # Left Column: Scoping architecture explanation
    add_card(slide, Inches(0.8), Inches(1.85), Inches(5.8), Inches(5.0))
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.4), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "LEXICAL SCOPING MODEL & HIERARCHY"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    sections = [
        ("Root Global Scope", "Pre-populated with built-in indicator signatures: SMA(series, period), EMA(series, period), RSI(series, period), and 7 price series identifiers (CLOSE, OPEN, HIGH, LOW, VOLUME, PRICE, ENTRY_PRICE)."),
        ("Strategy Child Scopes", "Each STRATEGY block instantiates its own dedicated Scope object pointing to Global as its parent. Stores declared indicators (e.g. sma_20, rsi_14)."),
        ("Scope Isolation Guarantee", "Scope lookup walks strictly outward to the parent Global scope, never sideways to siblings. Identifiers in Strategy A cannot leak into Strategy B."),
        ("Forward References Supported", "A pre-pass over indicator declarations populates strategy symbols before rule analysis, allowing rules to reference indicators declared anywhere in the block."),
    ]

    for title, desc in sections:
        p_t = tf.add_paragraph()
        p_t.text = f"▸ {title}"
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE
        p_t.space_before = Pt(8)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = COLOR_TEXT_PRIMARY
        p_d.space_before = Pt(2)

    # Right Column: Screenshot Step 3 Symbol Table
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_step3_symbol_table.png",
        left=6.9, top=1.85, max_width=5.6, max_height=5.0
    )

    add_footer(slide, 5)


def build_slide_6_semantic_analysis(prs):
    """Slide 6: Semantic Analysis & Type Consistency"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Semantic Analysis",
        "Static Type Inference & Indicator Validation",
        "Statically verifying domain constraints and expression type consistency before code generation.",
        6
    )

    cards = [
        (
            "01  Two-Type System",
            "NUMERIC vs. BOOLEAN",
            "• NUMERIC: Price series, scalar numbers, and arithmetic (+, -, *, /).\n"
            "• BOOLEAN: Relational comparisons (>, <, >=, <=, ==) and logical operators (AND, OR).\n"
            "• Strict Type Safety: Prevents illegal expressions such as (CLOSE > 100) + 5 at compile time."
        ),
        (
            "02  Indicator Signature Checks",
            "Arity & Argument Type Enforcement",
            "• Function Existence: Must resolve to BUILTIN_FUNC in Global Scope (SMA, EMA, RSI).\n"
            "• Arity Verification: Requires exactly 2 arguments (series, period).\n"
            "• Type Integrity: Arg 1 must be a PRICE_SERIES; Arg 2 must be an integer literal > 0."
        ),
        (
            "03  Identifier Resolution",
            "Hierarchical Scope Walking",
            "• Every variable reference in condition trees is resolved against strategy Scope.\n"
            "• Unresolved identifiers raise immediate SemanticError with exact source coordinates.\n"
            "• Shadowing Prevention: Reserved series cannot be overridden as variable names."
        ),
        (
            "04  Static Dead-Code Warnings",
            "Unused Indicator Tracking",
            "• After AST traversal, any declared indicator with zero symbol lookups is flagged.\n"
            "• Emits non-fatal compile-time warnings: [WARNING] Unused indicator 'x'.\n"
            "• Preserves compilation pipeline while notifying the trader of redundant computations."
        ),
    ]

    for idx, (title, sub, body) in enumerate(cards):
        col = idx % 2
        row = idx // 2
        c_left = 0.8 + col * 5.9
        c_top = 1.9 + row * 2.5

        add_card(slide, Inches(c_left), Inches(c_top), Inches(5.7), Inches(2.35))
        tb = slide.shapes.add_textbox(Inches(c_left + 0.25), Inches(c_top + 0.15), Inches(5.2), Inches(2.05))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(12)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_CYAN

        p1 = tf.add_paragraph()
        p1.text = sub
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.space_before = Pt(2)

        for line in body.split("\n"):
            p_b = tf.add_paragraph()
            p_b.text = line
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = COLOR_TEXT_PRIMARY
            p_b.space_before = Pt(3)

    add_footer(slide, 6)


def build_slide_7_negative_testing(prs):
    """Slide 7: Domain Invariants & Negative Testing"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Negative Error Testing",
        "Compile-Time Semantic Error Detection",
        "Trapping domain-specific illegal constructs at compile-time with source-anchored diagnostics.",
        7
    )

    # Top: 4 Error Categories Cards
    err_cards = [
        ("Undeclared Identifier", "Typo / Missing Binding", "Catches missing indicator declarations or misspelled variables before execution."),
        ("Division by Zero", "Literal Zero Divisor", "Statically evaluates literal divisors (expr / 0) preventing runtime crash."),
        ("Invalid Period", "Window Period <= 0", "Enforces mathematical indicator constraints (e.g. SMA(CLOSE, 0) rejected)."),
        ("ENTRY_PRICE in ENTRY", "Premature Trade State", "Disallows referencing trade entry price before a position is actually opened."),
    ]

    for i, (title, sub, desc) in enumerate(err_cards):
        left = 0.8 + i * 2.95
        add_card(slide, Inches(left), Inches(1.85), Inches(2.8), Inches(1.4), COLOR_CARD_BG, COLOR_RED)
        tb = slide.shapes.add_textbox(Inches(left + 0.15), Inches(1.95), Inches(2.5), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_RED
        p1 = tf.add_paragraph()
        p1.text = sub
        p1.font.size = Pt(8.5)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.space_before = Pt(2)
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(8)
        p2.font.color.rgb = COLOR_TEXT_MUTED
        p2.space_before = Pt(3)

    # Bottom: Step 4 Screenshot Negative Error Detection
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_step4_negative_testing.png",
        left=0.8, top=3.45, max_width=11.7, max_height=3.4
    )

    add_footer(slide, 7)


def build_slide_8_ir_tac(prs):
    """Slide 8: Intermediate Code Generation (Three-Address Code)"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Intermediate Code Generation",
        "Three-Address Code (TAC) Quadruples & Control Flow",
        "Lowering hierarchical AST logic into a linear, machine-independent execution stream.",
        8
    )

    # Left Column: TAC theory & design
    add_card(slide, Inches(0.8), Inches(1.85), Inches(5.8), Inches(5.0))
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.4), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "TAC QUADRUPLE SPECIFICATION & SHORT-CIRCUIT FLOW"
    p0.font.size = Pt(11.5)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    items = [
        ("Quadruple Structure", "Instructions emitted as (op, arg1, arg2, result). Linearizes nested arithmetic and boolean expressions bottom-up."),
        ("Register & Label Pools", "Monotonically increasing TempPool emits virtual registers t0, t1, t2...; LabelPool emits branch targets L0, L1, L2..."),
        ("Short-Circuit Boolean Lowering", "Boolean AND and OR expressions are lowered using conditional branch quadruples (if not t GOTO Lx), skipping evaluation of secondary operands when false."),
        ("First-Class Trading Actions", "Dispatches high-level order directives directly in the instruction stream: ACTION [ENTRY] BUY 100.0 SHARES OF 'AAPL'."),
    ]

    for title, desc in items:
        p_t = tf.add_paragraph()
        p_t.text = f"▸ {title}"
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE
        p_t.space_before = Pt(8)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = COLOR_TEXT_PRIMARY
        p_d.space_before = Pt(2)

    # Right Column: Screenshot Step 5 TAC
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_step5_ir_tac.png",
        left=6.9, top=1.85, max_width=5.6, max_height=5.0
    )

    add_footer(slide, 8)


def build_slide_9_runtime_interpreter(prs):
    """Slide 9: Runtime Execution Engine & Indicator Engine"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Runtime & Execution Engine",
        "Tree-Walking Interpreter & Mathematical Engine",
        "Dynamic environment binding and vector technical indicator calculation algorithms.",
        9
    )

    sections = [
        (
            "01  Dynamic Environment Binding",
            "Bar-by-Bar Runtime State",
            "• At every historical bar, a fresh Environment mapping is initialized with current bar prices (OPEN, HIGH, LOW, CLOSE, VOLUME).\n"
            "• Dynamic Variable Binding: ENTRY_PRICE is dynamically bound only when an open position exists.\n"
            "• Temporaries and indicator calculations are cached per bar to avoid redundant re-evaluations."
        ),
        (
            "02  Vector Technical Indicators",
            "High-Performance Incremental Math",
            "• SMA (Simple Moving Average): Sliding-window arithmetic mean with O(1)-amortized deque running sum.\n"
            "• EMA (Exponential Moving Average): Multiplier k = 2/(N+1), seeded with N-bar SMA window.\n"
            "• RSI (Relative Strength Index): Wilder's exponential smoothing tracking average gains and losses."
        ),
        (
            "03  Portfolio State Machine",
            "Realistic Order Simulation",
            "• Tracks cash balance, active Position (NONE, LONG, SHORT), and realized profit & loss.\n"
            "• Order Dispatched on Signals: BUY, SELL, STOP_LOSS, TAKE_PROFIT.\n"
            "• Sizing Rules: Fixed share quantity or full liquidation (SELL ALL)."
        ),
        (
            "04  Quantitative Correctness Oracle",
            "End-to-End Compiler Validation",
            "• The interpreter serves as an executable specification test for every earlier compiler stage.\n"
            "• A semantic or IR lowering defect manifests immediately as an anomalous trade or metric.\n"
            "• Ensures formal mathematical rigor across the entire language toolchain."
        ),
    ]

    for idx, (title, sub, body) in enumerate(sections):
        col = idx % 2
        row = idx // 2
        c_left = 0.8 + col * 5.9
        c_top = 1.9 + row * 2.5

        add_card(slide, Inches(c_left), Inches(c_top), Inches(5.7), Inches(2.35))
        tb = slide.shapes.add_textbox(Inches(c_left + 0.25), Inches(c_top + 0.15), Inches(5.2), Inches(2.05))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(12)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_CYAN

        p1 = tf.add_paragraph()
        p1.text = sub
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.space_before = Pt(2)

        for line in body.split("\n"):
            p_b = tf.add_paragraph()
            p_b.text = line
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = COLOR_TEXT_PRIMARY
            p_b.space_before = Pt(3)

    add_footer(slide, 9)


def build_slide_10_backtest_simulation(prs):
    """Slide 10: Portfolio State Machine & Backtest Simulation (Report + Chart)"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Simulation & Backtesting",
        "Backtest Execution Engine & Visual Performance",
        "Executing compiled strategy against real historical AAPL data (220 trading bars).",
        10
    )

    # Left Column: Step 6 Screenshot (Backtest Report Table & Trade Log)
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_step6_backtest_report.png",
        left=0.8, top=1.85, max_width=5.8, max_height=5.0
    )

    # Right Column: Matplotlib Equity Curve Chart
    insert_image_fit(
        slide,
        ASSETS_DIR / "equity_curve_chart.png",
        left=6.8, top=1.85, max_width=5.8, max_height=5.0
    )

    add_footer(slide, 10)


def build_slide_11_multistrategy(prs):
    """Slide 11: Multi-Strategy Demonstration & Scope Isolation"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Scope Isolation Demonstration",
        "Multi-Strategy Compilation & Lexical Scope Isolation",
        "Compiling multi-strategy files with identical variable names in separate scopes.",
        11
    )

    # Left Column: Multi-strategy architecture explanation
    add_card(slide, Inches(0.8), Inches(1.85), Inches(5.8), Inches(5.0))
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.4), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "MULTI-STRATEGY COMPILATION ARCHITECTURE"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    items = [
        ("Multi-Strategy Source Support", "A single SwayaLang (.strat) file can define multiple distinct STRATEGY declarations (e.g. FastSMA and SlowSMA in multi_strategy.strat)."),
        ("Independent Child Scopes", "Each strategy definition receives an isolated child scope rooted in the Global Scope. Local symbols are scoped strictly to their respective strategies."),
        ("Lexical Collision Prevention", "Both FastSMA and SlowSMA can declare independent indicator variables without namespace pollution or cross-strategy state bleeding."),
        ("End-to-End Independent Execution", "The interpreter walks each StrategyNode independently, producing separate trade logs, portfolio metrics, and equity curves."),
    ]

    for title, desc in items:
        p_t = tf.add_paragraph()
        p_t.text = f"▸ {title}"
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE
        p_t.space_before = Pt(8)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = COLOR_TEXT_PRIMARY
        p_d.space_before = Pt(2)

    # Right Column: Screenshot Multi-Strategy Symbol Table
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_multistrategy_isolation.png",
        left=6.9, top=1.85, max_width=5.6, max_height=5.0
    )

    add_footer(slide, 11)


def build_slide_12_verification_tests(prs):
    """Slide 12: Comprehensive Test Suite (63 Tests Passing)"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Verification & Testing",
        "Demonstration & Verification — 63 Tests Passing",
        "Exhaustive automated testing across all 8 compiler and runtime modules (100% pass rate).",
        12
    )

    # Left Column: 8 Test Suite Cards
    test_suites = [
        ("test_lexer.py", "11 Cases", "Token classification, line/col accuracy, LexErrors"),
        ("test_parser.py", "6 Cases", "LL(1) grammar, operator precedence, syntax errors"),
        ("test_ast.py", "4 Cases", "AST node creation, frozen immutability, pretty-print"),
        ("test_symbol_table.py", "8 Cases", "Parent-pointer scopes, define/resolve, isolation"),
        ("test_semantic.py", "12 Cases", "Indicator signatures, 2-type rules, 4 error traps"),
        ("test_ir.py", "4 Cases", "TAC quadruples, pools, short-circuit branch flow"),
        ("test_interpreter.py", "7 Cases", "Vector math (SMA/EMA/RSI), portfolio transitions"),
        ("test_driver.py", "11 Cases", "End-to-end CLI flags, exit codes, output dumps"),
    ]

    for idx, (name, count, desc) in enumerate(test_suites):
        col = idx % 2
        row = idx // 2
        c_left = 0.8 + col * 2.95
        c_top = 1.85 + row * 1.25

        add_card(slide, Inches(c_left), Inches(c_top), Inches(2.8), Inches(1.15))
        tb = slide.shapes.add_textbox(Inches(c_left + 0.15), Inches(c_top + 0.1), Inches(2.5), Inches(0.95))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = f"{name} ({count})"
        p0.font.size = Pt(9.5)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_CYAN

        p1 = tf.add_paragraph()
        p1.text = desc
        p1.font.size = Pt(8.5)
        p1.font.color.rgb = COLOR_TEXT_MUTED
        p1.space_before = Pt(2)

    # Right Column: Screenshot Pytest Execution Output
    insert_image_fit(
        slide,
        ASSETS_DIR / "screenshot_pytest_suite.png",
        left=6.9, top=1.85, max_width=5.6, max_height=5.0
    )

    add_footer(slide, 12)


def build_slide_13_challenges_innovations(prs):
    """Slide 13: Technical Challenges & Engineering Innovations"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Engineering Challenges",
        "Principal Engineering Challenges & Innovations",
        "Key architectural hurdles resolved during Phase 2 compiler implementation.",
        13
    )

    challenges = [
        (
            "Challenge 1: Compile-Time Declaration vs. Runtime State",
            "Indicators are declared once in source code (e.g. SMA(CLOSE, 20)) but must be evaluated incrementally across hundreds of bars.\n\n"
            "Resolution: Kept the symbol table strictly compile-time (storing function signature and formula), while the interpreter instantiates stateful running-sum deques and smoothing accumulators at runtime."
        ),
        (
            "Challenge 2: Contextual Keywords vs. Identifier Scoping",
            "Price fields like CLOSE and PRICE act as reserved keywords in indicators but values in arithmetic expressions, creating shadowing risks.\n\n"
            "Resolution: Classified them as dedicated PRICE_FIELD tokens in the lexer (never IDENTIFIER), preventing accidental user shadowing (e.g. INDICATOR CLOSE = ...) at the grammar level."
        ),
        (
            "Challenge 3: Linearizing Booleans with Short-Circuiting",
            "Evaluating compound expressions (AND, OR) naively would trigger costly indicator evaluations even when the left operand is false.\n\n"
            "Resolution: Lowered boolean combinators into conditional branch quadruples (if not t GOTO Lx), providing genuine short-circuit evaluation directly at the TAC intermediate representation."
        ),
        (
            "Innovation: End-to-End Backtest as Verification Oracle",
            "Compiler unit tests often stop at AST or TAC shape matching, missing subtle runtime semantic discrepancies.\n\n"
            "Resolution: Closed the loop with a simulated trading engine over real market data. Any semantic or IR code generation error immediately manifests as an invalid trade log or math anomaly."
        ),
    ]

    for idx, (title, desc) in enumerate(challenges):
        col = idx % 2
        row = idx // 2
        c_left = 0.8 + col * 5.9
        c_top = 1.9 + row * 2.5

        add_card(slide, Inches(c_left), Inches(c_top), Inches(5.7), Inches(2.35))
        tb = slide.shapes.add_textbox(Inches(c_left + 0.25), Inches(c_top + 0.15), Inches(5.2), Inches(2.05))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_CYAN

        p1 = tf.add_paragraph()
        p1.text = desc
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = COLOR_TEXT_PRIMARY
        p1.space_before = Pt(6)

    add_footer(slide, 13)


def build_slide_14_roadmap(prs):
    """Slide 14: Project Roadmap & Phase 3 Execution Timeline"""
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Roadmap & Execution Timeline",
        "Project Roadmap & Phase 3 Execution Timeline",
        "Structured milestones from core implementation to code optimizations and final deliverables.",
        14
    )

    phases = [
        (
            "Phase 1",
            "COMPLETED",
            RGBColor(5, 150, 105),
            "Problem Definition & Front-End Prototype",
            [
                "✓ Formal EBNF grammar design & project scaffold",
                "✓ Hand-written maximal-munch scanner & LL(1) parser",
                "✓ Immutable AST node hierarchy & pretty-printer",
                "✓ Prototype driver script & 27 unit tests passing",
            ]
        ),
        (
            "Phase 2",
            "REVIEW 2",
            RGBColor(14, 116, 144),
            "Core Compiler & Execution Engine",
            [
                "✓ Scoped Symbol Table across multi-strategy files",
                "✓ Semantic Analyzer with 2-type system & 4 error traps",
                "✓ Three-Address Code (TAC) with short-circuit branching",
                "✓ Bar-by-bar Interpreter & vector indicator algorithms",
                "✓ Portfolio state machine & historical backtesting",
                "✓ 63 automated pytest cases (100% pass rate)",
            ]
        ),
        (
            "Phase 3",
            "FINAL REVIEW",
            RGBColor(147, 51, 234),
            "Code Optimization & Visualization",
            [
                "▸ Constant Folding: Evaluate literal sub-expressions at compile time (CLOSE / (10 - 8) → CLOSE / 2)",
                "▸ Common Subexpression Elimination (CSE): Deduplicate identical indicator calculations across rules",
                "▸ Automated Equity Curve Plotting: Exporting matplotlib charts alongside JSON trade logs",
                "▸ Interactive Strategy Web Dashboard & Benchmarks",
                "▸ Final Comprehensive Project Report",
            ]
        ),
    ]

    col_w = 3.75
    col_spacing = 0.2
    for i, (p_name, badge_txt, badge_col, subtitle, milestones) in enumerate(phases):
        left = 0.8 + i * (col_w + col_spacing)
        top = 1.9

        add_card(slide, Inches(left), Inches(top), Inches(col_w), Inches(4.95))

        # Phase header box
        h_box = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.2), Inches(col_w - 0.4), Inches(0.4))
        tf_h = h_box.text_frame
        p_h = tf_h.paragraphs[0]
        p_h.text = p_name
        p_h.font.size = Pt(18)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_WHITE

        # Badge
        add_badge(slide, left + col_w - 1.4, top + 0.2, 1.2, 0.3, badge_txt, badge_col)

        # Subtitle
        s_box = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.65), Inches(col_w - 0.4), Inches(0.4))
        tf_s = s_box.text_frame
        tf_s.word_wrap = True
        p_s = tf_s.paragraphs[0]
        p_s.text = subtitle
        p_s.font.size = Pt(10)
        p_s.font.bold = True
        p_s.font.color.rgb = COLOR_CYAN

        # Milestone items
        m_box = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 1.15), Inches(col_w - 0.4), Inches(3.6))
        tf_m = m_box.text_frame
        tf_m.word_wrap = True

        for idx, m in enumerate(milestones):
            p = tf_m.paragraphs[0] if idx == 0 else tf_m.add_paragraph()
            p.text = m
            p.font.size = Pt(9.5)
            p.font.color.rgb = COLOR_TEXT_PRIMARY
            p.space_before = Pt(8)

    add_footer(slide, 14)


# ===========================================================================
# MAIN EXECUTION
# ===========================================================================

def main():
    prs = create_presentation()
    print("Building Phase 2 Presentation...")

    build_slide_1_title(prs)
    build_slide_2_scope_contrast(prs)
    build_slide_3_pipeline_architecture(prs)
    build_slide_4_frontend_ast(prs)
    build_slide_5_symbol_table(prs)
    build_slide_6_semantic_analysis(prs)
    build_slide_7_negative_testing(prs)
    build_slide_8_ir_tac(prs)
    build_slide_9_runtime_interpreter(prs)
    build_slide_10_backtest_simulation(prs)
    build_slide_11_multistrategy(prs)
    build_slide_12_verification_tests(prs)
    build_slide_13_challenges_innovations(prs)
    build_slide_14_roadmap(prs)

    output_path = Path("SwayaLang_Phase2_Presentation.pptx")
    prs.save(str(output_path))
    print(f"\nSuccessfully generated presentation: {output_path.resolve()}")


if __name__ == "__main__":
    main()
