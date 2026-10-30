"""compiler package for SwayaLang — Full 3-Phase Compiler Pipeline."""

from compiler.ast_nodes import (
    ActionNode,
    ASTNode,
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
)
from compiler.interpreter import BacktestReport, IndicatorEngine, Interpreter, MarketData, Position, Trade
from compiler.ir import IRGenerator, IRProgram, IRStrategy, Quad
from compiler.lexer import LexError, Lexer, Token, TokenType
from compiler.optimizer import ASTConstantFolder, OptimizationStats, Optimizer, TACOptimizer
from compiler.parser import ParseError, Parser
from compiler.reporter import (
    BenchmarkRunner,
    CompilerBenchmark,
    ComprehensiveReport,
    FinancialMetrics,
    ReportGenerator,
    StageTiming,
)
from compiler.semantic import SemanticAnalyzer, SemanticError
from compiler.symbol_table import Scope, Symbol, SymbolKind, SymbolTable

__all__ = [
    # Lexer & Parser
    "Token",
    "TokenType",
    "Lexer",
    "LexError",
    "Parser",
    "ParseError",
    # AST
    "ASTNode",
    "ProgramNode",
    "StrategyNode",
    "IndicatorDeclNode",
    "RuleBlockNode",
    "ActionNode",
    "FuncCallNode",
    "ComparisonNode",
    "BoolOpNode",
    "BinOpExprNode",
    "IdentNode",
    "NumberLitNode",
    # Symbol Table & Semantics
    "SymbolTable",
    "Scope",
    "Symbol",
    "SymbolKind",
    "SemanticAnalyzer",
    "SemanticError",
    # IR
    "Quad",
    "IRStrategy",
    "IRProgram",
    "IRGenerator",
    # Optimizer (Phase 3)
    "Optimizer",
    "ASTConstantFolder",
    "TACOptimizer",
    "OptimizationStats",
    # Interpreter & Runtime
    "Interpreter",
    "MarketData",
    "IndicatorEngine",
    "BacktestReport",
    "Trade",
    "Position",
    # Reporting & Benchmarking (Phase 3)
    "ReportGenerator",
    "ComprehensiveReport",
    "FinancialMetrics",
    "CompilerBenchmark",
    "BenchmarkRunner",
    "StageTiming",
]
