"""
demonstrate_phase2.py — SwayaLang Phase 2 Interactive Review Demonstration
===========================================================================
Review 2: Implementation Progress Review
Course: Compiler Design Laboratory (BCSE307P)
Author: Swayam Shukla (24BCE0751)

This script provides an interactive step-by-step demonstration of the Phase 2
compiler pipeline deliverables according to Section 10 & 11 of the syllabus:
  1. Lexical Analysis & Token Stream
  2. Syntax Analysis & AST Construction
  3. Scoped Symbol Table Management
  4. Semantic Analysis & Type Checking (including Negative Error Detection)
  5. Intermediate Representation (Three-Address Code Quadruples)
  6. Execution Engine / Interpreter Simulation (Backtest against Real Market Data)
"""

import sys
from pathlib import Path

from compiler.ast_nodes import ProgramNode
from compiler.interpreter import Interpreter, MarketData
from compiler.ir import IRGenerator
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer, SemanticError


def print_banner(title: str, char: str = "="):
    print("\n" + char * 80)
    print(f" {title}")
    print(char * 80)


def step_1_lexical_analysis(source: str):
    print_banner("DEMO STEP 1: LEXICAL ANALYSIS (Token Stream & Classification)", "-")
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"Total tokens generated: {len(tokens)}")
    print("Sample tokens (first 10):")
    for t in tokens[:10]:
        print(f"  {t}")
    return tokens


def step_2_syntax_analysis(tokens):
    print_banner("DEMO STEP 2: SYNTAX ANALYSIS & AST GENERATION", "-")
    parser = Parser(tokens)
    ast = parser.parse()
    print("Pretty-printed Abstract Syntax Tree (AST):")
    ast.pretty_print()
    return ast


def step_3_symbol_table_and_semantic(ast):
    print_banner("DEMO STEP 3: SCOPED SYMBOL TABLE & SEMANTIC ANALYSIS", "-")
    analyzer = SemanticAnalyzer(fail_fast=True)
    symtab, errors, warnings = analyzer.analyze(ast)

    print("Scoped Symbol Table (Hierarchical Scopes):")
    print(symtab.format_table())

    print("\nSemantic Analysis Status:")
    print(f"  Errors:   {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    for w in warnings:
        print(f"    [WARNING] {w}")
    print("  Validation: ALL SEMANTIC & TYPE INVARIANTS PASSED")


def step_4_negative_error_detection():
    print_banner("DEMO STEP 4: SEMANTIC ERROR DETECTION (Negative Testing)", "-")

    bad_sources = [
        (
            "Undeclared Identifier",
            'STRATEGY "Err1" { ENTRY: BUY 100 SHARES OF "AAPL" IF unknown_ind > 50 }'
        ),
        (
            "Division by Zero",
            'STRATEGY "Err2" { ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > (100 / 0) }'
        ),
        (
            "Invalid Indicator Period",
            'STRATEGY "Err3" { INDICATOR bad = SMA(CLOSE, 0) ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > bad }'
        ),
        (
            "ENTRY_PRICE used in ENTRY rule",
            'STRATEGY "Err4" { ENTRY: BUY 100 SHARES OF "AAPL" IF PRICE < ENTRY_PRICE * 0.95 }'
        ),
    ]

    for title, src in bad_sources:
        print(f"\nTesting: {title}")
        try:
            tokens = Lexer(src).tokenize()
            ast = Parser(tokens).parse()
            SemanticAnalyzer(fail_fast=True).analyze(ast)
            print("  [FAIL] Error was not detected!")
        except SemanticError as err:
            print(f"  [SUCCESS] Caught expected {err}")


def step_5_intermediate_representation(ast):
    print_banner("DEMO STEP 5: INTERMEDIATE CODE GENERATION (Three-Address Code)", "-")
    ir_gen = IRGenerator()
    ir_prog = ir_gen.generate(ast)
    print(ir_prog.dump())


def step_6_execution_engine(ast):
    print_banner("DEMO STEP 6: EXECUTION ENGINE / INTERPRETER (Market Simulation)", "-")
    csv_file = Path("examples/data/AAPL_daily.csv")
    if csv_file.is_file():
        data = MarketData.from_csv(csv_file, ticker="AAPL")
        print(f"Loaded historical dataset: {csv_file} ({len(data)} trading days)")
    else:
        data = MarketData.generate_synthetic(ticker="AAPL", n_bars=120)
        print("Generated synthetic dataset (120 trading days)")

    interpreter = Interpreter(data, initial_capital=100000.0)
    reports = interpreter.run(ast)

    for report in reports:
        print(report.format_summary())


def main():
    print_banner("SWAYALANG — REVIEW 2 COMPILER DEMONSTRATION")
    print("Project: SwayaLang Trading DSL Compiler & Execution Engine")
    print("Course:  Compiler Design Laboratory (BCSE307P) — Review 2")
    print("Author:  Swayam Shukla (24BCE0751)\n")

    strat_file = Path("examples/multi_rule.strat")
    if not strat_file.is_file():
        strat_file = Path("examples/golden_cross.strat")

    print(f"Target Strategy File: {strat_file}")
    source = strat_file.read_text(encoding="utf-8")
    print("Source Code:")
    print("-" * 40)
    print(source.strip())
    print("-" * 40)

    # Execute all pipeline demonstration steps
    tokens = step_1_lexical_analysis(source)
    ast = step_2_syntax_analysis(tokens)
    step_3_symbol_table_and_semantic(ast)
    step_4_negative_error_detection()
    step_5_intermediate_representation(ast)
    step_6_execution_engine(ast)

    print_banner("ALL PHASE 2 REVIEW DEMONSTRATION STEPS COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
