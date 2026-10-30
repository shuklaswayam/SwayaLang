"""
build_phase3_ppt.py — SwayaLang Review 3 Final Presentation Generator
======================================================================
Review 3: Final Project Review & Defense
Course: Compiler Design Laboratory (BCSE307P)
Author: Swayam Shukla (24BCE0751)
Institution: VIT Vellore

Generates an 18-slide widescreen (16:9) presentation in PowerPoint format
(SwayaLang_Phase3_Presentation.pptx) addressing all 10 evaluation criteria:
  1. Project Completion
  2. Functional Correctness
  3. Technical Complexity
  4. Compiler Integration
  5. Innovation
  6. Code Quality
  7. Testing
  8. Demonstration
  9. Documentation
  10. Viva Voce Individual Understanding
"""

from __future__ import annotations

import os
from pathlib import Path
from PIL import Image

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ---------------------------------------------------------------------------
# Colors & Theme Constants (Dark Theme Aesthetic)
# ---------------------------------------------------------------------------
COLOR_BG_DARK = RGBColor(11, 15, 23)        # #0b0f17
COLOR_CARD_BG = RGBColor(22, 27, 34)        # #161b22
COLOR_CARD_BG_ALT = RGBColor(21, 28, 40)    # #151c28
COLOR_BORDER = RGBColor(48, 54, 61)         # #30363d
COLOR_BORDER_CYAN = RGBColor(14, 116, 144)  # #0e7490
COLOR_BORDER_PURPLE = RGBColor(147, 51, 234)# #9333ea

COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_TEXT_PRIMARY = RGBColor(240, 246, 252)
COLOR_TEXT_MUTED = RGBColor(148, 163, 184)  # #94a3b8
COLOR_TEXT_DIM = RGBColor(100, 116, 139)    # #64748b

COLOR_CYAN = RGBColor(56, 189, 248)         # #38bdf8
COLOR_NEON_CYAN = RGBColor(0, 242, 254)     # #00f2fe
COLOR_GREEN = RGBColor(34, 197, 94)         # #22c55e
COLOR_EMERALD = RGBColor(16, 185, 129)      # #10b981
COLOR_PURPLE = RGBColor(168, 85, 247)       # #a855f7
COLOR_AMBER = RGBColor(245, 158, 11)        # #f59e0b
COLOR_RED = RGBColor(239, 68, 68)           # #ef4444

TOTAL_SLIDES = 18
ASSETS_DIR = Path("presentation_assets")


def create_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_base_slide(prs) -> Any:
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_BG_DARK
    bg.line.fill.background()
    return slide


def add_header(slide, category: str, title: str, subtitle: str, slide_num: int) -> None:
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

    # Slide number
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
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.5), Inches(0.55))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(23)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE

    # Subtitle
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.28), Inches(11.5), Inches(0.35))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = subtitle
    p_sub.font.size = Pt(12)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED


def add_card(slide, left: float, top: float, width: float, height: float, border_color=COLOR_BORDER) -> Any:
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_CARD_BG
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.0)
    return shape


def add_safe_image(slide, img_path: Path, left: float, top: float, max_w: float, max_h: float) -> None:
    if not img_path.is_file():
        # Fallback card
        card = add_card(slide, left, top, max_w, max_h, COLOR_BORDER)
        tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.2), Inches(max_w - 0.4), Inches(max_h - 0.4))
        p = tb.text_frame.paragraphs[0]
        p.text = f"[Image artifact: {img_path.name}]"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MUTED
        return

    with Image.open(img_path) as im:
        orig_w, orig_h = im.size

    aspect = orig_w / orig_h
    target_w = max_w
    target_h = max_w / aspect

    if target_h > max_h:
        target_h = max_h
        target_w = max_h * aspect

    # Center within allocated bounding box
    final_left = left + (max_w - target_w) / 2.0
    final_top = top + (max_h - target_h) / 2.0

    slide.shapes.add_picture(
        str(img_path), Inches(final_left), Inches(final_top), width=Inches(target_w), height=Inches(target_h)
    )


# ===========================================================================
# SLIDE BUILDERS (18 SLIDES)
# ===========================================================================

def build_slide_1_title(prs):
    slide = add_base_slide(prs)

    # Accent decorative line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.8), Inches(1.5), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_NEON_CYAN
    line.line.fill.background()

    # Title box
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "SwayaLang"
    p0.font.size = Pt(46)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_WHITE

    p1 = tf.add_paragraph()
    p1.text = "A Domain-Specific Language, Compiler & Optimizer for Backtestable Stock Trading Strategies"
    p1.font.size = Pt(19)
    p1.font.color.rgb = COLOR_CYAN
    p1.space_before = Pt(8)

    p2 = tf.add_paragraph()
    p2.text = "Phase 3: Final Implementation, Optimization Passes, Empirical Benchmarking & System Defense"
    p2.font.size = Pt(14)
    p2.font.color.rgb = COLOR_TEXT_MUTED
    p2.space_before = Pt(12)

    # Candidate Card
    add_card(slide, 1.0, 4.6, 11.3, 2.0, COLOR_BORDER_CYAN)
    meta_box = slide.shapes.add_textbox(Inches(1.3), Inches(4.8), Inches(10.7), Inches(1.6))
    tf_meta = meta_box.text_frame
    tf_meta.word_wrap = True

    p_cand = tf_meta.paragraphs[0]
    p_cand.text = "Author: Swayam Shukla  |  Register No: 24BCE0751  |  Degree: B.Tech Computer Science & Engineering"
    p_cand.font.size = Pt(14)
    p_cand.font.bold = True
    p_cand.font.color.rgb = COLOR_WHITE

    p_course = tf_meta.add_paragraph()
    p_course.text = "Course: Compiler Design Laboratory (BCSE307P)  |  Review: Review 3 — Final Project Review"
    p_course.font.size = Pt(13)
    p_course.font.color.rgb = COLOR_CYAN
    p_course.space_before = Pt(6)

    p_inst = tf_meta.add_paragraph()
    p_inst.text = "Institution: School of Computer Science & Engineering (SCOPE), Vellore Institute of Technology (VIT), Vellore"
    p_inst.font.size = Pt(12)
    p_inst.font.color.rgb = COLOR_TEXT_MUTED
    p_inst.space_before = Pt(6)


