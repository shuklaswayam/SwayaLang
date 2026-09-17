# SwayaLang

**SwayaLang** is a domain-specific language (DSL) and compiler/interpreter for
expressing rule-based stock-trading strategies — built from scratch in Python 3
as a complete compiler pipeline.

> Compiler Design Laboratory (BCSE307P) — VIT Vellore  
> Author: Swayam Shukla (24BCE0751)

---

## What It Does

Instead of writing ad-hoc backtesting scripts for every new trading idea, you
express your strategy declaratively in SwayaLang:

```
STRATEGY "GoldenCross" {
    INDICATOR sma_50  = SMA(CLOSE, 50)
    INDICATOR sma_200 = SMA(CLOSE, 200)
    INDICATOR rsi_14  = RSI(CLOSE, 14)

    ENTRY:     BUY 100 SHARES OF "AAPL"  IF sma_50 > sma_200 AND rsi_14 < 30
    EXIT:      SELL ALL                   IF sma_50 < sma_200
    STOP_LOSS: SELL ALL                   IF PRICE < ENTRY_PRICE * 0.95
}
```

The system then **lexes**, **parses**, **semantically validates**, **optimizes**,
and **executes** that specification against historical OHLCV data, producing a
simulated trade log and performance report.

---

## Compiler Pipeline

```
Source (.strat)
    │
    ▼
┌─────────┐   Token stream   ┌──────────┐   AST   ┌──────────────────┐
│  Lexer  │ ──────────────▶  │  Parser  │ ──────▶ │ Semantic Analyzer│
└─────────┘                  └──────────┘         └──────────────────┘
                                                           │ Annotated AST
                                                           ▼
                                                  ┌──────────────────┐
                                                  │   IR Generator   │
                                                  └──────────────────┘
                                                           │ Three-address code
                                                           ▼
                                                  ┌──────────────────┐
                                                  │    Optimizer     │
                                                  └──────────────────┘
                                                           │ Optimized IR
                                                           ▼
                                              OHLCV CSV ─▶ ┌─────────────┐
                                                           │ Interpreter │
                                                           └─────────────┘
                                                                 │ Trade log
                                                                 ▼
                                                        ┌──────────────────┐
                                                        │ Report Generator │
                                                        └──────────────────┘
                                                                 │
                                                    Win rate, drawdown, returns
```

| Stage | Module | Phase |
|-------|--------|-------|
| Lexer | `compiler/lexer.py` | 1 |
| Parser | `compiler/parser.py` | 1 |
| AST nodes | `compiler/ast_nodes.py` | 1 |
| Driver CLI | `driver.py` | 1 |
| Semantic analyzer | `compiler/semantic.py` | 2 |
| Symbol table | `compiler/symbol_table.py` | 2 |
| IR generator | `compiler/ir.py` | 3 |
| Optimizer | `compiler/optimizer.py` | 3 |
| Interpreter | `compiler/interpreter.py` | 2–3 |
| Report generator | `compiler/reporter.py` | 3 |

---

## Project Structure

```
SwayaLang/
├── GRAMMAR.md              ← Formal EBNF grammar specification
├── README.md               ← This file
├── driver.py               ← CLI entry point
├── COMPILER_PROJ_DEF.pdf   ← Project proposal & design document
│
├── compiler/               ← Compiler pipeline modules
│   ├── __init__.py
│   ├── lexer.py            ← Tokenizer (Phase 1)
│   ├── ast_nodes.py        ← AST dataclasses (Phase 1)
│   ├── parser.py           ← Recursive-descent parser (Phase 1)
│   ├── semantic.py         ← Semantic analyzer (Phase 2)
│   ├── symbol_table.py     ← Scoped symbol table (Phase 2)
│   ├── ir.py               ← IR generator (Phase 3)
│   ├── optimizer.py        ← Constant folding + CSE (Phase 3)
│   ├── interpreter.py      ← Bar-by-bar execution engine (Phase 2–3)
│   └── reporter.py         ← Backtest report generator (Phase 3)
│
├── examples/               ← Sample .strat strategy files
│   ├── golden_cross.strat  ← Canonical Phase 1 test strategy
│   └── rsi_oversold.strat  ← OR-condition + TAKE_PROFIT example
│
└── tests/                  ← pytest test suite
    ├── __init__.py
    ├── test_lexer.py       ← Lexer unit tests (Phase 1)
    ├── test_parser.py      ← Parser unit tests (Phase 1)
    ├── test_ast.py         ← AST pretty-print tests (Phase 1)
    └── test_driver.py      ← End-to-end driver subprocess tests (Phase 1)
```

