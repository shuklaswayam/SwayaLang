# SwayaLang

**SwayaLang** is a specialized Domain-Specific Language (DSL), optimizing multi-pass compiler, and high-performance vector backtesting execution engine for expressing rule-based stock trading strategies — built from scratch in Python 3.

> **Compiler Design Laboratory (BCSE307P)** — Vellore Institute of Technology  
> **Author:** Swayam Shukla (Reg No: **24BCE0751**)  
> **Status:** Phase 3 Final Production Release (Review 3 Complete) — **84/84 Tests Passing (100%)**

---

## What It Does

Instead of writing fragile, ad-hoc backtesting scripts for every new trading idea, you express your strategy declaratively in SwayaLang:

```swayalang
STRATEGY "GoldenCross" {
    INDICATOR sma_50  = SMA(CLOSE, 50)
    INDICATOR sma_200 = SMA(CLOSE, 200)
    INDICATOR rsi_14  = RSI(CLOSE, 14)

    ENTRY:     BUY 100 SHARES OF "AAPL"  IF sma_50 > sma_200 AND rsi_14 < 30
    EXIT:      SELL ALL                   IF sma_50 < sma_200
    STOP_LOSS: SELL ALL                   IF PRICE < ENTRY_PRICE * (1.0 - 0.05)
}
```

The SwayaLang system **lexes**, **parses**, **semantically validates**, **translates to Three-Address Code (TAC)**, **optimizes via multi-pass constant folding, algebraic simplification, and Common Subexpression Elimination (CSE)**, and **executes** the strategy against historical OHLCV market data — producing institutional-grade quantitative risk metrics (Sharpe ratio, Sortino ratio, Max Drawdown %, CAGR %, Profit Factor) and dark-mode equity curve visualizations.

---

## Compiler Architecture & Pipeline

```
Source (.strat)
    │
    ▼
┌─────────┐   Token stream   ┌──────────┐   AST   ┌──────────────────┐
│  Lexer  │ ──────────────▶  │  Parser  │ ──────▶ │ Semantic Analyzer│
└─────────┘                  └──────────┘         └──────────────────┘
                                                           │ Scoped Annotated AST
                                                           ▼
                                                  ┌──────────────────┐
                                                  │   IR Generator   │
                                                  └──────────────────┘
                                                           │ Linearized TAC Quadruples
                                                           ▼
                                                  ┌──────────────────┐
                                                  │  Phase 3 Opt     │
                                                  │ (Fold/Ident/CSE) │
                                                  └──────────────────┘
                                                           │ Optimized TAC
                                                           ▼
                                              OHLCV CSV ─▶ ┌─────────────┐
                                                           │ Interpreter │
                                                           └─────────────┘
                                                                  │ Execution & Trades
                                                                  ▼
                                                        ┌──────────────────┐
                                                        │ Financial Report │
                                                        │  & Risk Engine   │
                                                        └──────────────────┘
                                                                  │
                                                Sharpe, Sortino, Drawdown, Latency
```

### Pipeline Modules & Implementation Status

| Stage | Module | Phase | Status | Key Techniques |
| :--- | :--- | :---: | :---: | :--- |
| **Lexer** | `compiler/lexer.py` | 1 | Complete | Regex DFA tokenization, line/col tracking, comments `#` |
| **Parser** | `compiler/parser.py` | 1 | Complete | Recursive-descent parser, operator precedence, grammar |
| **AST Nodes** | `compiler/ast_nodes.py` | 1 | Complete | Immutable frozen dataclasses, structured visitor support |
| **Symbol Table** | `compiler/symbol_table.py` | 2 | Complete | Hierarchical scopes, lexical isolation, symbol attributes |
| **Semantic Analyzer** | `compiler/semantic.py` | 2 | Complete | Type checking, period validation ($\le 500$), domain rules |
| **IR Generator (TAC)** | `compiler/ir.py` | 2 | Complete | Quadruple format `(OP, ARG1, ARG2, RES)`, temporaries, labels |
| **Optimizer** | `compiler/optimizer.py` | 3 | Complete | Constant folding, algebraic identities, boolean laws, CSE, DCE |
| **Execution Engine** | `compiler/interpreter.py` | 2 | Complete | Lookahead-free vector indicators, portfolio state machine |
| **Report Generator** | `compiler/reporter.py` | 3 | Complete | Sharpe, Sortino, Drawdown, CAGR, microsecond profiling |
| **Driver CLI** | `driver.py` | 1–3 | Complete | Unified multi-phase CLI with 12 operational flags |
| **Web IDE** | `app.py` + `frontend/` | 3 | Complete | Flask REST API, 7-tab GUI, side-by-side optimizer diffs |
| **Benchmark Suite** | `benchmark.py` | 3 | Complete | Empirical scaling across 100 to 10,000 bars, chart export |
| **Demonstration** | `demonstrate_phase3.py` | 3 | Complete | Automated 9-step interactive lab evaluation walkthrough |

