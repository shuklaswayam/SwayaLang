"""
benchmark.py — SwayaLang Systematic Performance & Scaling Benchmark Suite
===========================================================================
Phase 3 deliverable for BCSE307P Compiler Design Laboratory.

Conducts empirical benchmarking of the SwayaLang compiler and runtime:
  1. Pipeline Stage Latency Breakdown (Lexer, Parser, Semantic, IR, Optimizer, Engine)
  2. Dataset Scaling Evaluation (100, 500, 1000, 5000, 10000 historical bars)
  3. Memory Footprint Profiling (Peak heap memory in KB across scales)
  4. Optimization Efficiency Impact (Instruction count reduction % & runtime speedup)
  5. High-Resolution Visual Plotting (benchmark_scaling_chart.png)
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from compiler.interpreter import Interpreter, MarketData
from compiler.ir import IRGenerator
from compiler.lexer import Lexer
from compiler.optimizer import Optimizer
from compiler.parser import Parser
from compiler.reporter import BenchmarkRunner, ReportGenerator
from compiler.semantic import SemanticAnalyzer


def run_scaling_benchmark() -> None:
    print("=" * 78)
    print(" SWAYALANG PHASE 3 COMPILER PERFORMANCE & SCALING BENCHMARK")
    print("=" * 78)

    sample_strat = """
    STRATEGY "BenchmarkStrategy" {
        INDICATOR sma_20  = SMA(CLOSE, 20)
        INDICATOR sma_50  = SMA(CLOSE, 50)
        INDICATOR rsi_14  = RSI(CLOSE, 14)

        ENTRY:     BUY 100 SHARES OF "AAPL" IF sma_20 > sma_50 AND rsi_14 < (15 + 15)
        EXIT:      SELL ALL                  IF sma_20 < sma_50
        STOP_LOSS: SELL ALL                  IF PRICE < ENTRY_PRICE * (1.0 - 0.05)
    }
    """

    scales = [100, 500, 1000, 5000, 10000]
    total_times_ms: List[float] = []
    engine_times_ms: List[float] = []
    compile_times_ms: List[float] = []
    memory_peaks_kb: List[float] = []
    throughputs: List[float] = []

    print(f"\n{'Bars':<8} | {'Compile (ms)':<14} | {'Engine (ms)':<14} | {'Total (ms)':<12} | {'Throughput (b/s)':<18} | {'Peak RAM (KB)':<12}")
    print("-" * 88)

    for n_bars in scales:
        data = MarketData.generate_synthetic(ticker="AAPL", n_bars=n_bars)
        report, opt_stats = BenchmarkRunner.measure_pipeline(
            source=sample_strat,
            market_data=data,
            capital=100000.0,
            enable_optimization=True,
        )

        b = report.benchmark
        compile_time = sum(t.duration_ms for t in b.timings if "Stage 6" not in t.stage_name)
        engine_time = next((t.duration_ms for t in b.timings if "Stage 6" in t.stage_name), 0.0)

        compile_times_ms.append(compile_time)
        engine_times_ms.append(engine_time)
        total_times_ms.append(b.total_time_ms)
        memory_peaks_kb.append(b.peak_memory_kb)
        throughputs.append(b.bars_per_second)

        print(f"{n_bars:<8} | {compile_time:<14.3f} | {engine_time:<14.3f} | {b.total_time_ms:<12.3f} | {b.bars_per_second:<18.1f} | {b.peak_memory_kb:<12.2f}")

    print("-" * 88)

    # ------------------------------------------------------------------
    # Optimization Efficiency Audit
    # ------------------------------------------------------------------
    print("\nOPTIMIZATION EFFICIENCY AUDIT:")
    print(f"  Initial TAC Quadruples:   {opt_stats.initial_quad_count}")
    print(f"  Optimized TAC Quadruples: {opt_stats.optimized_quad_count}")
    print(f"  Instructions Eliminated:  {opt_stats.instructions_eliminated}")
    print(f"  Instruction Reduction:    {opt_stats.reduction_pct:.2f}%")
    print(f"  Constant Folds:           {opt_stats.constant_folds}")
    print(f"  CSE Replacements:         {opt_stats.cse_eliminations}")

    # ------------------------------------------------------------------
    # Plot Benchmark Scaling Charts
    # ------------------------------------------------------------------
    output_dir = Path("presentation_assets")
    output_dir.mkdir(exist_ok=True)
    chart_path = output_dir / "benchmark_scaling_chart.png"

    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=200)
    fig.patch.set_facecolor("#0d1117")

    # Subplot 1: Latency Scaling (ms)
    ax1.set_facecolor("#161b22")
    ax1.plot(scales, total_times_ms, marker="o", color="#58a6ff", linewidth=2.0, label="Total Pipeline Latency (ms)")
    ax1.plot(scales, engine_times_ms, marker="s", color="#3fb950", linewidth=1.8, label="Execution Engine (ms)")
    ax1.plot(scales, compile_times_ms, marker="^", color="#d29922", linewidth=1.8, label="Compile Stages 1-5 (ms)")
    ax1.set_title("Compiler & Runtime Latency vs Dataset Size", fontsize=11, fontweight="bold", color="#f0f6fc")
    ax1.set_xlabel("Number of Historical Bars", fontsize=9, color="#c9d1d9")
    ax1.set_ylabel("Execution Time (milliseconds)", fontsize=9, color="#c9d1d9")
    ax1.grid(True, linestyle=":", alpha=0.3, color="#30363d")
    ax1.legend(facecolor="#21262d", edgecolor="#30363d", fontsize=8)

    # Subplot 2: Throughput (bars/sec) & Peak Memory (KB)
    ax2.set_facecolor("#161b22")
    color_tp = "#a371f7"
    ax2.plot(scales, throughputs, marker="D", color=color_tp, linewidth=2.0, label="Throughput (bars/sec)")
    ax2.set_xlabel("Number of Historical Bars", fontsize=9, color="#c9d1d9")
    ax2.set_ylabel("Throughput (bars / second)", fontsize=9, color=color_tp)
    ax2.tick_params(axis="y", labelcolor=color_tp)
    ax2.grid(True, linestyle=":", alpha=0.3, color="#30363d")

    # Secondary axis for memory
    ax2_mem = ax2.twinx()
    color_mem = "#f85149"
    ax2_mem.plot(scales, memory_peaks_kb, marker="x", color=color_mem, linestyle="--", linewidth=1.8, label="Peak Heap RAM (KB)")
    ax2_mem.set_ylabel("Peak Memory (KB)", fontsize=9, color=color_mem)
    ax2_mem.tick_params(axis="y", labelcolor=color_mem)

    ax2.set_title("Processing Throughput & Memory Footprint", fontsize=11, fontweight="bold", color="#f0f6fc")

    plt.tight_layout()
    fig.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"\n[OUTPUT] Scaling benchmark chart exported to: {chart_path}")
    print("=" * 78)


if __name__ == "__main__":
    run_scaling_benchmark()
