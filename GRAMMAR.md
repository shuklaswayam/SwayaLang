# SwayaLang — Formal Grammar Specification (EBNF)

**SwayaLang** is a statically-checked domain-specific language for expressing
rule-based stock-trading strategies. This document is the authoritative grammar
reference for all three compiler phases.

---

## 1. Notation

The grammar is written in Extended Backus–Naur Form (EBNF) with the following
conventions:

| Symbol | Meaning |
|--------|---------|
| `::=` | Defines a production rule |
| `'...'` | Terminal (literal keyword or punctuation) |
| `( ... )` | Grouping |
| `[ ... ]` | Optional — zero or one occurrence |
| `{ ... }` | Repetition — zero or more occurrences |
| `A \| B` | Alternation — A or B |
| `UPPER_CASE` | Lexical token produced by the lexer |

---

## 2. Top-Level Structure

```ebnf
program        ::= { strategy_def } EOF

strategy_def   ::= 'STRATEGY' STRING_LIT '{' strategy_body '}'

strategy_body  ::= { indicator_decl } rule_block { rule_block }
```

A **program** is a sequence of one or more `STRATEGY` blocks.  
Each strategy contains zero or more `INDICATOR` declarations followed by one or
more rule blocks (`ENTRY`, `EXIT`, `STOP_LOSS`, `TAKE_PROFIT`).

---

## 3. Indicator Declarations

```ebnf
indicator_decl ::= 'INDICATOR' IDENT '=' func_call

func_call      ::= IDENT '(' arg_list ')'

arg_list       ::= arg { ',' arg }

arg            ::= price_field
                 | NUMBER_LIT
                 | IDENT
```

Supported built-in indicator functions (validated during semantic analysis):

| Function | Signature | Description |
|----------|-----------|-------------|
| `SMA` | `SMA(price_field, period)` | Simple Moving Average |
| `EMA` | `EMA(price_field, period)` | Exponential Moving Average |
| `RSI` | `RSI(price_field, period)` | Relative Strength Index (0–100) |

---

## 4. Price Fields

```ebnf
price_field    ::= 'CLOSE'
                 | 'OPEN'
                 | 'HIGH'
                 | 'LOW'
                 | 'VOLUME'
                 | 'PRICE'
                 | 'ENTRY_PRICE'
```

`PRICE` refers to the current bar's closing price at runtime.  
`ENTRY_PRICE` is a runtime-bound variable set when a position is entered.

---

## 5. Rule Blocks

```ebnf
rule_block     ::= rule_keyword ':' action 'IF' condition

rule_keyword   ::= 'ENTRY'
                 | 'EXIT'
                 | 'STOP_LOSS'
                 | 'TAKE_PROFIT'
```

Each rule block declares a trigger condition and the action to perform when
that condition evaluates to `true` on a given price bar.

---

## 6. Actions

```ebnf
action         ::= buy_action
                 | sell_action
                 | short_action

buy_action     ::= 'BUY' ( order_qty | 'ALL' ) [ 'OF' STRING_LIT ]

sell_action    ::= 'SELL' ( order_qty | 'ALL' ) [ 'OF' STRING_LIT ]

short_action   ::= 'SHORT' order_qty [ 'OF' STRING_LIT ]

order_qty      ::= NUMBER_LIT 'SHARES'
```

Examples:

```
BUY 100 SHARES OF "AAPL"
SELL ALL
SHORT 50 SHARES OF "TSLA"
```

---

## 7. Conditions

```ebnf
condition      ::= or_condition

or_condition   ::= and_condition { 'OR' and_condition }

and_condition  ::= primary_cond { 'AND' primary_cond }

primary_cond   ::= '(' condition ')'
                 | comparison

comparison     ::= expr comparator expr

comparator     ::= '>'
                 | '<'
                 | '>='
                 | '<='
                 | '=='
```

Conditions use standard left-associative boolean logic with `AND` binding
tighter than `OR` (matching conventional precedence).

---

## 8. Expressions