---

## Project Structure

```
Compiler_Design_Proj/
├── GRAMMAR.md                       ← Formal EBNF grammar specification
├── README.md                        ← Project overview, architecture & status
├── USER_GUIDE.md                    ← Complete user instructions and operational manual
├── FINAL_PROJECT_REPORT.md          ← 15-chapter IEEE-style comprehensive project report
├── FINAL_PROJECT_REPORT.pdf         ← Publication-grade compiled PDF report (16 pages)
├── SwayaLang_Phase3_Presentation.pptx← 18-slide widescreen (16:9) presentation deck
├── SwayaLang_Phase3_Presentation.pdf ← Keynote vector-rendered presentation PDF
├── driver.py                        ← Unified CLI entry point (Phases 1, 2, and 3)
├── app.py                           ← SwayaLang Web IDE (Flask backend)
├── benchmark.py                     ← Empirical latency and scaling benchmark runner
├── demonstrate_phase3.py            ← 9-step interactive Review 3 lab evaluation script
├── build_report_pdf.py              ← ReportLab academic PDF builder with custom canvas
├── build_phase3_ppt.py              ← Programmatic presentation generator (python-pptx)
├── test_results.txt                 ← Automated test results log (84/84 passed)
│
├── compiler/                        ← Core compiler pipeline modules
│   ├── __init__.py                  ← Package exports and unified pipeline runner
│   ├── lexer.py                     ← Tokenizer (Phase 1)
│   ├── ast_nodes.py                 ← Typed immutable AST nodes (Phase 1)
│   ├── parser.py                    ← Recursive-descent parser (Phase 1)
│   ├── symbol_table.py              ← Scoped symbol table (Phase 2)
│   ├── semantic.py                  ← Semantic analyzer & safety traps (Phase 2)
│   ├── ir.py                        ← Three-Address Code Quadruple generator (Phase 2)
│   ├── optimizer.py                 ← Phase 3 Multi-pass TAC & AST optimizer
│   ├── interpreter.py               ← Lookahead-free vector execution engine (Phase 2)
│   └── reporter.py                  ← Phase 3 Quantitative risk & profiling engine
│
├── frontend/                        ← SwayaLang Web IDE frontend assets
│   ├── index.html                   ← Modern 7-tab single-page interface
│   └── static/
│       ├── style.css                ← Dark/glassmorphic responsive stylesheet
│       └── app.js                   ← Reactive UI controller, syntax highlighting & diffs
│
├── presentation_assets/             ← High-DPI terminal screenshots and charts
│   ├── benchmark_scaling_chart.png  ← Multi-scale latency benchmark chart
│   ├── equity_curve_chart.png       ← Financial equity & drawdown curve
│   ├── terminal_step1_lexer.png     ← Terminal evidence: Lexer tokens
│   ├── terminal_step2_ast.png       ← Terminal evidence: AST hierarchy
│   ├── terminal_step3_semantic.png  ← Terminal evidence: Symbol table & semantic check
│   ├── terminal_step4_tac_opt.png   ← Terminal evidence: TAC optimization & CSE
│   ├── terminal_step5_report.png    ← Terminal evidence: Quantitative financial report
│   ├── terminal_step6_negative.png  ← Terminal evidence: Semantic safety traps
│   ├── terminal_step7_scope.png     ← Terminal evidence: Multi-strategy scope isolation
│   └── terminal_step8_pytest.png    ← Terminal evidence: Pytest 84/84 passing suite
│
├── examples/                        ← Sample .strat trading strategies
│   ├── golden_cross.strat           ← Moving average crossover + RSI filter
│   ├── rsi_oversold.strat           ← Mean reversion + TAKE_PROFIT target
│   ├── multi_rule.strat             ← Comprehensive 4-rule strategy (ENTRY, EXIT, SL, TP)
│   ├── multi_strategy.strat         ← Multi-strategy file verifying scope isolation
│   ├── invalid_semantic_undeclared.strat ← Negative test (undeclared variable)
│   ├── invalid_semantic_type.strat  ← Negative test (period <= 0)
│   └── data/                        ← Historical OHLCV market datasets
│       ├── AAPL_daily.csv           ← 220 bars AAPL daily OHLCV
│       └── TSLA_daily.csv           ← 150 bars TSLA daily OHLCV
│
└── tests/                           ← Automated pytest suite (84 tests, 100% pass)
    ├── test_lexer.py                ← Lexer unit tests (Phase 1)
    ├── test_parser.py               ← Parser unit tests (Phase 1)
    ├── test_ast.py                  ← AST pretty-print tests (Phase 1)
    ├── test_symbol_table.py         ← Scoped symbol table tests (Phase 2)
    ├── test_semantic.py             ← Semantic analyzer & type checking tests (Phase 2)
    ├── test_ir.py                   ← Three-Address Code generator tests (Phase 2)
    ├── test_optimizer.py            ← Phase 3 Optimizer unit tests (folding, identities, CSE)
    ├── test_interpreter.py          ← Vector execution & trade simulator tests (Phase 2)
    ├── test_reporter.py             ← Phase 3 Quantitative risk formulas tests
    ├── test_phase3_integration.py   ← Phase 3 End-to-end integration & optimization tests
    └── test_driver.py               ← CLI driver tests across all 12 operational flags
```

