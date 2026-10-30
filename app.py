"""
app.py — SwayaLang Web IDE Backend (Flask REST API — Phase 3 Final)
====================================================================
Serves the web IDE and exposes API endpoints that run the complete
3-phase compiler pipeline in-process and return structured JSON
for the frontend to render:
  - Tokens & AST Hierarchy
  - Scoped Symbol Table Scopes
  - Unoptimized & Optimized TAC Quadruples with side-by-side diff
  - Quantitative Optimization Audit (folds, CSE, dead code pruning)
  - Quantitative Financial Metrics (Sharpe, Sortino, Drawdown, CAGR)
  - Compiler Systems Benchmarks (Stage latencies, memory footprint, throughput)

Endpoints:
    POST /api/compile   — Run full or partial pipeline, return JSON results
    POST /api/download_csv — Download trade history log as CSV
    GET  /api/examples  — Return list of bundled example strategies

Usage:
    python app.py
    # Opens on http://localhost:5001
"""

from __future__ import annotations

import csv
import io
import json
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, Response, jsonify, render_template, request, send_from_directory

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
    FinancialMetrics,
    ReportGenerator,
)
from compiler.semantic import SemanticAnalyzer, SemanticError
from compiler.symbol_table import SymbolTable

app = Flask(__name__, static_folder="frontend/static", template_folder="frontend")

EXAMPLES_DIR = Path("examples")
DATA_DIR = EXAMPLES_DIR / "data"


# ---------------------------------------------------------------------------
# Helper serialisers
# ---------------------------------------------------------------------------

def _token_to_dict(tok: Token) -> dict:
    return {
        "type": tok.type.name,
        "value": str(tok.value),
        "line": tok.line,
        "col": tok.col,
    }


def _ast_to_dict(node) -> dict:
    """Recursively serialise an AST node to a plain dict."""
    if node is None:
        return None
    name = type(node).__name__
    d: dict = {"_node": name}
    for k, v in vars(node).items():
        if k.startswith("_"):
            continue
        if isinstance(v, list):
            d[k] = [_ast_to_dict(item) if hasattr(item, "__dict__") else item for item in v]
        elif hasattr(v, "__dict__"):
            d[k] = _ast_to_dict(v)
        else:
            d[k] = v
    return d


def _symtab_to_dict(symtab: SymbolTable) -> dict:
    """Serialise symbol table scopes to JSON-friendly structure."""
    scopes = []
    for scope in symtab.all_scopes:
        entries = []
        for name, sym in scope.symbols.items():
            entries.append({
                "name": name,
                "kind": str(getattr(sym, "kind", "")),
                "type": str(getattr(sym, "data_type", "")),
                "value": str(sym.extra.get("description", "") if hasattr(sym, "extra") else ""),
            })
        scopes.append({"scope_name": scope.name, "symbols": entries})
    return {"scopes": scopes}