def build_slide_2_rubric_matrix(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Review 3 Evaluation Alignment",
        "Project Deliverables & Review 3 Rubric Alignment Matrix",
        "Direct point-by-point mapping between official course evaluation criteria and implemented deliverables.",
        2
    )

    criteria = [
        ("Project Completion", "100% of planned 3 phases delivered: Front-end, Semantics/IR, Optimization & Backtesting.", COLOR_EMERALD),
        ("Functional Correctness", "Validated on historical AAPL/TSLA daily data; backtest PnL & trade logs verified.", COLOR_CYAN),
        ("Technical Complexity", "Multi-pass compiler pipeline: LL(1) recursive descent, TAC lowering, DAG-based CSE & CF.", COLOR_PURPLE),
        ("Compiler Integration", "Classical 7-stage architecture consuming formal EBNF with strictly separated passes.", COLOR_CYAN),
        ("Innovation & Relevance", "Eliminates imperative Python boilerplate; declarative DSL for quantitative finance rules.", COLOR_AMBER),
        ("Code Quality & Structure", "Modular package architecture, immutable AST dataclasses, PEP-8 compliance, full type hints.", COLOR_EMERALD),
        ("Testing & Validation", "84 automated pytest test cases covering valid, invalid, boundary, and edge conditions (100% pass).", COLOR_EMERALD),
        ("Demonstration & Web IDE", "Live interactive CLI demo (demonstrate_phase3.py) and Monaco-powered Web IDE dashboard.", COLOR_PURPLE),
        ("Documentation Quality", "Comprehensive Final Project Report, User Guide, EBNF Grammar Specification, and API docs.", COLOR_CYAN),
        ("Viva Voce Readiness", "Detailed technical analysis of grammar parsing, AST lowering, optimization algebra, and runtime.", COLOR_AMBER),
    ]

    card_w = 5.65
    card_h = 0.95
    for i, (title, desc, accent) in enumerate(criteria):
        col = i % 2
        row = i // 2
        left = 0.8 + col * (card_w + 0.3)
        top = 1.8 + row * (card_h + 0.15)
        add_card(slide, left, top, card_w, card_h, COLOR_BORDER)

        tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.1), Inches(card_w - 0.4), Inches(card_h - 0.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = f"✓ {title}"
        p0.font.size = Pt(12)
        p0.font.bold = True
        p0.font.color.rgb = accent

        p1 = tf.add_paragraph()
        p1.text = desc
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = COLOR_TEXT_MUTED
        p1.space_before = Pt(2)


def build_slide_3_pipeline_architecture(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "System Architecture",
        "End-to-End 7-Stage Compiler Pipeline & Execution Engine",
        "Strict unidirectional data flow ensuring stage isolation, testability, and deterministic lowering.",
        3
    )

    stages = [
        ("Stage 1", "Lexical Analysis", "Maximal-munch scanner", "Regular grammars, tokens, position tracking"),
        ("Stage 2", "Syntax Analysis", "Recursive-descent LL(1)", "Grammar rules, AST hierarchy, error recovery"),
        ("Stage 3", "Symbol Table", "Scoped symbol resolution", "Hierarchical scopes, type metadata, builtins"),
        ("Stage 4", "Semantic Analysis", "Type & domain checking", "Static division-by-zero, arity, domain rules"),
        ("Stage 5", "Intermediate Code", "Three-Address Code (TAC)", "Quadruples, synthetic temporaries, jump labels"),
        ("Stage 6", "Code Optimizer", "CF, Propagation, CSE, DCE", "Algebraic folding, value numbering, jump pruning"),
        ("Stage 7", "Execution Engine", "Vector backtest runtime", "Portfolio state machine, Sharpe, Drawdown, PnL"),
    ]

    card_w = 1.58
    card_gap = 0.1
    top = 2.0
    for i, (st_num, st_name, st_tech, st_desc) in enumerate(stages):
        left = 0.8 + i * (card_w + card_gap)
        border = COLOR_BORDER_CYAN if i < 4 else (COLOR_BORDER_PURPLE if i < 6 else COLOR_EMERALD)
        add_card(slide, left, top, card_w, 4.6, border)

        tb = slide.shapes.add_textbox(Inches(left + 0.12), Inches(top + 0.15), Inches(card_w - 0.24), Inches(4.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p_num = tf.paragraphs[0]
        p_num.text = st_num.upper()
        p_num.font.size = Pt(10)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_CYAN

        p_name = tf.add_paragraph()
        p_name.text = st_name
        p_name.font.size = Pt(13)
        p_name.font.bold = True
        p_name.font.color.rgb = COLOR_WHITE
        p_name.space_before = Pt(4)

        p_tech = tf.add_paragraph()
        p_tech.text = st_tech
        p_tech.font.size = Pt(10.5)
        p_tech.font.color.rgb = COLOR_NEON_CYAN
        p_tech.space_before = Pt(8)

        p_desc = tf.add_paragraph()
        p_desc.text = st_desc
        p_desc.font.size = Pt(9.5)
        p_desc.font.color.rgb = COLOR_TEXT_MUTED
        p_desc.space_before = Pt(12)


def build_slide_4_grammar_spec(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Language Specification",
        "Formal EBNF Grammar & Concrete Language Constructs",
        "Deterministic context-free grammar designed for LL(1) parsing without backtracking or ambiguities.",
        4
    )

    left_w = 5.6
    right_w = 5.9

    # Left card: EBNF grammar
    add_card(slide, 0.8, 1.8, left_w, 5.0, COLOR_BORDER)
    tb_l = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(left_w - 0.4), Inches(4.6))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p0 = tf_l.paragraphs[0]
    p0.text = "Formal EBNF Specification (GRAMMAR.md)"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    ebnf_code = (
        "program        := strategy+\n"
        "strategy       := 'STRATEGY' STRING '{' ind_decl* rule_block+ '}'\n"
        "ind_decl       := 'INDICATOR' IDENT '=' func_call\n"
        "func_call      := IDENT '(' arg (',' arg)* ')'\n"
        "rule_block     := rule_kind ':' action 'IF' condition\n"
        "rule_kind      := 'ENTRY' | 'EXIT' | 'STOP_LOSS' | 'TAKE_PROFIT'\n"
        "action         := ('BUY'|'SELL'|'SHORT') qty_spec? STRING\n"
        "                | 'SELL' 'ALL'\n"
        "qty_spec       := NUMBER 'SHARES' 'OF'\n"
        "condition      := or_expr\n"
        "or_expr        := and_expr ('OR' and_expr)*\n"
        "and_expr       := cmp_expr ('AND' cmp_expr)*\n"
        "cmp_expr       := expr ('>'|'<'|'>='|'<='|'==') expr\n"
        "expr           := term (('+' | '-') term)*\n"
        "term           := factor (('*' | '/') factor)*\n"
        "factor         := IDENT | NUMBER | '(' condition ')'"
    )
    p_code = tf_l.add_paragraph()
    p_code.text = ebnf_code
    p_code.font.size = Pt(9.5)
    p_code.font.color.rgb = COLOR_TEXT_PRIMARY
    p_code.space_before = Pt(6)

    # Right card: Sample snippet & features
    add_card(slide, 6.7, 1.8, right_w, 5.0, COLOR_BORDER_CYAN)
    tb_r = slide.shapes.add_textbox(Inches(6.9), Inches(2.0), Inches(right_w - 0.4), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p_r0 = tf_r.paragraphs[0]
    p_r0.text = "Concrete SwayaLang DSL Snippet"
    p_r0.font.size = Pt(13)
    p_r0.font.bold = True
    p_r0.font.color.rgb = COLOR_NEON_CYAN

    strat_code = (
        'STRATEGY "GoldenCross" {\n'
        '    INDICATOR sma_50  = SMA(CLOSE, 50)\n'
        '    INDICATOR sma_200 = SMA(CLOSE, 200)\n'
        '    INDICATOR rsi_14  = RSI(CLOSE, 14)\n\n'
        '    ENTRY:     BUY 100 SHARES OF "AAPL"\n'
        '               IF sma_50 > sma_200 AND rsi_14 < 30\n\n'
        '    EXIT:      SELL ALL\n'
        '               IF sma_50 < sma_200\n\n'
        '    STOP_LOSS: SELL ALL\n'
        '               IF PRICE < ENTRY_PRICE * 0.95\n'
        '}'
    )
    p_sc = tf_r.add_paragraph()
    p_sc.text = strat_code
    p_sc.font.size = Pt(10.5)
    p_sc.font.color.rgb = COLOR_WHITE
    p_sc.space_before = Pt(8)


def build_slide_5_frontend(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Front-End Implementation",
        "Scanner (Lexer), Recursive-Descent Parser & Immutable AST",
        "Phase 1 foundation: maximal-munch tokenization and LL(1) recursive AST construction with line/col tracking.",
        5
    )

    # Left: Lexer & Parser Card
    add_card(slide, 0.8, 1.8, 5.5, 5.0, COLOR_BORDER)
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.1), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "Front-End Compiler Highlights"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    points = [
        ("Hand-written Maximal-Munch Scanner", "Identifies multi-char operators (>=, <=, ==) and differentiates keywords from user identifiers."),
        ("Exact Coordinate Tracking", "Every Token carries (line, col) enabling IDE error highlighting with caret pointers."),
        ("Deterministic LL(1) Recursive Descent", "Precedence climbing for arithmetic (*, / over +, -) and boolean (AND over OR)."),
        ("Immutable Frozen AST Hierarchy", "All nodes are Python frozen dataclasses preventing unintended mutation across passes."),
        ("Human-Readable AST Pretty Printer", "Indented 2-space hierarchical tree output for auditing AST structures."),
    ]
    for h, d in points:
        p = tf.add_paragraph()
        p.text = f"• {h}: {d}"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)

    # Right: Screenshot of Tokens and AST
    add_safe_image(slide, ASSETS_DIR / "screenshot_step1_2_ast.png", 6.6, 1.8, 5.9, 5.0)


def build_slide_6_symbol_table(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Symbol Table Management",
        "Hierarchical Scoped Symbol Table & Lexical Isolation",
        "Phase 2 deliverable: global built-ins and per-strategy child scopes preventing cross-strategy variable leakage.",
        6
    )

    # Left: Symbol table screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_step3_symbol_table.png", 0.8, 1.8, 6.0, 5.0)

    # Right: Design principles
    add_card(slide, 7.1, 1.8, 5.4, 5.0, COLOR_BORDER_CYAN)
    tb = slide.shapes.add_textbox(Inches(7.3), Inches(2.0), Inches(5.0), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "Scoped Symbol Table Architecture"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_NEON_CYAN

    principles = [
        ("Two-Tier Hierarchical Scopes", "Global scope registers built-in indicator signatures (SMA, EMA, RSI) and price fields (CLOSE, OPEN, HIGH, LOW, VOLUME, PRICE, ENTRY_PRICE)."),
        ("Lexical Scope Isolation", "Child scopes represent individual strategies. Variables defined in 'GoldenCross' are strictly inaccessible to 'Momentum'."),
        ("Rich Symbol Metadata", "Each Symbol record tracks symbol name, SymbolKind (INDICATOR, PRICE_FIELD, BUILTIN_FUNC), DataType (SERIES, INT, FLOAT), and declaration signature."),
        ("Shadowing Prevention", "Declaring indicators matching built-in keywords or price fields immediately raises a fatal compiler SemanticError."),
        ("Clean Scope Formatting", "ASCII tabular rendering for compiler introspection and IDE symbol inspector."),
    ]
    for h, d in principles:
        p = tf.add_paragraph()
        p.text = f"▸ {h}: {d}"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)


def build_slide_7_semantic_analysis(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Semantic Validation",
        "Semantic Analyzer, Type System & 4 Static Safety Traps",
        "Phase 2 deliverable: compile-time enforcement of type invariants, indicator signatures, and domain logic.",
        7
    )

    # Left: Negative testing screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_step4_negative_testing.png", 0.8, 1.8, 6.2, 5.0)

    # Right: Four static error traps
    add_card(slide, 7.3, 1.8, 5.2, 5.0, COLOR_BORDER)
    tb = slide.shapes.add_textbox(Inches(7.5), Inches(2.0), Inches(4.8), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "Four Core Static Semantic Safety Traps"
    p0.font.size = Pt(13.5)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_AMBER

    traps = [
        ("Trap 1: Undeclared Identifiers", "Catches misspelled indicator names or unassigned variables in condition expressions before execution."),
        ("Trap 2: Static Division by Zero", "Traps zero denominators in constant arithmetic expressions at compile-time (e.g. CLOSE > 100 / 0)."),
        ("Trap 3: Indicator Arity & Period Validation", "Enforces that periods are strictly positive integers (period > 0) and matches function parameter counts."),
        ("Trap 4: Domain Logic Invariant", "Prohibits ENTRY_PRICE references in ENTRY rules since no trade position exists prior to entry."),
        ("Warning System: Dead Indicators", "Issues non-fatal warnings for indicators declared but never referenced in any rule."),
    ]
    for h, d in traps:
        p = tf.add_paragraph()
        p.text = f"• {h}: {d}"
        p.font.size = Pt(9.8)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(5)


def build_slide_8_ir_generation(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Intermediate Code Generation",
        "Linearized Three-Address Code (TAC) Quadruples",
        "Phase 2 deliverable: lowering hierarchical AST into machine-independent linear quadruples (op, arg1, arg2, result).",
        8
    )

    # Left: TAC screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_step5_ir_tac.png", 0.8, 1.8, 5.8, 5.0)

    # Right: Concept card
    add_card(slide, 6.9, 1.8, 5.6, 5.0, COLOR_BORDER_CYAN)
    tb = slide.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.2), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "Three-Address Code (TAC) Lowering Strategy"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_NEON_CYAN

    concepts = [
        ("Quadruple Architecture", "Standard (op, arg1, arg2, result) record format enabling straightforward optimization passes."),
        ("Synthetic Temporary Allocation", "Generates virtual registers (t0, t1, t2, ...) in Static Single Assignment (SSA) form for complex nested sub-expressions."),
        ("Branch Label Generation", "Generates jump labels (L0, L1, L2, ...) to control rule skipping when boolean preconditions evaluate to false."),
        ("Boolean Short-Circuit Lowering", "Lowers compound conditions (AND, OR) into explicit conditional test and jump sequences (if not t GOTO L)."),
        ("Action Lowering", "Lowers high-level trading actions into explicit ACTION opcodes with execution parameters."),
    ]
    for h, d in concepts:
        p = tf.add_paragraph()
        p.text = f"▸ {h}: {d}"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)