```ebnf
expr           ::= term { ( '+' | '-' ) term }

term           ::= factor { ( '*' | '/' ) factor }

factor         ::= '(' expr ')'
                 | NUMBER_LIT
                 | price_field
                 | IDENT
```

Operator precedence (highest to lowest): `*`, `/` → `+`, `-`.  
Parentheses override precedence.

---

## 9. Lexical Tokens

### 9.1 Keywords (reserved — cannot be used as identifiers)

```
STRATEGY  INDICATOR  ENTRY  EXIT  STOP_LOSS  TAKE_PROFIT
BUY  SELL  SHORT  ALL  SHARES  OF  IF  AND  OR
CLOSE  OPEN  HIGH  LOW  VOLUME  PRICE  ENTRY_PRICE
SMA  EMA  RSI
```

### 9.2 Literals

```ebnf
STRING_LIT     ::= '"' { any_char_except_dquote } '"'

NUMBER_LIT     ::= DIGIT { DIGIT } [ '.' { DIGIT } ]

IDENT          ::= LETTER ( LETTER | DIGIT | '_' )* 
```

Where `LETTER = [A-Za-z]`, `DIGIT = [0-9]`.

### 9.3 Operators and Delimiters

```
{  }  (  )  ,  :  =
>  <  >=  <=  ==
+  -  *  /
```

### 9.4 Comments

```ebnf
comment        ::= '#' { any_char_except_newline } NEWLINE
```

Comments begin with `#` and extend to end of line. They are discarded by the
lexer and do not appear in the token stream.

### 9.5 Whitespace

Whitespace (spaces, tabs, carriage returns, newlines) is ignored between tokens
except that newlines terminate line comments.

---

## 10. Error Recovery Conventions

| Error class | Example | Lexer action |
|-------------|---------|--------------|
| `LexError` | Unknown character `@` | Raise with line + column |
| `LexError` | Unterminated string `"foo` | Raise at EOF with opening position |
| `ParseError` | Missing `IF` in rule block | Raise with offending token position |
| `SemanticError` | Undeclared indicator used in condition | Raise after parse, during analysis |

---

## 11. Full Sample Program

```
# GoldenCross strategy — buy on SMA crossover with RSI filter
STRATEGY "GoldenCross" {
    INDICATOR sma_50  = SMA(CLOSE, 50)
    INDICATOR sma_200 = SMA(CLOSE, 200)
    INDICATOR rsi_14  = RSI(CLOSE, 14)

    ENTRY:     BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200 AND rsi_14 < 30
    EXIT:      SELL ALL                  IF sma_50 < sma_200
    STOP_LOSS: SELL ALL                  IF PRICE < ENTRY_PRICE * 0.95
}
```

---

## 12. Precedence and Associativity Summary

| Level | Operators | Associativity |
|-------|-----------|---------------|
| 1 (highest) | `*`, `/` | Left |
| 2 | `+`, `-` | Left |
| 3 | `>`, `<`, `>=`, `<=`, `==` | None (no chaining) |
| 4 | `AND` | Left |
| 5 (lowest) | `OR` | Left |

---

## 13. Grammar Completeness Notes (Phase 1 → Phase 3)

| Feature | Phase 1 | Phase 2 | Phase 3 |
|---------|---------|---------|---------|
| EBNF grammar document | ✅ This file | — | Finalized |
| Lexer token stream | ✅ Prototype | Complete | Complete |
| Parser (partial AST) | ✅ ENTRY only | Full AST | Full AST |
| Symbol table | ❌ | ✅ | Complete |
| Semantic analysis | ❌ | ✅ | Complete |
| IR / three-address code | ❌ | ❌ | ✅ |
| Optimizer | ❌ | ❌ | ✅ |
| Interpreter / backtest | ❌ | ✅ Prototype | Complete |

---

*Prepared for: Compiler Design Laboratory (BCSE307P) — Review 1: Project Proposal and Design Review*  
*Author: Swayam Shukla (24BCE0751)*