def _report_to_dict(report: BacktestReport) -> dict:
    trades = []
    for t in report.trades:
        trades.append({
            "id": t.trade_id,
            "bar": t.bar,
            "date": t.date,
            "ticker": t.ticker,
            "action": t.action,
            "shares": t.shares,
            "price": round(t.price, 4),
            "total_value": round(t.total_value, 2),
            "cash_after": round(t.cash_after, 2),
            "realized_pnl": round(t.realized_pnl, 4) if t.realized_pnl is not None else None,
            "return_pct": round(t.return_pct, 4) if t.return_pct is not None else None,
            "rule_kind": t.rule_kind,
        })
    return {
        "strategy_name": report.strategy_name,
        "ticker": report.ticker,
        "total_bars": report.total_bars,
        "initial_capital": report.initial_capital,
        "final_equity": round(report.final_equity, 2),
        "net_profit": round(report.net_profit, 2),
        "return_pct": round(report.return_pct, 4),
        "total_trades": report.total_trades,
        "winning_trades": report.winning_trades,
        "losing_trades": report.losing_trades,
        "win_rate_pct": round(report.win_rate_pct, 2),
        "max_drawdown_pct": round(report.max_drawdown_pct, 4),
        "equity_curve": [round(v, 2) for v in report.equity_curve],
        "trades": trades,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/examples")
def get_examples():
    """Return list of bundled strategy example names and their source."""
    examples = []
    if EXAMPLES_DIR.is_dir():
        for f in sorted(EXAMPLES_DIR.glob("*.strat")):
            if "invalid" in f.name:
                continue
            examples.append({
                "name": f.stem,
                "filename": f.name,
                "source": f.read_text(encoding="utf-8"),
            })
    return jsonify(examples)


@app.route("/api/compile", methods=["POST"])
def compile_endpoint():
    """
    Run SwayaLang compiler pipeline with Phase 3 Optimization and Benchmarks.
    """
    body = request.get_json(force=True, silent=True) or {}
    source: str = body.get("source", "")
    stages: list = body.get("stages", ["tokens", "ast", "symbols", "ir", "optimize", "run", "benchmark"])
    capital: float = float(body.get("capital", 100_000.0))
    data_key: str = body.get("data", "AAPL")

    result: dict = {
        "ok": True,
        "error": None,
        "tokens": None,
        "ast": None,
        "symbols": None,
        "warnings": [],
        "ir": None,
        "optimized_ir": None,
        "optimization": None,
        "benchmark": None,
        "financial": None,
        "report": None,
    }

    try:
        # Stage 1 — Lexer
        lexer = Lexer(source)
        tokens: list[Token] = lexer.tokenize()
        if "tokens" in stages:
            result["tokens"] = [_token_to_dict(t) for t in tokens]

        # Stage 2 — Parser / AST
        parser = Parser(tokens)
        prog_ast: ProgramNode = parser.parse()
        if "ast" in stages:
            result["ast"] = _ast_to_dict(prog_ast)

        # Stage 3 — Symbol Table + Semantic Analysis
        analyzer = SemanticAnalyzer(fail_fast=False)
        symtab, errors, warnings = analyzer.analyze(prog_ast)
        result["warnings"] = warnings

        if errors:
            err = errors[0]
            result["ok"] = False
            result["error"] = {
                "stage": "semantic",
                "message": str(err),
                "line": getattr(err, "line", None),
                "col": getattr(err, "col", None),
            }
            if "symbols" in stages:
                result["symbols"] = _symtab_to_dict(symtab)
            return jsonify(result)

        if "symbols" in stages:
            result["symbols"] = _symtab_to_dict(symtab)

        # Stage 4 — IR Generation (TAC)
        ir_gen = IRGenerator()
        ir_prog = ir_gen.generate(prog_ast)
        if "ir" in stages:
            result["ir"] = ir_prog.dump()

        # Stage 5 — Code Optimization (Phase 3 Core)
        optimizer = Optimizer()
        opt_ast, opt_ir, opt_stats = optimizer.optimize(prog_ast, ir_prog)
        if opt_ir is not None:
            result["optimized_ir"] = opt_ir.dump()
        result["optimization"] = {
            "initial_quad_count": opt_stats.initial_quad_count,
            "optimized_quad_count": opt_stats.optimized_quad_count,
            "instructions_eliminated": opt_stats.instructions_eliminated,
            "reduction_pct": round(opt_stats.reduction_pct, 2),
            "constant_folds": opt_stats.constant_folds,
            "constant_propagations": opt_stats.constant_propagations,
            "cse_eliminations": opt_stats.cse_eliminations,
            "dead_code_eliminations": opt_stats.dead_code_eliminations,
            "redundant_jumps_eliminated": opt_stats.redundant_jumps_eliminated,
            "transformation_log": opt_stats.transformation_log,
        }

        # Market Data selection
        csv_path = DATA_DIR / f"{data_key.upper()}_daily.csv"
        if csv_path.is_file():
            market_data = MarketData.from_csv(csv_path, ticker=data_key.upper())
        else:
            market_data = MarketData.generate_synthetic(ticker=data_key.upper(), n_bars=200)

        # Stage 6 & 7 — Execution & Comprehensive Benchmarking
        if "run" in stages or "benchmark" in stages:
            comp_report, _ = BenchmarkRunner.measure_pipeline(
                source=source,
                market_data=market_data,
                capital=capital,
                enable_optimization=True,
            )
            result["report"] = _report_to_dict(
                BacktestReport(
                    strategy_name=comp_report.strategy_name,
                    ticker=comp_report.ticker,
                    total_bars=comp_report.total_bars,
                    initial_capital=comp_report.financial.initial_capital,
                    final_equity=comp_report.financial.final_equity,
                    net_profit=comp_report.financial.net_profit,
                    return_pct=comp_report.financial.return_pct,
                    total_trades=comp_report.financial.total_trades,
                    winning_trades=comp_report.financial.winning_trades,
                    losing_trades=comp_report.financial.losing_trades,
                    win_rate_pct=comp_report.financial.win_rate_pct,
                    max_drawdown_pct=comp_report.financial.max_drawdown_pct,
                    trades=comp_report.trades,
                    equity_curve=comp_report.equity_curve,
                )
            )
            result["financial"] = asdict(comp_report.financial)
            result["benchmark"] = {
                "total_time_ms": comp_report.benchmark.total_time_ms,
                "peak_memory_kb": comp_report.benchmark.peak_memory_kb,
                "bars_processed": comp_report.benchmark.bars_processed,
                "bars_per_second": comp_report.benchmark.bars_per_second,
                "timings": [asdict(t) for t in comp_report.benchmark.timings],
            }

    except LexError as e:
        result["ok"] = False
        result["error"] = {"stage": "lexer", "message": str(e), "line": getattr(e, "line", None), "col": getattr(e, "col", None)}
    except ParseError as e:
        result["ok"] = False
        result["error"] = {"stage": "parser", "message": str(e), "line": getattr(e, "line", None), "col": getattr(e, "col", None)}
    except SemanticError as e:
        result["ok"] = False
        result["error"] = {"stage": "semantic", "message": str(e), "line": getattr(e, "line", None), "col": getattr(e, "col", None)}
    except Exception as e:
        result["ok"] = False
        result["error"] = {"stage": "runtime", "message": str(e), "line": None, "col": None}

    return jsonify(result)


@app.route("/api/download_csv", methods=["POST"])
def download_csv():
    """Return trade log as downloadable CSV."""
    body = request.get_json(force=True, silent=True) or {}
    trades = body.get("trades", [])
    if not trades:
        return Response("No trade data", status=400)

    si = io.StringIO()
    writer = csv.DictWriter(
        si,
        fieldnames=["id", "date", "ticker", "action", "shares", "price", "total_value", "cash_after", "realized_pnl", "return_pct", "rule_kind"],
    )
    writer.writeheader()
    writer.writerows(trades)
    output = si.getvalue()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=swayalang_trades.csv"},
    )


if __name__ == "__main__":
    print("═" * 60)
    print("  SwayaLang Web IDE (Phase 3 Final)  →  http://localhost:5001")
    print("═" * 60)
    app.run(debug=True, port=5001)
