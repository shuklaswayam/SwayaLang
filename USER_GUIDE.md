# SwayaLang User Guide & Operational Manual
**Course:** BCSE307P — Compiler Design Laboratory  
**Author:** Swayam Shukla (Reg No: 24BCE0751)  
**Institution:** School of Computer Science & Engineering, Vellore Institute of Technology  
**Version:** 3.0.0 (Phase 3 Final Production Release)

---

## 1. Introduction

**SwayaLang** is a specialized Domain-Specific Language (DSL), optimizing multi-pass compiler, and high-performance vector backtesting execution engine tailored for quantitative stock trading strategies. 

Traditional algorithmic trading environments suffer from high boilerplate, runtime type errors in dynamic scripts, lookahead data leaks, and unoptimized condition evaluations. SwayaLang eliminates these vulnerabilities by providing:
1. **Front-End Compiler Pipeline:** Lexical analysis, recursive-descent syntax parsing into an immutable typed Abstract Syntax Tree (AST), and scoped symbol table validation.
2. **Intermediate Representation (IR):** Linearized Three-Address Code (TAC) Quadruple representation decoupling grammar from runtime execution.
3. **Phase 3 Optimizing Engine:** Constant folding, algebraic identity simplification, boolean short-circuit propagation, global Common Subexpression Elimination (CSE via value numbering for pure indicators), and dead-code pruning.
4. **Execution & Risk Engine:** Lookahead-free vector indicator engine (SMA, EMA, RSI) and full financial risk profiler (Sharpe, Sortino, Max Drawdown, Profit Factor, CAGR %).
5. **Interactive Developer Tooling:** Dual-mode interfaces consisting of a full-featured Command-Line Interface (`driver.py`) and a modern web-based visual IDE (`app.py`).

---

## 2. Installation & Prerequisites

### 2.1 System Requirements
- **Operating System:** macOS (Apple Silicon / Intel), Linux (Ubuntu, Debian, Fedora), or Windows 10/11 (via WSL2 or Native PowerShell).
- **Python Runtime:** Python 3.10, 3.11, or 3.12 (Python 3.12 recommended).
- **Disk Space:** ~50 MB for repository, virtual environment, and generated presentation assets.

### 2.2 Environment Setup
Clone or extract the repository and install dependencies into an isolated virtual environment:

```bash
# 1. Navigate to the project root
cd /path/to/Compiler_Design_Proj

# 2. (Optional) Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install core dependencies
pip install -r requirements.txt
```

### 2.3 Dependency Manifest
| Package | Version | Purpose |
| :--- | :--- | :--- |
| `flask` | `>= 3.0.0` | Lightweight REST API server for the Web IDE |
| `matplotlib` | `>= 3.8.0` | Dark-mode financial equity curve and drawdown chart plotting |
| `pytest` | `>= 8.0.0` | Comprehensive unit and integration test framework |
| `python-pptx` | `>= 0.6.21` | Programmatic presentation slide deck generator |
| `reportlab` | `>= 4.0.0` | Publication-grade academic PDF report builder |

---

## 3. Language Syntax & Strategy Specification

A SwayaLang trading strategy file (`.strat`) consists of four primary blocks:
1. `strategy <Name>:` Strategy header defining the identifier.
2. `capital <Number>;` Initial cash allocation for simulation.
3. `indicators:` Declarations of technical indicators with lookback periods.
4. `rules:` Ordered sequence of conditional trading directives.

### 3.1 Minimal Example (`simple_sma.strat`)
```swayalang
strategy SimpleTrend:
    capital 100000;

    indicators:
        sma_20 = SMA(close, 20);
        sma_50 = SMA(close, 50);
        rsi_14 = RSI(close, 14);

    rules:
        # Long entry when fast moving average crosses above slow moving average
        BUY 100 SHARES WHEN sma_20 > sma_50 AND rsi_14 < 70;

        # Risk-managed exit with stop-loss or profit target
        SELL 100 SHARES WHEN close < ENTRY_PRICE * 0.95 OR close > ENTRY_PRICE * 1.10;
```