---

## Quick Start Guide

### 1. Requirements & Setup
```bash
# Clone or enter the workspace
cd Compiler_Design_Proj

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Automated Test Suite (84 Tests)
```bash
pytest -v
```
Output:
```text
============================== 84 passed in 3.67s ==============================
```

### 3. Run the Interactive Review 3 Demonstration
```bash
python3 driver.py --demo3
```
Walks through all 9 evaluation steps:
1. Lexical Analysis (`compiler/lexer.py`)
2. Recursive-Descent Parsing & AST (`compiler/parser.py`)
3. Symbol Table & Semantic Checking (`compiler/symbol_table.py`, `compiler/semantic.py`)
4. Three-Address Code & Multi-Pass Optimizer (`compiler/optimizer.py`)
5. Backtest Execution & Risk Profiling (`compiler/interpreter.py`, `compiler/reporter.py`)
6. Semantic Safety Traps & Error Handling
7. Multi-Strategy Scope Isolation
8. Pytest Test Suite Validation (84/84 Tests)
9. Web IDE & Tooling Verification

### 4. CLI Driver Commands

```bash
# Compile and check syntax & semantics
python3 driver.py examples/golden_cross.strat --compile

# Generate TAC Quadruples with Phase 3 Optimization
python3 driver.py examples/golden_cross.strat --ir --optimize

# Backtest against historical data and print quantitative risk profile
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv --report

# Export high-DPI dark-mode equity curve plot
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv --plot

# Benchmark latency and peak memory across compiler stages
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv --benchmark
```

### 5. Launch the Web IDE
```bash
python3 app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser to inspect interactive token streams, AST nodes, symbol tables, raw/optimized TAC diffs, benchmark meters, and trade logs.

---

## Phase 3 Core Contributions (Optimization & Profiling)

### 1. Multi-Pass TAC & AST Optimization (`compiler/optimizer.py`)
- **Constant Folding:** Statically computes constant arithmetic at compile time:
  $$\text{ENTRY\_PRICE} \times (1.0 - 0.05) \longrightarrow \text{ENTRY\_PRICE} \times 0.95$$
