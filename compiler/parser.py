"""
compiler/parser.py — SwayaLang Recursive-Descent Parser
=========================================================
Phase 1 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Consume the token stream produced by ``compiler.lexer.Lexer`` and build
    an Abstract Syntax Tree (AST) using the node types defined in
    ``compiler.ast_nodes``.

    Phase 1 scope (§11 of project spec):
        - Parse a full ``STRATEGY`` block.
        - Parse all ``INDICATOR`` declarations.
        - Parse at minimum one ``ENTRY`` rule with a single binary condition.
        - Build and return a ``ProgramNode``.

    Module boundary (§9 of project spec):
        The parser accepts a pre-built ``List[Token]`` from the caller.
        It does *not* invoke the lexer internally, so it can be unit-tested
        by feeding hand-crafted token lists directly without touching the
        file system or the lexer at all.

Grammar entry points (see GRAMMAR.md for the full EBNF):
    parse()           → ProgramNode
    parse_strategy()  → StrategyNode
    parse_indicator() → IndicatorDeclNode
    parse_rule_block()→ RuleBlockNode
    parse_condition() → ASTNode (ComparisonNode | BoolOpNode)
    parse_action()    → ActionNode
    parse_expr()      → ASTNode (NumberLitNode | IdentNode | BinOpExprNode)

Error handling:
    Raises ParseError(message, token) on unexpected tokens.

Usage:
    from compiler.lexer import Lexer
    from compiler.parser import Parser, ParseError

    tokens = Lexer(source).tokenize()
    tree   = Parser(tokens).parse()
    tree.pretty_print()
"""

from __future__ import annotations

from typing import List

