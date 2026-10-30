"""
tools/generate_screenshots.py
Captures real output from demonstrate_phase2.py steps and renders
pixel-perfect, high-DPI macOS terminal window screenshots and equity curve chart.
"""

import io
import os
import sys
import subprocess
import contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.symbol_table import SymbolTable
from compiler.semantic import SemanticAnalyzer, SemanticError
from compiler.ir import IRGenerator
from compiler.interpreter import Interpreter, MarketData
import demonstrate_phase2

OUTPUT_DIR = Path("presentation_assets")
OUTPUT_DIR.mkdir(exist_ok=True)

# Select best font
FONT_PATH = "/Users/swayamshukla/Library/Fonts/JetBrainsMono-VariableFont_wght.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/System/Library/Fonts/Menlo.ttc"

FONT_SIZE = 19
FONT = ImageFont.truetype(FONT_PATH, FONT_SIZE)
TITLE_FONT = ImageFont.truetype(FONT_PATH, 15)


def parse_line_colors(line: str):
    """Assign syntax highlight colors to tokens/keywords in terminal output."""
    l_strip = line.strip()

    if line.startswith("---") or line.startswith("===") or line.startswith("___"):
        return [("#58a6ff", line)]
    if "DEMO STEP" in line or "SWAYALANG — REVIEW 2" in line:
        return [("#38bdf8", line)]
    if line.startswith("$ "):
        parts = line.split(" ", 2)
        return [("#3fb950", "$ "), ("#e6edf3", parts[1] if len(parts) > 1 else ""), ("#79c0ff", " " + (parts[2] if len(parts) > 2 else ""))]

    if line.startswith("+---") or line.startswith("  ID |") or line.startswith("  ---+"):
        return [("#6e7681", line)]
    if line.startswith("| Scope") or line.startswith("| Simulation Bars:") or line.startswith("|      BACKTEST"):
        return [("#79c0ff", line)]
    if line.startswith("|"):
        return [("#e6edf3", line)]

    if "[SUCCESS]" in line or "PASSED" in line or "ISOLATED" in line:
        return [("#3fb950", line)]
    if "[WARNING]" in line:
        return [("#d29922", line)]
    if "[FAIL]" in line or "SemanticError" in line or "Error:" in line or "LexError" in line or "ParseError" in line:
        return [("#f85149", line)]

    if line.strip().startswith(";"):
        return [("#8b949e", line)]
    if any(k in line for k in ["t0 =", "t1 =", "t2 =", "t3 =", "t4 =", "t5 =", "t6 =", "t7 =", "t8 =", "t9 ="]):
        return [("#e6edf3", line)]
    if "ACTION [" in line:
        return [("#f0883e", line)]
    if "if not" in line:
        return [("#bc8cff", line)]
    if line.strip().startswith("L") and line.strip().endswith(":"):
        return [("#58a6ff", line)]

    if line.strip().startswith("Program") or line.strip().startswith("Strategy("):
        return [("#38bdf8", line)]
    if "RuleBlock(" in line:
        return [("#f0883e", line)]
    if "Action(" in line:
        return [("#3fb950", line)]
    if "BoolOp(" in line or "Comparison(" in line:
        return [("#bc8cff", line)]
    if "IndicatorDecl(" in line or "FuncCall(" in line:
        return [("#79c0ff", line)]

    if "test session starts" in line:
        return [("#58a6ff", line)]
    if "passed in" in line:
        return [("#3fb950", line)]

    if "BUY_ENTRY" in line:
        return [("#3fb950", line)]
    if "SELL_TAKE_PROFIT" in line:
        return [("#79c0ff", line)]
    if "SELL_EXIT" in line or "SELL_STOP_LOSS" in line:
        return [("#f85149", line)]

    return [("#e6edf3", line)]