- **Algebraic Identities:** Eliminates redundant neutral operations:
  $$x \times 1 \longrightarrow x, \quad x + 0 \longrightarrow x, \quad x - 0 \longrightarrow x, \quad x \times 0 \longrightarrow 0$$
- **Boolean Short-Circuit Laws:**
  $$\text{True AND } P \longrightarrow P, \quad \text{False AND } P \longrightarrow \text{False}$$
- **Global Common Subexpression Elimination (CSE):** Utilizes value numbering over pure indicator calculations and price fields across rules within a strategy, eliminating identical recalculations.
- **Dead Code Elimination (DCE):** Prunes unused intermediate temporaries and unreferenced labels.
- **Audit Verification:** Delivers up to **28.6% instruction reduction** on complex multi-rule strategies while preserving exact bitwise trading equivalence.

### 2. Quantitative Financial Risk Profiling (`compiler/reporter.py`)
Computes institutional risk metrics:
- **Sharpe Ratio:** $\frac{R_p - R_f}{\sigma_p \cdot \sqrt{252}}$ (annualized risk-adjusted excess return).
- **Sortino Ratio:** $\frac{R_p - R_f}{\sigma_d \cdot \sqrt{252}}$ (penalizing only downside volatility).
- **Maximum Drawdown (MDD):** $\max_{t} \left(\frac{\text{Peak}_t - \text{Equity}_t}{\text{Peak}_t}\right) \times 100\%$.
- **Compound Annual Growth Rate (CAGR %):** $\left(\frac{\text{Ending Equity}}{\text{Starting Equity}}\right)^{\frac{252}{N}} - 1$.
- **Profit Factor & Win Rate:** Ratio of gross profits to gross losses and percentage of profitable trades.

### 3. Empirical Systems Scaling & Performance
Benchmarked across dataset scales on Apple M-series hardware:
- **Throughput:** Exceeds **21,000 bars/sec** on historical trade simulation.
- **Front-End Compilation (Lex + Parse + Semantic + TAC):** $< 0.85\text{ ms}$.
- **Optimization Overhead:** $< 0.12\text{ ms}$.
- **Peak Memory Footprint:** $< 1.8\text{ MB}$ monitored via `tracemalloc`.

---

## Syllabus Rubric Alignment & Review 3 Deliverables

| Deliverable | File / Artifact | Review Criteria Addressed |
| :--- | :--- | :--- |
| **Complete Working Project** | `compiler/`, `app.py`, `driver.py` | Project Completion & Working Demo |
| **Complete Source Code** | Modular, PEP 8 typed code with docstrings | Code Quality & Architecture |
| **Test Cases (84 Tests)** | `tests/` (unit, integration, driver, negative) | Comprehensive Validation & Testing |
| **Test Results Evidence** | `test_results.txt` (84/84 passed in 3.67s) | Functional Correctness |
| **Screenshots & Output Evidence** | `presentation_assets/` (8 terminal runs + 2 charts) | Demonstration & Output Evidence |
| **Final Project Report (PDF)** | `FINAL_PROJECT_REPORT.pdf` (16 pages, ReportLab) | Quality of Project Report |
| **Final Project Report (Markdown)** | `FINAL_PROJECT_REPORT.md` (15 chapters) | Comprehensive Academic Documentation |
| **Presentation Slide Deck (PPTX)** | `SwayaLang_Phase3_Presentation.pptx` (18 slides) | Presentation & Visual Delivery |
| **Presentation Slide Deck (PDF)** | `SwayaLang_Phase3_Presentation.pdf` (Keynote export) | Cross-Platform Compatibility |
| **User Instructions** | `USER_GUIDE.md` (Installation, CLI, IDE, Syntax) | User Instructions |

---

## License & Academic Disclaimer

This project was developed for academic evaluation in the **Compiler Design Laboratory (BCSE307P)** at **Vellore Institute of Technology (VIT)**, 2026.  
All rights reserved © Swayam Shukla (24BCE0751).
