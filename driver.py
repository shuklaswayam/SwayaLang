"""
driver.py — SwayaLang Command-Line Driver
==========================================
Phase 1 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Read a ``.strat`` source file, run it through the SwayaLang lexer and
    parser, and print:
      1. The token stream (labelled, one token per line).
      2. The resulting AST in pretty-printed indented form.

Usage:
    python driver.py <path/to/strategy.strat>

Exit codes:
    0 — success
    1 — missing argument, file not found, LexError, or ParseError
"""

from __future__ import annotations

import sys
from pathlib import Path

from compiler.lexer import Lexer, LexError
from compiler.parser import Parser, ParseError


def run_pipeline(source: str) -> None:
    """Run lexer and parser stages and print token stream and AST."""
    # Stage 1: Lexical Analysis
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    print("── Token Stream ────────────────────────────────────────────────────────────")
    for tok in tokens:
        print(tok)

    # Stage 2: Syntax Analysis (Parsing & AST Construction)
    print("\n── Abstract Syntax Tree ────────────────────────────────────────────────────")
    parser = Parser(tokens)
    prog_ast = parser.parse()
    prog_ast.pretty_print()


def main() -> None:
    """Entry point: parse argv, lex, parse, and print output."""
    if len(sys.argv) < 2:
        print("Usage: python driver.py <path/to/strategy.strat>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.is_file():
        print(f"Error: File not found: '{file_path}'", file=sys.stderr)
        sys.exit(1)

    try:
        source = file_path.read_text(encoding="utf-8")
        run_pipeline(source)
    except LexError as err:
        print(f"{err}", file=sys.stderr)
        sys.exit(1)
    except ParseError as err:
        print(f"{err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