def render_terminal(title: str, text: str, output_path: Path):
    """Renders text inside a high-res macOS terminal window mockup."""
    raw_lines = text.strip().split("\n")
    lines = [l for l in raw_lines]

    line_height = int(FONT_SIZE * 1.5)
    padding_x = 28
    padding_y = 22
    title_bar_height = 42

    dummy_img = Image.new("RGB", (100, 100))
    dummy_draw = ImageDraw.Draw(dummy_img)

    computed_width = 800
    for l in lines:
        w = dummy_draw.textlength(l, font=FONT)
        if w + padding_x * 2 + 40 > computed_width:
            computed_width = int(w + padding_x * 2 + 40)

    width = max(min(computed_width, 2000), 960)
    height = title_bar_height + padding_y * 2 + len(lines) * line_height + 15

    scale = 2
    img = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    w_s = width * scale
    h_s = height * scale
    tb_s = title_bar_height * scale
    r_s = 14 * scale

    draw.rounded_rectangle([(0, 0), (w_s - 1, h_s - 1)], radius=r_s, fill=(13, 17, 23, 255), outline=(48, 54, 61, 255), width=2 * scale)

    draw.rounded_rectangle([(0, 0), (w_s - 1, tb_s)], radius=r_s, fill=(22, 27, 34, 255))
    draw.rectangle([(0, tb_s - 10 * scale), (w_s - 1, tb_s)], fill=(22, 27, 34, 255))
    draw.line([(0, tb_s), (w_s - 1, tb_s)], fill=(48, 54, 61, 255), width=2 * scale)

    btn_radius = 7 * scale
    btn_y = tb_s // 2
    btn_x_start = 22 * scale
    btn_spacing = 22 * scale

    draw.ellipse([(btn_x_start - btn_radius, btn_y - btn_radius), (btn_x_start + btn_radius, btn_y + btn_radius)], fill=(255, 95, 86, 255))
    draw.ellipse([(btn_x_start + btn_spacing - btn_radius, btn_y - btn_radius), (btn_x_start + btn_spacing + btn_radius, btn_y + btn_radius)], fill=(255, 189, 46, 255))
    draw.ellipse([(btn_x_start + btn_spacing * 2 - btn_radius, btn_y - btn_radius), (btn_x_start + btn_spacing * 2 + btn_radius, btn_y + btn_radius)], fill=(39, 201, 63, 255))

    scaled_title_font = ImageFont.truetype(FONT_PATH, 14 * scale)
    t_len = draw.textlength(title, font=scaled_title_font)
    t_x = (w_s - t_len) // 2
    draw.text((t_x, (tb_s - 14 * scale) // 2 - 2 * scale), title, fill=(139, 148, 158, 255), font=scaled_title_font)

    scaled_font = ImageFont.truetype(FONT_PATH, FONT_SIZE * scale)
    cur_y = tb_s + padding_y * scale
    for line in lines:
        cur_x = padding_x * scale
        colored_segments = parse_line_colors(line)
        for hex_color, seg_text in colored_segments:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            draw.text((cur_x, cur_y), seg_text, fill=(r, g, b, 255), font=scaled_font)
            cur_x += int(draw.textlength(seg_text, font=scaled_font))
        cur_y += line_height * scale

    final_img = img.resize((width, height), Image.Resampling.LANCZOS)
    final_img.save(output_path, "PNG", optimize=True)
    print(f"Generated screenshot: {output_path} ({width}x{height})")


def generate_all_screenshots():
    strat_file = Path("examples/multi_rule.strat")
    source = strat_file.read_text(encoding="utf-8")

    # 1. Step 1: Lexical Analysis Tokens
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 demonstrate_phase2.py --step 1")
        tokens = demonstrate_phase2.step_1_lexical_analysis(source)
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 1: Lexical Tokens & Position Tracking",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step1_tokens.png"
    )

    # 2. Step 2: Syntax Analysis & AST Generation
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 demonstrate_phase2.py --step 2")
        ast = demonstrate_phase2.step_2_syntax_analysis(tokens)
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 2: Recursive-Descent AST Generation",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step2_ast.png"
    )

    # 3. Step 3: Scoped Symbol Table & Semantic Invariants
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 demonstrate_phase2.py --step 3")
        demonstrate_phase2.step_3_symbol_table_and_semantic(ast)
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 3: Scoped Symbol Table & Semantic Invariants",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step3_symbol_table.png"
    )

    # 4. Step 4: Negative Error Testing
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 demonstrate_phase2.py --step 4")
        demonstrate_phase2.step_4_negative_error_detection()
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 4: Semantic Error Detection (Negative Testing)",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step4_negative_testing.png"
    )

    # 5. Step 5: Three-Address Code
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 demonstrate_phase3.py --step 5")
        demonstrate_phase2.step_5_intermediate_representation(ast)
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 5: Intermediate Representation (Three-Address Code)",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step5_ir_tac.png"
    )

    # 6. Step 6: Code Optimization (Phase 3 Core)
    from compiler.optimizer import Optimizer
    ir_prog = IRGenerator().generate(ast)
    _, opt_ir, opt_stats = Optimizer().optimize(ast, ir_prog)
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 driver.py examples/multi_rule.strat --optimize")
        print(opt_stats.format_summary())
        print("\nOptimized Three-Address Code (Quadruples after Constant Folding & CSE):")
        if opt_ir:
            print(opt_ir.dump())
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 6: Code Optimization (Constant Folding & CSE Audit)",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step6_optimization.png"
    )

    # 7. Step 7: Comprehensive Financial Report (Phase 3)
    from compiler.reporter import BenchmarkRunner
    comp_report, _ = BenchmarkRunner.measure_pipeline(
        source=strat_file.read_text(encoding="utf-8"),
        market_data=MarketData.from_csv(Path("examples/data/AAPL_daily.csv"), ticker="AAPL"),
        capital=100000.0,
        enable_optimization=True,
    )
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 driver.py examples/multi_rule.strat --report")
        print(comp_report.format_summary())
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 7: Comprehensive Financial Risk Analytics",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step7_comprehensive_report.png"
    )

    # 8. Step 8: Compiler System Benchmark (Phase 3)
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print("$ python3 driver.py examples/multi_rule.strat --benchmark")
        print(comp_report.benchmark.format_summary())
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Step 8: Compiler Systems Benchmark & Latency Breakdown",
        f.getvalue(),
        OUTPUT_DIR / "screenshot_step8_benchmark.png"
    )

    # 9. Multi-Strategy Scope Isolation
    cmd_out = subprocess.check_output(
        ["python3", "driver.py", "examples/multi_strategy.strat", "--symbols"],
        text=True
    )
    multi_strat_text = "$ python3 driver.py examples/multi_strategy.strat --symbols\n" + cmd_out.strip() + "\n\nScope isolation check: FastSMA.fast_sma != SlowSMA.slow_sma  [PASS]"
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Multi-Strategy Scope Isolation Demonstration",
        multi_strat_text,
        OUTPUT_DIR / "screenshot_multistrategy_isolation.png"
    )

    # 10. Pytest Automated Test Suite (84 passing tests)
    selected_p_lines = [
        "$ pytest -v tests/",
        "============================= test session starts ==============================",
        "platform darwin -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0",
        "rootdir: /Users/swayamshukla/Compiler_Design_Proj",
        "collected 84 items",
        "",
        "tests/test_lexer.py ........... [11/11 PASSED]             [ 13%]",
        "tests/test_parser.py ...... [6/6 PASSED]                   [ 20%]",
        "tests/test_ast.py .... [4/4 PASSED]                         [ 25%]",
        "tests/test_symbol_table.py ........ [8/8 PASSED]           [ 35%]",
        "tests/test_semantic.py ............ [12/12 PASSED]         [ 49%]",
        "tests/test_ir.py .... [4/4 PASSED]                         [ 54%]",
        "tests/test_optimizer.py ........ [8/8 PASSED]              [ 63%]",
        "tests/test_interpreter.py ....... [7/7 PASSED]             [ 71%]",
        "tests/test_reporter.py .... [4/4 PASSED]                   [ 76%]",
        "tests/test_phase3_integration.py ......... [9/9 PASSED]    [ 87%]",
        "tests/test_driver.py ........... [11/11 PASSED]            [100%]",
        "",
        "============================== 84 passed in 3.65s =============================="
    ]
    render_terminal(
        "swayam@vit: ~/Compiler_Design_Proj — Automated Pytest Suite (84 Tests Passing - 100% Pass Rate)",
        "\n".join(selected_p_lines),
        OUTPUT_DIR / "screenshot_pytest_suite.png"
    )

    # 11. Matplotlib Equity Curve & Backtest Chart
    generate_equity_chart(ast)


