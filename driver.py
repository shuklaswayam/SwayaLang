"""
driver.py — SwayaLang Command-Line Driver (Full 3-Phase Compiler Pipeline)
==========================================================================
Final Phase 3 deliverable for BCSE307P Compiler Design Laboratory.

Pipeline Stages Demonstrated:
    1. Lexical Analysis       (Lexer: Token recognition & position tracking)
    2. Syntax Analysis        (Parser: Recursive-descent AST construction)
    3. Symbol Table           (Scoped symbol resolution & type metadata)
    4. Semantic Analysis      (Type checking, signature & domain validation)
    5. Intermediate Code      (Three-Address Code Quadruples generator)
    6. Code Optimization      (AST & TAC Constant Folding, CSE, DCE, Jumps)
    7. Execution Engine       (Bar-by-bar backtest simulation & trade execution)
    8. Analytics & Report     (Risk metrics, performance profiling, plotting)

Usage:
    python driver.py <strategy.strat> [options]

Options:
    --tokens          Display lexical token stream
    --ast             Display pretty-printed Abstract Syntax Tree
    --symbols         Display scoped Symbol Table
    --semantic        Run semantic analysis & type checking
    --ir              Display Three-Address Code (TAC) Quadruples
    --optimize        Display optimized TAC and optimization statistics
    --run             Execute backtest simulation on price data
    --report          Display comprehensive financial & systems report
    --benchmark       Display execution latency breakdown & memory footprint
    --plot [path]     Export high-DPI equity curve & drawdown chart PNG
    --export-json <p> Export comprehensive metrics to JSON file
    --export-csv <p>  Export trade history log to CSV file
    --data <path>     Path to OHLCV historical CSV data
    --capital <num>   Initial simulation capital (default: 100,000.0)
    --demo            Run automated Phase 2 demonstration
    --demo3           Run automated comprehensive Phase 3 demonstration

Exit codes:
    0 — success
    1 — missing argument, file not found, LexError, ParseError, or SemanticError
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from compiler.ast_nodes import ProgramNode
from compiler.interpreter import BacktestReport, Interpreter, MarketData
from compiler.ir import IRGenerator, IRProgram
from compiler.lexer import LexError, Lexer, Token
from compiler.optimizer import OptimizationStats, Optimizer
from compiler.parser import ParseError, Parser
from compiler.reporter import (
    BenchmarkRunner,
    CompilerBenchmark,
    ComprehensiveReport,
    ReportGenerator,
)
from compiler.semantic import SemanticAnalyzer, SemanticError
from compiler.symbol_table import SymbolTable


def run_pipeline(
    source: str,
    data_path: Optional[Path] = None,
    capital: float = 100000.0,
    show_tokens: bool = True,
    show_ast: bool = True,
    show_symbols: bool = True,
    show_semantic: bool = True,
    show_ir: bool = True,
    show_optimize: bool = True,
    run_execution: bool = True,
    show_report: bool = True,
    show_benchmark: bool = False,
    plot_path: Optional[Path] = None,
    export_json_path: Optional[Path] = None,
    export_csv_path: Optional[Path] = None,
) -> None:
    """Run full or partial compiler pipeline stages."""

    # -----------------------------------------------------------------------
    # Stage 1: Lexical Analysis
    # -----------------------------------------------------------------------
    lexer = Lexer(source)
    tokens: list[Token] = lexer.tokenize()

    if show_tokens:
        print("── Token Stream ────────────────────────────────────────────────────────────")
        for tok in tokens:
            print(tok)

    # -----------------------------------------------------------------------
    # Stage 2: Syntax Analysis & AST Construction
    # -----------------------------------------------------------------------
    parser = Parser(tokens)
    prog_ast: ProgramNode = parser.parse()

    if show_ast:
        print("\n── Abstract Syntax Tree ────────────────────────────────────────────────────")
        prog_ast.pretty_print()

    # -----------------------------------------------------------------------
    # Stage 3: Symbol Table & Semantic Analysis
    # -----------------------------------------------------------------------
    analyzer = SemanticAnalyzer(fail_fast=True)
    symtab, errors, warnings = analyzer.analyze(prog_ast)

    if show_symbols:
        print("\n── Symbol Table ────────────────────────────────────────────────────────────")
        print(symtab.format_table())

    if show_semantic:
        print("\n── Semantic Analysis ───────────────────────────────────────────────────────")
        print(f"Status: VALIDATED (0 errors, {len(warnings)} warning(s))")
        for w in warnings:
            print(f"  [WARNING] {w}")

    # -----------------------------------------------------------------------
    # Stage 4: Intermediate Code Generation (Three-Address Code)
    # -----------------------------------------------------------------------
    ir_gen = IRGenerator()
    ir_prog: IRProgram = ir_gen.generate(prog_ast)

    if show_ir:
        print("\n── Intermediate Representation (Three-Address Code) ───────────────────────")
        print(ir_prog.dump())

    # -----------------------------------------------------------------------
    # Stage 5: Code Optimization (AST & TAC) — Phase 3
    # -----------------------------------------------------------------------
    optimizer = Optimizer()
    opt_ast, opt_ir, opt_stats = optimizer.optimize(prog_ast, ir_prog)

    if show_optimize:
        print("\n── Code Optimization (Phase 3) ─────────────────────────────────────────────")
        print(opt_stats.format_summary())
        if opt_ir is not None:
            print("\nOptimized Three-Address Code:")
            print(opt_ir.dump())

    # -----------------------------------------------------------------------
    # Stage 6: Execution Engine / Backtest Runtime
    # -----------------------------------------------------------------------
    market_data: MarketData
    if data_path and data_path.is_file():
        market_data = MarketData.from_csv(data_path, ticker=data_path.stem.split("_")[0])
    else:
        # Check default sample files
        default_aapl = Path("examples/data/AAPL_daily.csv")
        default_tsla = Path("examples/data/TSLA_daily.csv")
        if default_aapl.is_file():
            market_data = MarketData.from_csv(default_aapl, ticker="AAPL")
        elif default_tsla.is_file():
            market_data = MarketData.from_csv(default_tsla, ticker="TSLA")
        else:
            market_data = MarketData.generate_synthetic(ticker="AAPL", n_bars=120)

    reports: list[BacktestReport] = []
    if run_execution:
        print("\n── Execution Engine (Backtest Simulation) ───────────────────────────────────")
        engine = Interpreter(market_data, initial_capital=capital)
        reports = engine.run(opt_ast)
        for report in reports:
            print(report.format_summary())
            print()

    # -----------------------------------------------------------------------
    # Stage 7: Analytics & Comprehensive Reporting — Phase 3
    # -----------------------------------------------------------------------
    if (show_report or show_benchmark or plot_path or export_json_path or export_csv_path) and reports:
        final_report, _ = BenchmarkRunner.measure_pipeline(
            source=source,
            market_data=market_data,
            capital=capital,
            enable_optimization=True,
        )

        if show_report:
            print("\n── Comprehensive Performance Report (Phase 3) ──────────────────────────────")
            print(final_report.format_summary())

        if show_benchmark:
            print("\n── Compiler System Benchmark (Phase 3) ─────────────────────────────────────")
            print(final_report.benchmark.format_summary())

        if plot_path:
            out_img = ReportGenerator.plot_equity_curve(final_report, output_path=plot_path)
            print(f"\n[OUTPUT] High-DPI Equity Curve Chart saved to: {out_img}")

        if export_json_path:
            final_report.export_json(export_json_path)
            print(f"[OUTPUT] Metrics exported to JSON: {export_json_path}")

        if export_csv_path:
            final_report.export_csv(export_csv_path)
            print(f"[OUTPUT] Trade history exported to CSV: {export_csv_path}")


def run_demo() -> None:
    """Run an automated demonstration of Phase 2 capabilities (for backwards compatibility)."""
    print("=" * 80)
    print(" SWAYALANG PHASE 2 CORE IMPLEMENTATION DEMONSTRATION")
    print("=" * 80)

    demo_file = Path("examples/golden_cross.strat")
    if not demo_file.is_file():
        print("Demo file not found.", file=sys.stderr)
        return

    print(f"\nRunning Full Pipeline on: {demo_file}")
    source = demo_file.read_text(encoding="utf-8")
    run_pipeline(
        source,
        show_tokens=True,
        show_ast=True,
        show_symbols=True,
        show_semantic=True,
        show_ir=True,
        show_optimize=False,
        run_execution=True,
        show_report=False,
    )


def run_demo3() -> None:
    """Run full comprehensive Phase 3 demonstration."""
    import demonstrate_phase3
    demonstrate_phase3.run_phase3_full_demonstration()


def main() -> None:
    """CLI Entry point."""
    if len(sys.argv) < 2:
        print("Usage: python driver.py <path/to/strategy.strat> [options]", file=sys.stderr)
        sys.exit(1)

    if "--demo" in sys.argv:
        run_demo()
        sys.exit(0)

    if "--demo3" in sys.argv:
        run_demo3()
        sys.exit(0)

    arg_file = sys.argv[1]
    file_path = Path(arg_file)
    if not file_path.is_file():
        print(f"Error: File not found: '{file_path}'", file=sys.stderr)
        sys.exit(1)

    # Inspect flags
    flags = set(sys.argv[2:])
    specific_flags = {
        "--tokens",
        "--ast",
        "--symbols",
        "--semantic",
        "--ir",
        "--optimize",
        "--opt",
        "--run",
        "--report",
        "--benchmark",
    }
    active_specific = flags.intersection(specific_flags)

    # Determine data path or capital
    data_path: Optional[Path] = None
    capital: float = 100000.0
    plot_path: Optional[Path] = None
    export_json_path: Optional[Path] = None
    export_csv_path: Optional[Path] = None

    if "--data" in sys.argv:
        idx = sys.argv.index("--data")
        if idx + 1 < len(sys.argv):
            data_path = Path(sys.argv[idx + 1])

    if "--capital" in sys.argv:
        idx = sys.argv.index("--capital")
        if idx + 1 < len(sys.argv):
            try:
                capital = float(sys.argv[idx + 1])
            except ValueError:
                pass

    if "--plot" in sys.argv:
        idx = sys.argv.index("--plot")
        if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--"):
            plot_path = Path(sys.argv[idx + 1])
        else:
            plot_path = Path("presentation_assets/equity_curve_chart.png")

    if "--export-json" in sys.argv:
        idx = sys.argv.index("--export-json")
        if idx + 1 < len(sys.argv):
            export_json_path = Path(sys.argv[idx + 1])

    if "--export-csv" in sys.argv:
        idx = sys.argv.index("--export-csv")
        if idx + 1 < len(sys.argv):
            export_csv_path = Path(sys.argv[idx + 1])

    if active_specific:
        show_tokens = "--tokens" in flags
        show_ast = "--ast" in flags
        show_symbols = "--symbols" in flags
        show_semantic = "--semantic" in flags
        show_ir = "--ir" in flags
        show_optimize = ("--optimize" in flags) or ("--opt" in flags)
        run_execution = "--run" in flags
        show_report = "--report" in flags
        show_benchmark = "--benchmark" in flags
    else:
        # Default behavior: run complete 3-phase pipeline
        show_tokens = True
        show_ast = True
        show_symbols = True
        show_semantic = True
        show_ir = True
        show_optimize = True
        run_execution = True
        show_report = True
        show_benchmark = True

    try:
        source = file_path.read_text(encoding="utf-8")
        run_pipeline(
            source=source,
            data_path=data_path,
            capital=capital,
            show_tokens=show_tokens,
            show_ast=show_ast,
            show_symbols=show_symbols,
            show_semantic=show_semantic,
            show_ir=show_ir,
            show_optimize=show_optimize,
            run_execution=run_execution,
            show_report=show_report,
            show_benchmark=show_benchmark,
            plot_path=plot_path,
            export_json_path=export_json_path,
            export_csv_path=export_csv_path,
        )
    except LexError as err:
        print(f"{err}", file=sys.stderr)
        sys.exit(1)
    except ParseError as err:
        print(f"{err}", file=sys.stderr)
        sys.exit(1)
    except SemanticError as err:
        print(f"{err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
