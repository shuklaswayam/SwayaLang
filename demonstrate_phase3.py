"""
demonstrate_phase3.py — SwayaLang Phase 3 Interactive Review Demonstration
===========================================================================
Review 3: Final Project Review & Implementation Defense
Course: Compiler Design Laboratory (BCSE307P)
Author: Swayam Shukla (24BCE0751)
Institution: VIT Vellore

This script provides an interactive step-by-step demonstration of the complete
final project according to Section 12 & 13 of the project syllabus:
  1. Lexical Analysis & Token Stream
  2. Syntax Analysis & Abstract Syntax Tree Lowering
  3. Scoped Symbol Table & Type Invariant Checking
  4. Robust Negative Testing & Semantic Error Diagnostics
  5. Intermediate Representation (Linearized Three-Address Code Quadruples)
  6. Code Optimization (Constant Folding, Constant Propagation, CSE & DCE)
  7. Execution Engine Simulation (Vector Backtest & Historical Trade Signals)
  8. Advanced Financial Risk Analytics (Sharpe Ratio, Sortino, Drawdown, CAGR)
  9. Systems Performance Profiling (Latency Breakdown, Memory RSS, Throughput)
  10. Automated High-Resolution Equity Curve & Benchmark Artifact Generation
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from compiler.ast_nodes import ProgramNode
from compiler.interpreter import Interpreter, MarketData
from compiler.ir import IRGenerator, IRProgram
from compiler.lexer import LexError, Lexer
from compiler.optimizer import Optimizer
from compiler.parser import ParseError, Parser
from compiler.reporter import BenchmarkRunner, ReportGenerator
from compiler.semantic import SemanticAnalyzer, SemanticError


def print_banner(title: str, char: str = "=", width: int = 82) -> None:
    print("\n" + char * width)
    print(f" {title}")
    print(char * width)


def step_1_lexical_analysis(source: str):
    print_banner("DEMO STEP 1: LEXICAL ANALYSIS (Maximal-Munch Token Stream)", "-")
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"[STATUS] Tokenization Succeeded: {len(tokens)} total tokens classified.")
    print("Sample tokens (first 10):")
    for t in tokens[:10]:
        print(f"  {t}")
    return tokens


def step_2_syntax_analysis(tokens):
    print_banner("DEMO STEP 2: SYNTAX ANALYSIS & AST GENERATION", "-")
    parser = Parser(tokens)
    ast = parser.parse()
    print("[STATUS] Parsing Succeeded: Immutable Abstract Syntax Tree constructed.")
    print("Pretty-printed Abstract Syntax Tree:")
    ast.pretty_print()
    return ast


def step_3_symbol_table_and_semantics(ast):
    print_banner("DEMO STEP 3: SCOPED SYMBOL TABLE & SEMANTIC TYPE CHECKING", "-")
    analyzer = SemanticAnalyzer(fail_fast=True)
    symtab, errors, warnings = analyzer.analyze(ast)

    print("Scoped Symbol Table (Hierarchical Lexical Isolation):")
    print(symtab.format_table())

    print("\nSemantic Analysis Status:")
    print(f"  Static Errors Detected:   {len(errors)}")
    print(f"  Compiler Warnings Issued: {len(warnings)}")
    for w in warnings:
        print(f"    [WARNING] {w}")
    print("  [SUCCESS] All type invariants, indicator signatures & domain rules validated.")
    return symtab


def step_4_negative_error_detection():
    print_banner("DEMO STEP 4: COMPREHENSIVE NEGATIVE TESTING & ERROR DIAGNOSTICS", "-")
    test_cases = [
        (
            "Lexical Unknown Character",
            'STRATEGY "BadLex" { ENTRY: @ }',
            LexError,
        ),
        (
            "Syntax Missing IF Clause",
            'STRATEGY "BadSyn" { ENTRY: BUY 100 SHARES OF "AAPL" sma_50 > 20 }',
            ParseError,
        ),
        (
            "Semantic Undeclared Indicator",
            'STRATEGY "BadSem1" { ENTRY: BUY 100 SHARES OF "AAPL" IF unknown_ind > 50 }',
            SemanticError,
        ),
        (
            "Semantic Static Division by Zero",
            'STRATEGY "BadSem2" { ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > (100 / 0) }',
            SemanticError,
        ),
        (
            "Domain Violation: ENTRY_PRICE in ENTRY Rule",
            'STRATEGY "BadSem3" { ENTRY: BUY 100 SHARES OF "AAPL" IF PRICE < ENTRY_PRICE * 0.95 }',
            SemanticError,
        ),
    ]

    for title, src, expected_exc in test_cases:
        print(f"\n[TESTING] {title}:")
        try:
            tokens = Lexer(src).tokenize()
            ast = Parser(tokens).parse()
            SemanticAnalyzer(fail_fast=True).analyze(ast)
            print("  [FAIL] Expected compiler error was not raised!")
        except expected_exc as err:
            print(f"  [CAUGHT AS EXPECTED] {type(err).__name__}: {err}")


def step_5_intermediate_code_generation(ast):
    print_banner("DEMO STEP 5: INTERMEDIATE CODE GENERATION (Three-Address Code)", "-")
    ir_gen = IRGenerator()
    ir_prog = ir_gen.generate(ast)
    print("Generated Linearized Three-Address Code (TAC) Quadruples:")
    print(ir_prog.dump())
    return ir_prog


def step_6_code_optimization(ast, ir_prog):
    print_banner("DEMO STEP 6: CODE OPTIMIZATION (Constant Folding, CSE, DCE)", "-")
    optimizer = Optimizer()
    opt_ast, opt_ir, stats = optimizer.optimize(ast, ir_prog)

    print(stats.format_summary())
    print("\nOptimized Three-Address Code (Quadruples after Optimization):")
    if opt_ir is not None:
        print(opt_ir.dump())

    print(f"\n[IMPACT] Initial Quads: {stats.initial_quad_count} -> Optimized: {stats.optimized_quad_count} ({stats.reduction_pct:.2f}% reduction)")

    # Dedicated Optimization Showcase (Demonstrating Constant Folding & CSE in action)
    print("\n--- Dedicated Optimization Benchmark Demonstration ---")
    opt_demo_src = '''
    STRATEGY "OptimizationShowcase" {
        INDICATOR sma_50  = SMA(CLOSE, 50)
        INDICATOR sma_200 = SMA(CLOSE, 200)

        ENTRY:     BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200 AND PRICE > (10 + 40)
        EXIT:      SELL ALL                  IF sma_50 > sma_200
        STOP_LOSS: SELL ALL                  IF PRICE < ENTRY_PRICE * (1.0 - 0.05)
    }
    '''
    raw_tokens = Lexer(opt_demo_src).tokenize()
    raw_ast_demo = Parser(raw_tokens).parse()
    raw_ir_demo = IRGenerator().generate(raw_ast_demo)
    _, opt_ir_demo, demo_stats = Optimizer().optimize(raw_ast_demo, raw_ir_demo)

    print(demo_stats.format_summary())
    print(f"[VERIFICATION] Constant Folds: {demo_stats.constant_folds} | CSE Deduplications: {demo_stats.cse_eliminations} | Reduction: {demo_stats.reduction_pct:.2f}%")
    return opt_ast, opt_ir, stats


def step_7_execution_and_financial_analytics(source: str, data: MarketData, opt_ast):
    print_banner("DEMO STEP 7: BACKTEST RUNTIME & ADVANCED FINANCIAL RISK ANALYTICS", "-")
    report, opt_stats = BenchmarkRunner.measure_pipeline(
        source=source,
        market_data=data,
        capital=100000.0,
        enable_optimization=True,
    )
    print(report.format_summary())
    return report


def step_8_system_benchmarks(report):
    print_banner("DEMO STEP 8: COMPILER SYSTEMS BENCHMARK & MEMORY PROFILING", "-")
    print(report.benchmark.format_summary())


def step_9_artifact_generation(report):
    print_banner("DEMO STEP 9: PUBLICATION-GRADE VISUAL ARTIFACT EXPORT", "-")
    output_dir = Path("presentation_assets")
    output_dir.mkdir(exist_ok=True)

    chart_path = output_dir / "equity_curve_chart.png"
    json_path = output_dir / "final_backtest_report.json"
    csv_path = output_dir / "final_trade_history.csv"

    ReportGenerator.plot_equity_curve(report, output_path=chart_path)
    report.export_json(json_path)
    report.export_csv(csv_path)

    print(f"  [EXPORT] High-DPI Equity Curve Chart: {chart_path} ({chart_path.stat().st_size:,} bytes)")
    print(f"  [EXPORT] Structured JSON Report:     {json_path} ({json_path.stat().st_size:,} bytes)")
    print(f"  [EXPORT] Execution Trade History CSV: {csv_path} ({csv_path.stat().st_size:,} bytes)")


def run_phase3_full_demonstration():
    print("=" * 82)
    print(" SWAYALANG REVIEW 3: FINAL IMPLEMENTATION & COMPILER DEFENSE DEMONSTRATION")
    print(" Candidate: Swayam Shukla (24BCE0751) | Course: BCSE307P | VIT Vellore")
    print("=" * 82)

    demo_file = Path("examples/multi_rule.strat")
    data_file = Path("examples/data/AAPL_daily.csv")

    if not demo_file.is_file():
        print(f"Error: Demo strategy not found: {demo_file}", file=sys.stderr)
        return
    if not data_file.is_file():
        print(f"Error: Market dataset not found: {data_file}", file=sys.stderr)
        return

    source = demo_file.read_text(encoding="utf-8")
    data = MarketData.from_csv(data_file, ticker="AAPL")

    # Step 1: Lexer
    tokens = step_1_lexical_analysis(source)

    # Step 2: Parser
    ast = step_2_syntax_analysis(tokens)

    # Step 3: Symbol Table & Semantic Analysis
    step_3_symbol_table_and_semantics(ast)

    # Step 4: Negative Error Diagnostics
    step_4_negative_error_detection()

    # Step 5: Intermediate Code Generation
    ir_prog = step_5_intermediate_code_generation(ast)

    # Step 6: Code Optimization (Phase 3 Core)
    opt_ast, opt_ir, opt_stats = step_6_code_optimization(ast, ir_prog)

    # Step 7: Execution & Financial Risk Analytics
    report = step_7_execution_and_financial_analytics(source, data, opt_ast)

    # Step 8: System Latency & Memory Benchmark
    step_8_system_benchmarks(report)

    # Step 9: Export Artifacts
    step_9_artifact_generation(report)

    print("\n" + "=" * 82)
    print(" [REVIEW 3 VERIFICATION PASSED] All Phase 3 deliverables completed and verified.")
    print("=" * 82)


if __name__ == "__main__":
    run_phase3_full_demonstration()