---

## Quick Start (Phase 1)

### Prerequisites

```bash
python3 --version   # requires Python 3.10+
pip3 install pytest  # for running the test suite
```

### Run the Driver

```bash
# From the project root:
python driver.py examples/golden_cross.strat
```

Expected output (Phase 1 prototype):

```
── Token Stream ────────────────────────────────────────────────────────────
Token(STRATEGY, 'STRATEGY', line=2, col=1)
Token(STRING_LIT, 'GoldenCross', line=2, col=10)
Token(LBRACE, '{', line=2, col=23)
...
Token(EOF, '', line=14, col=1)

── Abstract Syntax Tree ────────────────────────────────────────────────────
Program (strategies=1)
  Strategy(name='GoldenCross')
    indicators:
      IndicatorDecl(name='sma_50')
        FuncCall(name='SMA')
          Ident(CLOSE)
          NumberLit(50)
      ...
    rules:
      RuleBlock(kind='ENTRY')
        action:
          Action(action='BUY', qty=100.0, ticker='AAPL')
        condition:
          BoolOp(op='AND')
            Comparison(op='>')
              Ident(sma_50)
              Ident(sma_200)
            Comparison(op='<')
              Ident(rsi_14)
              NumberLit(30)
```

### Run the Tests

```bash
pytest tests/ -v
```

---

## Language Reference

See **[GRAMMAR.md](./GRAMMAR.md)** for the complete EBNF grammar.

### Supported Indicators

| Indicator | Syntax | Returns |
|-----------|--------|---------|
| Simple Moving Average | `SMA(CLOSE, period)` | Float |
| Exponential Moving Average | `EMA(CLOSE, period)` | Float |
| Relative Strength Index | `RSI(CLOSE, period)` | Float (0–100) |

### Price Fields

`CLOSE`, `OPEN`, `HIGH`, `LOW`, `VOLUME`, `PRICE`, `ENTRY_PRICE`

### Actions

| Action | Syntax | Description |
|--------|--------|-------------|
| Buy N shares | `BUY 100 SHARES OF "AAPL"` | Open long position |
| Sell all | `SELL ALL` | Close all long positions |
| Short N shares | `SHORT 50 SHARES OF "TSLA"` | Open short position |

### Rule Block Types

| Keyword | Purpose |
|---------|---------|
| `ENTRY` | Open a position when condition is true |
| `EXIT` | Close a position when condition is true |
| `STOP_LOSS` | Emergency close on loss threshold |
| `TAKE_PROFIT` | Close on profit target |

---

## Scope (Phase 1)

**In scope:**
- Lexer tokenizing all keywords, identifiers, literals, and operators
- Recursive-descent parser building AST for `STRATEGY`, `INDICATOR`, and rule blocks
- AST pretty-printer for human-readable tree output
- CLI driver: lex → parse → print tokens → print AST
- `pytest` unit tests for lexer and parser

**Out of scope (Phase 2–3):**
- Semantic analysis, symbol table, type checking
- Intermediate representation and optimization
- Interpreter / backtest execution engine
- Live trading or brokerage integration

---

## Development Log

| Date | Phase | Milestone |
|------|-------|-----------|
| 2026-09-16 | 1 | Project scaffold, grammar spec, module skeletons |

---

## License

Academic project — VIT Vellore, Compiler Design Laboratory (BCSE307P), 2026.