def build_slide_9_optimization_pass_1(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Code Optimization (Phase 3 Core)",
        "Pass 1: Constant Folding & Constant Propagation",
        "Compile-time algebra evaluating constant expressions and propagating literal values through synthetic registers.",
        9
    )

    # 3 Cards across the slide
    cards = [
        ("Arithmetic Constant Folding", [
            "Evaluates arithmetic on numeric literals at compile time:",
            "  ENTRY_PRICE * (1.0 - 0.05) → ENTRY_PRICE * 0.95",
            "  CLOSE / (10 - 8) → CLOSE / 2.0",
            "  (10 + 20) → 30.0",
            "",
            "Eliminates runtime floating-point arithmetic across hundreds of daily market bars.",
        ], COLOR_EMERALD),
        ("Algebraic Identity Laws", [
            "Simplifies redundant operations using mathematical identity and annihilator properties:",
            "  x * 1.0 → x   (Multiplicative Identity)",
            "  x + 0.0 → x   (Additive Identity)",
            "  x - 0.0 → x   (Subtractive Identity)",
            "",
            "Reduces bytecode instruction count and eliminates temporary register pressure.",
        ], COLOR_CYAN),
        ("Boolean Logic Folding", [
            "Resolves static boolean conditions at compile time:",
            "  True AND P → P",
            "  False AND P → False (Short-circuit elimination)",
            "  True OR P → True",
            "  False OR P → P",
            "",
            "Static branch pruning eliminates impossible rule paths before interpretation.",
        ], COLOR_PURPLE),
    ]

    card_w = 3.65
    for i, (title, lines, col) in enumerate(cards):
        left = 0.8 + i * (card_w + 0.28)
        add_card(slide, left, 1.9, card_w, 4.9, col)

        tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(2.1), Inches(card_w - 0.4), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(13)
        p0.font.bold = True
        p0.font.color.rgb = col

        for l in lines:
            p = tf.add_paragraph()
            p.text = l
            p.font.size = Pt(9.5)
            p.font.color.rgb = COLOR_TEXT_PRIMARY if "→" in l else COLOR_TEXT_MUTED
            p.space_before = Pt(3)