### 3.2 Supported Technical Indicators
- `SMA(field, period)`: Simple Moving Average over `period` bars (e.g., `SMA(close, 20)`).
- `EMA(field, period)`: Exponential Moving Average with smoothing factor $\alpha = \frac{2}{N+1}$.
- `RSI(field, period)`: Relative Strength Index measuring momentum on a $[0, 100]$ scale.

### 3.3 Historical Price Fields & Built-in Variables
- Price Fields: `open`, `high`, `low`, `close`, `volume`.
- Contextual Variables:
  - `ENTRY_PRICE`: Execution price of currently active position.
  - `BARS_HELD`: Integer count of bars elapsed since position entry.
  - `CURRENT_BAR`: Current 0-indexed simulation bar index.

### 3.4 Supported Actions
- `BUY <quantity> SHARES WHEN <condition>;`
- `SELL <quantity> SHARES WHEN <condition>;`
- `HOLD WHEN <condition>;`

---

## 4. Command-Line Interface (CLI) Usage

The unified CLI entry point is [driver.py](file:///Users/swayamshukla/Compiler_Design_Proj/driver.py).

### 4.1 CLI Options Summary
```text
usage: driver.py [-h] [--compile] [--ir] [--optimize] [--execute DATA_FILE]
                 [--report] [--benchmark] [--plot [PLOT_FILE]]
                 [--export-json JSON_FILE] [--export-csv CSV_FILE]
                 [--demo3] [--summary]
                 [file]
```

### 4.2 Standard Operational Workflows

#### A. Compile & Validate (Front-End Stages)
Validates lexical syntax, parses to AST, and performs semantic type/scope validation:
```bash
python3 driver.py examples/golden_cross.strat --compile
```

#### B. Generate Intermediate Representation (Three-Address Code)
Emits linearized quadruple instructions for both unoptimized and optimized intermediate representations:
```bash
# Generate unoptimized TAC
python3 driver.py examples/golden_cross.strat --ir

# Generate unoptimized AND optimized TAC side-by-side with instruction savings
python3 driver.py examples/golden_cross.strat --ir --optimize
```

#### C. Run Backtest Simulation Against Historical Data
Executes the strategy against historical CSV bar data (e.g. `data/AAPL_daily.csv`):
```bash
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv
```

#### D. Full Financial Risk Profiling & Metrics
Computes Wall-Street standard quantitative metrics (Sharpe ratio, Sortino ratio, Max Drawdown, CAGR %, Profit Factor):
```bash
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv --report
```

#### E. Generate Equity Curve Visualization Chart
Automatically saves a high-DPI dark-mode equity curve with underwater drawdown chart:
```bash
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv --plot
# Or specify a custom output path:
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv --plot custom_equity.png
```

#### F. Benchmark Compilation & Execution Latency
Profiles millisecond-level stage latencies (Lexing, Parsing, Semantic Checking, TAC Generation, Optimization, Indicator Precomputation, and Bar Simulation):
```bash
python3 driver.py examples/golden_cross.strat --execute data/AAPL_daily.csv --benchmark
```

#### G. Interactive Review 3 Evaluation Demonstration
Launches the 9-step automated laboratory evaluation sequence:
```bash
python3 driver.py --demo3
```

---

## 5. Web-Based Integrated Development Environment (Web IDE)

For interactive graphical evaluation, SwayaLang includes a modern web-based IDE built with Flask and Vanilla CSS/JS.

### 5.1 Launching the Web Server
```bash
python3 app.py
```
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

### 5.2 Interface Capabilities & Tabs
1. **Strategy Editor:** Real-time syntax editor pre-loaded with example trading strategies (`Golden Cross`, `RSI Reversal`, `Multi-Rule Breakout`).
2. **Tokens Tab:** Displays the token stream generated by the Lexical Analyzer (`compiler/lexer.py`), showing token types, values, line numbers, and column offsets.
3. **AST Tab:** Interactive JSON tree rendering the typed Abstract Syntax Tree nodes.
4. **Symbol Table Tab:** Displays registered indicators, price fields, user variables, and their resolved data types and scoping attributes.
5. **IR / TAC Tab:** Displays raw Three-Address Code quadruples (`OP, ARG1, ARG2, RESULT`).
6. **Optimizer Tab (Phase 3 Core):** Displays side-by-side unoptimized vs. optimized TAC, highlighting constant-folded lines and eliminated redundant subexpressions, along with a transformation audit log.
7. **Benchmark Tab (Phase 3 Core):** Displays real-time latency breakdowns per compiler stage, peak memory utilization (`tracemalloc`), and throughput metrics (`bars/sec`).
8. **Equity Curve & Trades Panel:** Visualizes interactive performance metrics, closed trade logs, and PnL breakdowns.

---

## 6. Running Test Suites & Performance Benchmarks

### 6.1 Pytest Automated Test Suite
To run the full suite of 84 automated unit and integration tests:
```bash
pytest -v
```
All 84 tests cover:
- Lexical edge cases, invalid character trapping, comment stripping.
- Recursive-descent grammar rules and frozen dataclass AST nodes.
- Scoped symbol table lookups and semantic type checkers.
- Three-Address Code generation and quadruple formatting.
- Phase 3 constant folding, algebraic simplification, boolean short-circuiting, and CSE.
- High-precision financial risk formulas (Sharpe, Sortino, Max Drawdown).
- End-to-end integration and CLI driver flag combinations.

### 6.2 Empirical Scaling Benchmarks
To measure execution scaling across dataset sizes (100, 500, 1,000, 5,000, and 10,000 bars) and export scaling charts:
```bash
python3 benchmark.py
```
This generates `presentation_assets/benchmark_scaling_chart.png` and logs stage latencies.

---

## 7. Error Handling & Diagnostic Catalog

SwayaLang implements precise compiler diagnostic messages with source line and column coordinates:

| Error Type | Example Trigger | Diagnostic Message |
| :--- | :--- | :--- |
| **Lexical Error** | Unexpected character `@` | `LexerError: Unexpected character '@' at line 4, col 12` |
| **Syntax Error** | Missing colon after strategy name | `ParserError: Expected ':' after strategy name at line 1, col 23` |
| **Semantic Error** | Indicator period $\le 0$ | `SemanticError: Indicator 'SMA' period must be positive at line 5, col 9` |
| **Semantic Error** | Lookback period $> 500$ | `SemanticError: Lookback period 1000 exceeds maximum safety limit (500) at line 6, col 9` |
| **Semantic Error** | Undeclared variable | `SemanticError: Undefined variable 'unknown_var' referenced at line 8, col 15` |
| **Runtime Error** | Insufficient data bars | `SimulationError: Dataset has 45 bars, but strategy requires at least 200 bars` |

---

## 8. Summary of Project Deliverables

| Deliverable | Location |
| :--- | :--- |
| **Working Project & Source Code** | `compiler/`, `app.py`, `driver.py` |
| **Test Cases & Test Results** | `tests/`, `test_results.txt` (84/84 Passed) |
| **Output Evidence & Screenshots** | `presentation_assets/` (Terminal steps, Pytest, Scaling chart) |
| **Final Project Report (PDF & Markdown)** | `FINAL_PROJECT_REPORT.pdf`, `FINAL_PROJECT_REPORT.md` |
| **Presentation Slide Deck (PPTX & PDF)** | `SwayaLang_Phase3_Presentation.pptx`, `SwayaLang_Phase3_Presentation.pdf` |
| **User Instructions** | `USER_GUIDE.md` (This document) |

---
*For questions, assistance, or laboratory evaluation inquiries, refer to `FINAL_PROJECT_REPORT.pdf` Chapter 14 (Viva Voce Technical Defense).*