from compiler.ast_nodes import (
    ActionNode,
    BinOpExprNode,
    BoolOpNode,
    ComparisonNode,
    FuncCallNode,
    IdentNode,
    IndicatorDeclNode,
    NumberLitNode,
    ProgramNode,
    RuleBlockNode,
    StrategyNode,
    ASTNode,
)
from compiler.lexer import Token, TokenType


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class ParseError(Exception):
    """Raised by the Parser on unexpected tokens or malformed structure."""

    def __init__(self, message: str, token: Token) -> None:
        super().__init__(
            f"ParseError at line {token.line}, col {token.col} "
            f"(got {token.type.name} {token.value!r}): {message}"
        )
        self.token = token
        self.line  = token.line
        self.col   = token.col


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    """
    Hand-written recursive-descent parser for SwayaLang.

    Each grammar production from ``GRAMMAR.md`` corresponds to one method.
    The parser maintains a *current position* cursor into ``tokens`` and
    never modifies the token list.

    Attributes:
        tokens (List[Token]): Full token stream including trailing EOF.

    Example::

        tokens = Lexer(source).tokenize()
        tree   = Parser(tokens).parse()
        tree.pretty_print()
    """

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens: List[Token] = tokens
        self._pos:   int         = 0   # index of current token

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def parse(self) -> ProgramNode:
        """Parse the complete token stream and return the root ``ProgramNode``.

        Raises:
            ParseError: if the token stream does not conform to the grammar.
        """
        strategies: List[StrategyNode] = []
        while not self._at_end():
            strategies.append(self.parse_strategy())
        if not strategies:
            raise ParseError("expected at least one STRATEGY block", self._current())
        return ProgramNode(strategies=strategies)

    # ------------------------------------------------------------------
    # Grammar productions (one method per production rule)
    # ------------------------------------------------------------------

    def parse_strategy(self) -> StrategyNode:
        """Parse a single ``STRATEGY STRING_LIT '{' strategy_body '}'`` block."""
        self._expect(TokenType.STRATEGY, "expected 'STRATEGY' keyword")
        name_tok = self._expect(TokenType.STRING_LIT, "expected strategy name as string literal")
        self._expect(TokenType.LBRACE, "expected '{' after strategy name")

        indicators: List[IndicatorDeclNode] = []
        while self._check(TokenType.INDICATOR):
            indicators.append(self.parse_indicator())

        rules: List[RuleBlockNode] = []
        while self._check(TokenType.ENTRY, TokenType.EXIT, TokenType.STOP_LOSS, TokenType.TAKE_PROFIT):
            rules.append(self.parse_rule_block())

        if not rules:
            raise ParseError("expected at least one rule block (ENTRY, EXIT, STOP_LOSS, TAKE_PROFIT)", self._current())

        self._expect(TokenType.RBRACE, "expected '}' closing strategy block")
        return StrategyNode(name=name_tok.value, indicators=indicators, rules=rules)

    def parse_indicator(self) -> IndicatorDeclNode:
        """Parse ``INDICATOR IDENT '=' func_call``."""
        self._expect(TokenType.INDICATOR, "expected 'INDICATOR' keyword")
        name_tok = self._expect(TokenType.IDENT, "expected indicator identifier")
        self._expect(TokenType.EQ, "expected '=' after indicator identifier")
        func_call = self.parse_func_call()
        return IndicatorDeclNode(name=name_tok.value, func_call=func_call)

    def parse_func_call(self) -> FuncCallNode:
        """Parse ``IDENT '(' arg_list ')'``."""
        tok = self._current()
        if tok.type in (TokenType.SMA, TokenType.EMA, TokenType.RSI, TokenType.IDENT):
            name = tok.value
            self._advance()
        else:
            raise ParseError("expected function name (e.g. SMA, EMA, RSI or identifier)", tok)

        self._expect(TokenType.LPAREN, "expected '(' after function name")
        args: List[ASTNode] = []
        if not self._check(TokenType.RPAREN):
            args.append(self._parse_func_arg())
            while self._match(TokenType.COMMA):
                args.append(self._parse_func_arg())
        self._expect(TokenType.RPAREN, "expected ')' closing function arguments")
        return FuncCallNode(name=name, args=args)

    def _parse_func_arg(self) -> ASTNode:
        """Parse a single function argument: price_field | NUMBER_LIT | IDENT."""
        tok = self._current()
        if tok.type == TokenType.NUMBER_LIT:
            self._advance()
            return NumberLitNode(value=float(tok.value), raw=tok.value)
        elif tok.type in (
            TokenType.IDENT,
            TokenType.CLOSE,
            TokenType.OPEN,
            TokenType.HIGH,
            TokenType.LOW,
            TokenType.VOLUME,
            TokenType.PRICE,
            TokenType.ENTRY_PRICE,
        ):
            self._advance()
            return IdentNode(name=tok.value)
        else:
            raise ParseError("expected function argument (price field, number, or identifier)", tok)

    def parse_rule_block(self) -> RuleBlockNode:
        """Parse ``rule_keyword ':' action 'IF' condition``."""
        tok = self._current()
        if tok.type in (TokenType.ENTRY, TokenType.EXIT, TokenType.STOP_LOSS, TokenType.TAKE_PROFIT):
            kind = tok.value
            self._advance()
        else:
            raise ParseError("expected rule keyword (ENTRY, EXIT, STOP_LOSS, TAKE_PROFIT)", tok)

        self._expect(TokenType.COLON, "expected ':' after rule keyword")
        action = self.parse_action()
        self._expect(TokenType.IF, "expected 'IF' before rule condition")
        condition = self.parse_condition()
        return RuleBlockNode(kind=kind, action=action, condition=condition)

    def parse_action(self) -> ActionNode:
        """Parse ``(BUY|SELL|SHORT) (NUMBER_LIT SHARES | ALL) [OF STRING_LIT]``."""
        tok = self._current()
        if tok.type in (TokenType.BUY, TokenType.SELL, TokenType.SHORT):
            action_type = tok.value
            self._advance()
        else:
            raise ParseError("expected action keyword (BUY, SELL, SHORT)", tok)

        quantity = None
        all_flag = False

        if self._match(TokenType.ALL):
            all_flag = True
        elif self._check(TokenType.NUMBER_LIT):
            num_tok = self._advance()
            quantity = float(num_tok.value)
            self._expect(TokenType.SHARES, "expected 'SHARES' after quantity")
        else:
            raise ParseError("expected quantity (e.g. 100 SHARES) or 'ALL'", self._current())

        ticker = None
        if self._match(TokenType.OF):
            str_tok = self._expect(TokenType.STRING_LIT, "expected ticker symbol as string literal after 'OF'")
            ticker = str_tok.value

        return ActionNode(action=action_type, quantity=quantity, all_flag=all_flag, ticker=ticker)

    def parse_condition(self) -> ASTNode:
        """Parse top-level boolean condition."""
        return self.parse_or_condition()

    def parse_or_condition(self) -> ASTNode:
        """Parse ``and_condition { OR and_condition }``."""
        left = self.parse_and_condition()
        while self._check(TokenType.OR):
            op_tok = self._advance()
            right = self.parse_and_condition()
            left = BoolOpNode(op=op_tok.value, left=left, right=right)
        return left

    def parse_and_condition(self) -> ASTNode:
        """Parse ``primary_cond { AND primary_cond }``."""
        left = self.parse_primary_cond()
        while self._check(TokenType.AND):
            op_tok = self._advance()
            right = self.parse_primary_cond()
            left = BoolOpNode(op=op_tok.value, left=left, right=right)
        return left

    def parse_primary_cond(self) -> ASTNode:
        """Parse ``'(' condition ')' | comparison``."""
        if self._check(TokenType.LPAREN) and self._is_parenthesized_condition():
            self._advance()  # consume '('
            cond = self.parse_condition()
            self._expect(TokenType.RPAREN, "expected ')' closing condition")
            return cond
        return self.parse_comparison()

    def _is_parenthesized_condition(self) -> bool:
        """Check if current '(' encloses a comparison or boolean operator."""
        depth = 0
        idx = self._pos
        while idx < len(self.tokens):
            tok = self.tokens[idx]
            if tok.type == TokenType.LPAREN:
                depth += 1
            elif tok.type == TokenType.RPAREN:
                depth -= 1
                if depth == 0:
                    return False
            elif depth == 1 and tok.type in (
                TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE, TokenType.EQEQ,
                TokenType.AND, TokenType.OR
            ):
                return True
            idx += 1
        return False

    def parse_comparison(self) -> ComparisonNode:
        """Parse ``expr comparator expr``."""
        left = self.parse_expr()
        tok = self._current()
        if tok.type in (TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE, TokenType.EQEQ):
            op = tok.value
            self._advance()
            right = self.parse_expr()
            return ComparisonNode(op=op, left=left, right=right)
        else:
            raise ParseError("expected comparison operator ('>', '<', '>=', '<=', '==')", tok)

    def parse_expr(self) -> ASTNode:
        """Parse additive expression: ``term { ('+' | '-') term }``."""
        left = self.parse_term()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self.parse_term()
            left = BinOpExprNode(op=op_tok.value, left=left, right=right)
        return left

    def parse_term(self) -> ASTNode:
        """Parse multiplicative term: ``factor { ('*' | '/') factor }``."""
        left = self.parse_factor()
        while self._check(TokenType.STAR, TokenType.SLASH):
            op_tok = self._advance()
            right = self.parse_factor()
            left = BinOpExprNode(op=op_tok.value, left=left, right=right)
        return left

    def parse_factor(self) -> ASTNode:
        """Parse ``'(' expr ')' | NUMBER_LIT | price_field | IDENT``."""
        tok = self._current()
        if self._match(TokenType.LPAREN):
            expr = self.parse_expr()
            self._expect(TokenType.RPAREN, "expected ')' after expression")
            return expr
        elif tok.type == TokenType.NUMBER_LIT:
            self._advance()
            return NumberLitNode(value=float(tok.value), raw=tok.value)
        elif tok.type in (
            TokenType.IDENT,
            TokenType.CLOSE,
            TokenType.OPEN,
            TokenType.HIGH,
            TokenType.LOW,
            TokenType.VOLUME,
            TokenType.PRICE,
            TokenType.ENTRY_PRICE,
        ):
            self._advance()
            return IdentNode(name=tok.value)
        else:
            raise ParseError("expected expression factor (number, identifier, or price field)", tok)

    # ------------------------------------------------------------------
    # Token stream helpers
    # ------------------------------------------------------------------

    def _current(self) -> Token:
        """Return the token at the current position (never goes past EOF)."""
        return self.tokens[min(self._pos, len(self.tokens) - 1)]

    def _peek(self, offset: int = 0) -> Token:
        """Return the token at ``current + offset`` without consuming it."""
        idx = min(self._pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def _advance(self) -> Token:
        """Consume and return the current token, advancing the cursor."""
        tok = self._current()
        if tok.type is not TokenType.EOF:
            self._pos += 1
        return tok

    def _check(self, *types: TokenType) -> bool:
        """Return True if the current token type is one of *types*."""
        return self._current().type in types

    def _match(self, *types: TokenType) -> bool:
        """Consume the current token if its type is in *types*.

        Returns:
            True if consumed, False otherwise.
        """
        if self._check(*types):
            self._advance()
            return True
        return False

    def _expect(self, ttype: TokenType, error_msg: str = "") -> Token:
        """Consume the current token and assert its type equals *ttype*.

        Args:
            ttype:     The expected TokenType.
            error_msg: Contextual message appended to the ParseError.

        Returns:
            The consumed token.

        Raises:
            ParseError: if the current token type does not match *ttype*.
        """
        tok = self._current()
        if tok.type is not ttype:
            msg = error_msg or f"expected {ttype.name}"
            raise ParseError(msg, tok)
        return self._advance()

    def _at_end(self) -> bool:
        """Return True if the current token is EOF."""
        return self._current().type is TokenType.EOF