def build_slide_10_optimization_pass_2(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Code Optimization (Phase 3 Core)",
        "Pass 2: Common Subexpression Elimination (CSE) & Dead Code Pruning",
        "Value numbering across rule quadruples deduplicating technical indicator calls and pruning dead registers.",
        10
    )

    left_w = 5.7
    right_w = 5.8

    # Left: CSE Explanation
    add_card(slide, 0.8, 1.8, left_w, 5.0, COLOR_BORDER_PURPLE)
    tb_l = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(left_w - 0.4), Inches(4.6))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    p0 = tf_l.paragraphs[0]
    p0.text = "Common Subexpression Elimination (CSE)"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_PURPLE

    p_cse_desc = tf_l.add_paragraph()
    p_cse_desc.text = (
        "In trading strategies, multiple rules frequently test identical sub-conditions:\n"
        "  Rule 1 (ENTRY): sma_50 > sma_200\n"
        "  Rule 2 (EXIT):  sma_50 > sma_200 (or shared indicator calls)\n\n"
        "Value Numbering Algorithm:\n"
        "1. Computes canonical key: hash(op, arg1, arg2).\n"
        "2. Commutative normalization: min(arg1, arg2) for +, *, ==, AND, OR.\n"
        "3. Strategy-wide invariant: Because market indicators and price fields are pure & immutable per bar, expressions persist across basic blocks.\n"
        "4. Redundant quadruples are replaced with direct temporary aliases: t4 = t1."
    )
    p_cse_desc.font.size = Pt(10)
    p_cse_desc.font.color.rgb = COLOR_TEXT_MUTED
    p_cse_desc.space_before = Pt(6)

    # Right: DCE & Jump Optimization
    add_card(slide, 6.8, 1.8, right_w, 5.0, COLOR_BORDER)
    tb_r = slide.shapes.add_textbox(Inches(7.0), Inches(2.0), Inches(right_w - 0.4), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p_r0 = tf_r.paragraphs[0]
    p_r0.text = "Dead Code Elimination (DCE) & Jump Optimization"
    p_r0.font.size = Pt(14)
    p_r0.font.bold = True
    p_r0.font.color.rgb = COLOR_CYAN

    p_dce = tf_r.add_paragraph()
    p_dce.text = (
        "Dead Temporary Pruning:\n"
        "• Scans the complete TAC sequence to construct variable reference sets.\n"
        "• Eliminates unreferenced temporary assignments (t_dead = ...) with no side effects.\n\n"
        "Fall-Through Jump Elimination:\n"
        "• Detects unconditional jumps targeting immediately subsequent labels:\n"
        "    goto L1\n"
        "    L1:       → [Eliminated]\n\n"
        "Unreferenced Label Cleaning:\n"
        "• Removes jump targets that have no incoming branches."
    )
    p_dce.font.size = Pt(10)
    p_dce.font.color.rgb = COLOR_TEXT_MUTED
    p_dce.space_before = Pt(6)


def build_slide_11_optimization_audit(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Empirical Optimization Results",
        "Quantitative Optimization Audit & Instruction Reduction",
        "Demonstrated bytecode reduction and execution efficiency across canonical test strategies.",
        11
    )

    # Left: Optimization screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_step6_optimization.png", 0.8, 1.8, 6.0, 5.0)

    # Right: Optimization Audit Cards
    add_card(slide, 7.1, 1.8, 5.4, 5.0, COLOR_BORDER_EMERALD if hasattr(COLOR_BORDER, "EMERALD") else COLOR_BORDER)
    tb = slide.shapes.add_textbox(Inches(7.3), Inches(2.0), Inches(5.0), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "Phase 3 Optimization Metrics Audit"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_EMERALD

    metrics = [
        ("Instruction Reduction Rate", "7.7% to 25.0% bytecode reduction across strategies with compound expressions."),
        ("Constant Folding Transformations", "100% of compile-time arithmetic (1.0 - 0.05, 10 + 20) evaluated ahead-of-time."),
        ("Common Subexpressions Replaced", "Deduplicates shared indicator comparisons across entry, exit, and stop-loss blocks."),
        ("Semantics Preservation Proof", "Empirical proof via test_optimization_semantic_equivalence: Unoptimized vs Optimized execution outputs are 100% mathematically identical."),
        ("Zero Runtime Overhead", "Optimized AST and TAC execute in fewer bytecode operations per bar."),
    ]
    for h, d in metrics:
        p = tf.add_paragraph()
        p.text = f"✓ {h}: {d}"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)


def build_slide_12_backtest_runtime(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Execution Engine & Runtime",
        "Vector Indicator Mathematics & Portfolio State Machine",
        "Bar-by-bar historical simulation evaluating technical indicators and trade execution rules against market CSV data.",
        12
    )

    # Left: Vector mathematics
    add_card(slide, 0.8, 1.8, 5.6, 5.0, COLOR_BORDER_CYAN)
    tb_l = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.2), Inches(4.6))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    p0 = tf_l.paragraphs[0]
    p0.text = "Technical Indicator Mathematical Formulations"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN

    math_text = (
        "1. Simple Moving Average (SMA):\n"
        "   SMA_t = (1 / n) * Σ_{i=0}^{n-1} P_{t-i}\n\n"
        "2. Exponential Moving Average (EMA):\n"
        "   α = 2 / (n + 1)\n"
        "   EMA_t = α * P_t + (1 - α) * EMA_{t-1}\n\n"
        "3. Relative Strength Index (RSI - Wilder's Smoothing):\n"
        "   RS = SmoothedAvgGain / SmoothedAvgLoss\n"
        "   RSI = 100 - (100 / (1 + RS))\n\n"
        "Precomputed once per strategy run into time-series vector arrays, providing O(1) bar lookup."
    )
    p_m = tf_l.add_paragraph()
    p_m.text = math_text
    p_m.font.size = Pt(9.5)
    p_m.font.color.rgb = COLOR_TEXT_PRIMARY
    p_m.space_before = Pt(6)

    # Right: State Machine
    add_card(slide, 6.7, 1.8, 5.8, 5.0, COLOR_BORDER)
    tb_r = slide.shapes.add_textbox(Inches(6.9), Inches(2.0), Inches(5.4), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p_r0 = tf_r.paragraphs[0]
    p_r0.text = "Portfolio State Machine Dynamics"
    p_r0.font.size = Pt(13)
    p_r0.font.bold = True
    p_r0.font.color.rgb = COLOR_EMERALD

    sm_text = (
        "• State Vector: (Cash, Position, Shares, Entry Price, Realized PnL)\n"
        "• Warm-Up Skip: Automatically skips bars where indicators are undefined (bar < max_period).\n"
        "• ENTRY Rule: Transitions Flat → Long. Deducts capital (shares * price), initializes Position object.\n"
        "• EXIT / STOP_LOSS / TAKE_PROFIT: Transitions Long → Flat. Credits cash with sale proceeds, logs realized PnL and return %.\n"
        "• Dynamic Variables: Runtime environment binds PRICE and ENTRY_PRICE dynamically per bar."
    )
    p_sm = tf_r.add_paragraph()
    p_sm.text = sm_text
    p_sm.font.size = Pt(10)
    p_sm.font.color.rgb = COLOR_TEXT_MUTED
    p_sm.space_before = Pt(6)


def build_slide_13_financial_analytics(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Quantitative Financial Analytics",
        "Financial Risk Analytics: Sharpe, Sortino, Drawdown & Equity Curve",
        "Phase 3 deliverable: comprehensive financial reporting and automated publication-grade equity curve visualization.",
        13
    )

    # Left: Comprehensive report screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_step7_comprehensive_report.png", 0.8, 1.8, 5.6, 5.0)

    # Right: Equity Curve Chart
    add_safe_image(slide, ASSETS_DIR / "equity_curve_chart.png", 6.6, 1.8, 5.9, 5.0)


def build_slide_14_system_benchmarks(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Performance Benchmarking",
        "Systems Latency, Memory Profiling & Scaling Throughput",
        "Phase 3 deliverable: nanosecond timing per compiler stage, peak RSS memory tracing, and dataset scaling up to 10,000 bars.",
        14
    )

    # Left: Benchmark screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_step8_benchmark.png", 0.8, 1.8, 5.6, 5.0)

    # Right: Scaling Chart
    add_safe_image(slide, ASSETS_DIR / "benchmark_scaling_chart.png", 6.6, 1.8, 5.9, 5.0)


def build_slide_15_testing_matrix(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Comprehensive Validation",
        "Automated Test Suite: 84 Unit & Integration Tests (100% Pass Rate)",
        "Exhaustive test matrix covering valid programs, syntax errors, semantic traps, boundary scales, and optimizer equivalence.",
        15
    )

    # Left: Pytest suite screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_pytest_suite.png", 0.8, 1.8, 6.0, 5.0)

    # Right: Test breakdown card
    add_card(slide, 7.1, 1.8, 5.4, 5.0, COLOR_BORDER_CYAN)
    tb = slide.shapes.add_textbox(Inches(7.3), Inches(2.0), Inches(5.0), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "Test Coverage Breakdown by Subsystem"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_NEON_CYAN

    tests_breakdown = [
        ("Lexer Tests (11 tests)", "Keywords, identifiers, numbers, strings, delimiters, position tracking, unterminated strings, invalid characters."),
        ("Parser Tests (6 tests)", "LL(1) parsing, AST hierarchy, parenthesized conditions, missing strategy, missing rules, syntax errors."),
        ("Symbol Table Tests (8 tests)", "Hierarchical scope resolution, built-in registration, lexical isolation, duplicate symbol prevention."),
        ("Semantic Tests (12 tests)", "Type system validation, arity mismatch, invalid period, static division by zero, ENTRY_PRICE in ENTRY, dead indicator warning."),
        ("IR Generator Tests (4 tests)", "Three-Address Code formatting, temporary variable indexing, boolean short-circuit branching."),
        ("Optimizer Tests (8 tests)", "Constant folding, algebraic identities, boolean laws, CSE deduplication, dead code pruning, jump optimization."),
        ("Interpreter & Reporter Tests (11 tests)", "Indicator engines, Sharpe/Sortino calculations, CSV/JSON exports, plotting, trade log state transitions."),
        ("Integration & Driver Tests (20 tests)", "End-to-end CLI execution, boundary capital scaling, 0-trade strategies, semantic equivalence proofs."),
    ]
    for h, d in tests_breakdown:
        p = tf.add_paragraph()
        p.text = f"• {h}: {d}"
        p.font.size = Pt(8.8)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(3)


def build_slide_16_web_ide(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Interactive Demonstration",
        "SwayaLang Modern Web IDE & Developer Tooling",
        "Full-stack browser workbench: Monaco code editor, dynamic tab inspectors, optimizer diffs, and Chart.js equity visualization.",
        16
    )

    # Left: Web IDE features
    add_card(slide, 0.8, 1.8, 5.6, 5.0, COLOR_BORDER_PURPLE)
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.2), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "SwayaLang Web IDE Architecture"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_PURPLE

    features = [
        ("Monaco Editor Integration", "Custom Monarch syntax tokenizer for SwayaLang keywords, indicators, and strings with in-editor error squiggles."),
        ("Stage Execution Toggles", "Inspect selective stages: Tokens, AST Tree, Symbol Scopes, Raw TAC, Optimizer Diffs, Financials, or Benchmarks."),
        ("Optimizer Diff Viewer", "Side-by-side view comparing unoptimized vs optimized Three-Address Code with reduction percentage badge."),
        ("Interactive Financial Charting", "Real-time Chart.js rendering of portfolio equity curve and trade execution markers."),
        ("Export Capabilities", "One-click download of trade execution history as CSV (swayalang_trades.csv)."),
        ("REST Backend (app.py)", "Flask API executing the compiler pipeline in-process with nanosecond timing telemetry."),
    ]
    for h, d in features:
        p = tf.add_paragraph()
        p.text = f"▸ {h}: {d}"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_MUTED
        p.space_before = Pt(6)

    # Right: Multi-strategy scope isolation screenshot
    add_safe_image(slide, ASSETS_DIR / "screenshot_multistrategy_isolation.png", 6.7, 1.8, 5.8, 5.0)


def build_slide_17_technical_innovations(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Technical Innovations & Academic Rigor",
        "Compiler Design Concepts & Domain Synthesis",
        "Synthesis of classical computer science compiler theory with high-performance quantitative financial modeling.",
        17
    )

    cards = [
        ("Declarative DSL for Finance", [
            "Replaces error-prone imperative backtesting scripts with clean declarative language.",
            "Eliminates lookahead bias: compiler strictly evaluates bar-by-bar sequentially.",
            "Non-programmers can author complex quantitative rules easily.",
        ], COLOR_CYAN),
        ("Classical Compiler Rigor", [
            "Hand-written scanner & recursive-descent parser without parser generator crutches.",
            "Immutable Abstract Syntax Tree (AST) node hierarchy.",
            "Linearized Three-Address Code (TAC) Quadruples representation.",
        ], COLOR_EMERALD),
        ("Advanced Code Optimization", [
            "Multi-pass optimizer implementing Constant Folding, Propagation, CSE, and Dead Code Elimination.",
            "Guaranteed semantics preservation proven by automated test suites.",
            "Significant bytecode reduction and zero runtime penalty.",
        ], COLOR_PURPLE),
        ("Production-Grade Engineering", [
            "84 automated pytest test cases with 100% pass rate.",
            "Dual interface: Command-line Driver (driver.py) & Modern Web IDE (app.py).",
            "Comprehensive reporting: Sharpe, Sortino, Drawdown, and publication charts.",
        ], COLOR_AMBER),
    ]

    card_w = 5.6
    card_h = 2.3
    for i, (title, points, col) in enumerate(cards):
        col_idx = i % 2
        row_idx = i // 2
        left = 0.8 + col_idx * (card_w + 0.3)
        top = 1.9 + row_idx * (card_h + 0.3)
        add_card(slide, left, top, card_w, card_h, col)

        tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.15), Inches(card_w - 0.4), Inches(card_h - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(13)
        p0.font.bold = True
        p0.font.color.rgb = col

        for pt in points:
            p = tf.add_paragraph()
            p.text = f"• {pt}"
            p.font.size = Pt(9.5)
            p.font.color.rgb = COLOR_TEXT_MUTED
            p.space_before = Pt(3)


def build_slide_18_viva_defense(prs):
    slide = add_base_slide(prs)
    add_header(
        slide,
        "Viva Voce Defense & Individual Understanding",
        "Key Compiler Design Questions & Technical Defense",
        "Rigorous technical preparation covering parsing theory, intermediate representations, and optimization algebra.",
        18
    )

    qa_items = [
        (
            "Q: Why use recursive-descent parsing over shift-reduce (LALR)?",
            "A: Recursive-descent gives complete, fine-grained control over syntax error recovery, produces clear source-located error messages, avoids shift-reduce conflict debugging, and directly constructs custom immutable AST nodes with O(n) linear parsing time.",
            COLOR_CYAN,
        ),
        (
            "Q: How are operator precedence and associativity handled without conflicts?",
            "A: Precedence climbing is hard-coded into the grammar hierarchy: or_expr calls and_expr, which calls cmp_expr, which calls expr (+, -), which calls term (*, /). This naturally enforces arithmetic precedence over comparisons and comparisons over boolean operators without ambiguous productions.",
            COLOR_EMERALD,
        ),
        (
            "Q: Why is Three-Address Code (TAC) necessary if the interpreter can walk the AST?",
            "A: TAC linearizes hierarchical nested tree structures into a machine-independent sequential quadruple stream. This enables straightforward machine-independent optimization algorithms (such as value numbering for CSE and control-flow jump analysis) that are mathematically complex to perform directly on arbitrary recursive trees.",
            COLOR_PURPLE,
        ),
        (
            "Q: How does Common Subexpression Elimination (CSE) guarantee semantic equivalence?",
            "A: In SwayaLang, indicators and price series are computed purely and are immutable for any given bar. Therefore, subexpressions composed of indicators and price fields have no side effects, guaranteeing that substituting redundant calculations with earlier temporary registers is 100% semantics-preserving.",
            COLOR_AMBER,
        ),
    ]

    card_w = 11.5
    card_h = 1.15
    for i, (q, a, col) in enumerate(qa_items):
        top = 1.85 + i * (card_h + 0.15)
        add_card(slide, 0.8, top, card_w, card_h, COLOR_BORDER)

        tb = slide.shapes.add_textbox(Inches(1.0), Inches(top + 0.1), Inches(card_w - 0.4), Inches(card_h - 0.2))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = q
        p0.font.size = Pt(11.5)
        p0.font.bold = True
        p0.font.color.rgb = col

        p1 = tf.add_paragraph()
        p1.text = a
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = COLOR_TEXT_PRIMARY
        p1.space_before = Pt(3)


# ===========================================================================
# MAIN GENERATOR ROUTINE
# ===========================================================================

def build_presentation() -> Path:
    prs = create_presentation()
    print("Building SwayaLang Review 3 Presentation (18 slides)...")

    build_slide_1_title(prs)
    build_slide_2_rubric_matrix(prs)
    build_slide_3_pipeline_architecture(prs)
    build_slide_4_grammar_spec(prs)
    build_slide_5_frontend(prs)
    build_slide_6_symbol_table(prs)
    build_slide_7_semantic_analysis(prs)
    build_slide_8_ir_generation(prs)
    build_slide_9_optimization_pass_1(prs)
    build_slide_10_optimization_pass_2(prs)
    build_slide_11_optimization_audit(prs)
    build_slide_12_backtest_runtime(prs)
    build_slide_13_financial_analytics(prs)
    build_slide_14_system_benchmarks(prs)
    build_slide_15_testing_matrix(prs)
    build_slide_16_web_ide(prs)
    build_slide_17_technical_innovations(prs)
    build_slide_18_viva_defense(prs)

    output_pptx = Path("SwayaLang_Phase3_Presentation.pptx")
    prs.save(str(output_pptx))
    print(f"✓ Saved Presentation PPTX: {output_pptx.resolve()} ({output_pptx.stat().st_size:,} bytes)")
    return output_pptx


if __name__ == "__main__":
    build_presentation()