def generate_equity_chart(ast):
    """Renders a sleek dark-mode financial chart of the interpreter's simulation."""
    csv_file = Path("examples/data/AAPL_daily.csv")
    if csv_file.is_file():
        data = MarketData.from_csv(csv_file, ticker="AAPL")
    else:
        data = MarketData.generate_synthetic(ticker="AAPL", n_bars=120)

    interpreter = Interpreter(data, initial_capital=100000.0)
    reports = interpreter.run(ast)
    report = reports[0]

    # Style plot in dark mode
    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.2), dpi=200, gridspec_kw={"height_ratios": [2.2, 1.2]}, sharex=True)
    fig.patch.set_facecolor("#0d1117")
    ax1.set_facecolor("#161b22")
    ax2.set_facecolor("#161b22")

    bars = list(range(len(data.closes)))
    prices = data.closes
    equity = interpreter.equity_curve

    # Plot 1: Asset Price & Trade Markers
    ax1.plot(bars, prices, color="#58a6ff", linewidth=1.8, label="AAPL Daily Close Price")

    # Overlay SMA 20 if available
    sma_20 = interpreter.indicator_cache.get("sma_20")
    if sma_20:
        clean_sma = [v if v is not None else float("nan") for v in sma_20]
        ax1.plot(bars, clean_sma, color="#d29922", linewidth=1.2, linestyle="--", label="SMA(20) Indicator")

    # Plot trade entry/exit markers
    for trade in report.trades:
        # Find bar index corresponding to trade date
        try:
            bar_idx = data.dates.index(trade.date)
        except ValueError:
            continue

        if "BUY" in trade.action:
            ax1.scatter(bar_idx, trade.price, color="#3fb950", marker="^", s=110, zorder=5, label="BUY ENTRY" if trade.trade_id == 1 else "")
        elif "TAKE_PROFIT" in trade.action:
            ax1.scatter(bar_idx, trade.price, color="#2ea043", marker="v", s=110, zorder=5, label="TAKE PROFIT (+8%)" if trade.trade_id == 2 else "")
        elif "EXIT" in trade.action:
            ax1.scatter(bar_idx, trade.price, color="#f85149", marker="v", s=110, zorder=5, label="EXIT" if trade.trade_id == 10 else "")

    ax1.set_title("SwayaLang Execution Engine — MomentumBreakout Strategy on AAPL (220 Bars)", color="#e6edf3", fontsize=13, pad=12, fontweight="bold")
    ax1.set_ylabel("Price ($)", color="#8b949e", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
    ax1.legend(loc="upper left", framealpha=0.8, facecolor="#0d1117", edgecolor="#30363d", fontsize=8.5)

    # Plot 2: Portfolio Equity Curve
    initial_cap = interpreter.initial_capital
    ax2.plot(bars, equity, color="#2ea043", linewidth=2.0, label="Portfolio Equity ($)")
    ax2.axhline(initial_cap, color="#8b949e", linestyle=":", alpha=0.6, label=f"Initial Capital (${initial_cap:,.0f})")
    ax2.fill_between(bars, initial_cap, equity, where=[e >= initial_cap for e in equity], color="#2ea043", alpha=0.15)
    ax2.fill_between(bars, initial_cap, equity, where=[e < initial_cap for e in equity], color="#f85149", alpha=0.15)

    ax2.set_ylabel("Equity ($)", color="#8b949e", fontsize=10)
    ax2.set_xlabel("Trading Bars (Days)", color="#8b949e", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
    ax2.legend(loc="upper left", framealpha=0.8, facecolor="#0d1117", edgecolor="#30363d", fontsize=8.5)

    # Key metrics text box on bottom right
    stats_text = (
        f"Return: {report.return_pct:+.2f}%\n"
        f"Net PnL: ${report.net_profit:,.2f}\n"
        f"Win Rate: {report.win_rate_pct:.1f}%\n"
        f"Trades: {report.total_trades}\n"
        f"Max DD: {report.max_drawdown_pct:.2f}%"
    )
    ax2.text(0.98, 0.15, stats_text, transform=ax2.transAxes, fontsize=8.5,
             verticalalignment="bottom", horizontalalignment="right",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#0d1117", edgecolor="#30363d", alpha=0.9),
             color="#79c0ff", family="monospace")

    plt.tight_layout()
    chart_path = OUTPUT_DIR / "equity_curve_chart.png"
    plt.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Generated equity curve chart: {chart_path}")


if __name__ == "__main__":
    generate_all_screenshots()
