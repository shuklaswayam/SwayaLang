/* ═══════════════════════════════════════════════════════════════════════════
   SwayaLang IDE — app.js
   Monaco editor + pipeline API integration + all panel renderers
   ═══════════════════════════════════════════════════════════════════════════ */

"use strict";

// ─── State ───────────────────────────────────────────────────────────────────
let monacoEditor = null;
let equityChart = null;
let lastTrades = [];
let activeStages = new Set(["tokens", "ast", "symbols", "ir", "optimize", "run"]);

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const btnRun = document.getElementById("btn-run");
const btnFormat = document.getElementById("btn-format");
const dataSelect = document.getElementById("data-select");
const capitalInput = document.getElementById("capital-input");
const errorBar = document.getElementById("error-bar");
const errorText = document.getElementById("error-text");
const statusLeft = document.getElementById("status-left");
const examplesList = document.getElementById("examples-list");
const tabsHeader = document.getElementById("tabs-header");

// ─── Default starter code ────────────────────────────────────────────────────
const STARTER = `# MomentumAlpha — Phase 3 Compiler Optimization Showcase Strategy
# Compiler Optimization Passes Triggered:
#   1. Constant Folding: evaluates (25 * 2) -> 50, (1.0 - 0.04) -> 0.96, (1.0 + 0.08) -> 1.08
#   2. Common Subexpression Elimination (CSE): reuses identical sub-condition across rules
#   3. Dead Code Elimination: removes dead intermediate temporary registers in TAC
#   4. Instruction Reduction: eliminates redundant instructions with full semantic equivalence

STRATEGY "MomentumAlpha" {
    INDICATOR sma_20 = SMA(CLOSE, 20)
    INDICATOR rsi_14 = RSI(CLOSE, 14)

    ENTRY:       BUY 100 SHARES OF "AAPL" IF (CLOSE > sma_20) AND (rsi_14 > (25 * 2))
    EXIT:        SELL ALL                  IF (CLOSE < sma_20) AND (rsi_14 > (25 * 2))
    STOP_LOSS:   SELL ALL                  IF PRICE < ENTRY_PRICE * (1.0 - 0.04)
    TAKE_PROFIT: SELL ALL                  IF PRICE > ENTRY_PRICE * (1.0 + 0.08)
}
`;

// ═══════════════════════════════════════════════════════════════════════════════
//  Monaco Editor Setup
// ═══════════════════════════════════════════════════════════════════════════════

require.config({ paths: { vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs" } });

require(["vs/editor/editor.main"], () => {
  // --- Define SwayaLang language ---
  monaco.languages.register({ id: "swayalang" });

  monaco.languages.setMonarchTokensProvider("swayalang", {
    keywords: [
      "STRATEGY", "INDICATOR", "ENTRY", "EXIT", "STOP_LOSS", "TAKE_PROFIT",
      "BUY", "SELL", "SHARES", "OF", "ALL", "IF", "AND", "OR", "NOT",
      "PRICE", "ENTRY_PRICE", "CLOSE", "OPEN", "HIGH", "LOW", "VOLUME",
      "SMA", "EMA", "RSI", "MACD", "BB",
    ],
    operators: [">", "<", ">=", "<=", "==", "!=", "+", "-", "*", "/"],
    tokenizer: {
      root: [
        [/#.*$/, "comment"],
        [/"[^"]*"/, "string"],
        [/\b\d+(\.\d+)?\b/, "number"],
        [/[A-Z_][A-Z0-9_]*/, {
          cases: {
            "@keywords": "keyword",
            "@default": "identifier",
          },
        }],
        [/[a-z_]\w*/, "variable"],
        [/[{}()\[\]:,]/, "delimiter"],
        [/[><=!+\-*/]+/, "operator"],
      ],
    },
  });

  // --- Theme (Wise: light canvas, Forest Ink + Lime Voltage) ---
  monaco.editor.defineTheme("swayalang-wise", {
    base: "vs",
    inherit: true,
    rules: [
      { token: "keyword",    foreground: "163300", fontStyle: "bold" },
      { token: "string",     foreground: "054d28" },
      { token: "number",     foreground: "0b4c72" },
      { token: "comment",    foreground: "868685", fontStyle: "italic" },
      { token: "identifier", foreground: "6a6c6a" },
      { token: "variable",   foreground: "454745" },
      { token: "operator",   foreground: "454745" },
      { token: "delimiter",  foreground: "868685" },
    ],
    colors: {
      "editor.background":                "#ffffff",
      "editor.foreground":                "#454745",
      "editor.lineHighlightBackground":   "#e2f6d5",
      "editorLineNumber.foreground":      "#868685",
      "editorLineNumber.activeForeground":"#163300",
      "editor.selectionBackground":       "#9fe87040",
      "editorCursor.foreground":          "#163300",
      "editor.inactiveSelectionBackground":"#9fe87020",
      "editorIndentGuide.background":     "#e8ebe6",
      "editorIndentGuide.activeBackground":"#868685",
    },
  });

  // --- Auto-completion ---
  monaco.languages.registerCompletionItemProvider("swayalang", {
    provideCompletionItems(model, position) {
      const suggestions = [
        "STRATEGY", "INDICATOR", "ENTRY", "EXIT", "STOP_LOSS", "TAKE_PROFIT",
        "BUY", "SELL", "SHARES", "OF", "ALL", "IF", "AND", "OR",
        "PRICE", "ENTRY_PRICE", "CLOSE", "OPEN", "HIGH", "LOW",
        "SMA", "EMA", "RSI",
      ].map(kw => ({
        label: kw,
        kind: monaco.languages.CompletionItemKind.Keyword,
        insertText: kw,
        range: {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: model.getWordUntilPosition(position).startColumn,
          endColumn: position.column,
        },
      }));
      return { suggestions };
    },
  });

  // --- Create editor ---
  monacoEditor = monaco.editor.create(
    document.getElementById("editor-container"),
    {
      value: STARTER,
      language: "swayalang",
      theme: "swayalang-wise",
      fontSize: 13,
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      fontLigatures: true,
      lineHeight: 20,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      wordWrap: "on",
      padding: { top: 12, bottom: 12 },
      renderLineHighlight: "all",
      smoothScrolling: true,
      cursorBlinking: "smooth",
      cursorSmoothCaretAnimation: "on",
      suggest: { showKeywords: true },
      tabSize: 4,
      automaticLayout: true,
    }
  );

  // Keyboard shortcut: Ctrl/Cmd+Enter → Run
  monacoEditor.addCommand(
    monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
    () => runPipeline()
  );

  setStatus("Ready · Press ▶ Run or Ctrl+Enter to compile");
  loadExamples();
});

// ═══════════════════════════════════════════════════════════════════════════════
//  Tab System
// ═══════════════════════════════════════════════════════════════════════════════

tabsHeader.addEventListener("click", (e) => {
  const tab = e.target.closest(".tab");
  if (!tab) return;
  const name = tab.dataset.tab;
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t === tab));
  document.querySelectorAll(".tab-panel").forEach(p =>
    p.classList.toggle("active", p.id === `tab-${name}`)
  );
});

// ─── Stage toggle chips ───────────────────────────────────────────────────────
document.querySelectorAll(".toggle-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const stage = chip.dataset.stage;
    if (activeStages.has(stage)) {
      activeStages.delete(stage);
      chip.classList.remove("active");
    } else {
      activeStages.add(stage);
      chip.classList.add("active");
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
//  Pipeline Runner
// ═══════════════════════════════════════════════════════════════════════════════

btnRun.addEventListener("click", runPipeline);
btnFormat.addEventListener("click", () => {
  if (monacoEditor) {
    monacoEditor.getAction("editor.action.formatDocument")?.run();
  }
});

async function runPipeline() {
  if (!monacoEditor) return;
  const source = monacoEditor.getValue();
  const stages = [...activeStages];
  const capital = parseFloat(capitalInput.value) || 100000;
  const data = dataSelect.value === "SYNTH" ? "AAPL" : dataSelect.value;

  clearAllPanels();
  setRunning(true);
  clearError();
  setStatus("⚙ Compiling…");

  try {
    const res = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, stages, capital, data }),
    });

    if (!res.ok) {
      showError(`HTTP ${res.status}: ${res.statusText}`, "network");
      setStatus("✖ Network error");
      return;
    }

    const data_resp = await res.json();

    if (!data_resp.ok && data_resp.error) {
      const err = data_resp.error;
      const loc = err.line ? ` (line ${err.line}${err.col ? `:${err.col}` : ""})` : "";
      showError(`[${err.stage.toUpperCase()}] ${err.message}${loc}`, err.stage, err.line);
      setStatus(`✖ ${err.stage} error`);
    } else {
      clearError();
      setStatus(`✓ Pipeline complete · ${stages.join(", ")}`);
    }

    // Show warnings
    showWarnings(data_resp.warnings || []);

    // Render each stage — each renderer isolated so one failure can't block others
    if (data_resp.tokens !== null) { try { renderTokens(data_resp.tokens); } catch (e) { console.error("renderTokens:", e); } }
    if (data_resp.ast !== null) { try { renderAST(data_resp.ast); } catch (e) { console.error("renderAST:", e); } }
    if (data_resp.symbols !== null) { try { renderSymbols(data_resp.symbols); } catch (e) { console.error("renderSymbols:", e); } }
    if (data_resp.ir !== null) { try { renderIR(data_resp.ir); } catch (e) { console.error("renderIR:", e); } }
    if (data_resp.optimized_ir !== null || data_resp.optimization !== null) {
      try { renderOptimizer(data_resp); } catch (e) { console.error("renderOptimizer:", e); }
    }
    if (data_resp.report !== null) { try { renderReport(data_resp.report, data_resp.financial); } catch (e) { console.error("renderReport:", e); } }
    if (data_resp.benchmark !== null) { try { renderBenchmark(data_resp.benchmark); } catch (e) { console.error("renderBenchmark:", e); } }

    // Auto-switch to first populated tab
    autoSwitchTab(data_resp, stages);

  } catch (ex) {
    showError(`Fetch failed: ${ex.message}`, "network");
    setStatus("✖ Request failed");
  } finally {
    setRunning(false);
  }
}

// ─── auto-switch to the first non-empty tab ───────────────────────────────────
function autoSwitchTab(resp, stages) {
  const order = ["tokens", "ast", "symbols", "ir", "optimizer", "report", "benchmark"];
  const stageToTab = { tokens: "tokens", ast: "ast", symbols: "symbols", ir: "ir", optimize: "optimizer", run: "report" };
  for (const s of stages) {
    const tabKey = stageToTab[s];
    if (!tabKey) continue;
    const hasData = (s === "run" ? resp.report : resp[s]) !== null;
    if (hasData) {
      activateTab(tabKey);
      return;
    }
  }
}

function activateTab(name) {
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === `tab-${name}`));
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TOKEN RENDERER
// ═══════════════════════════════════════════════════════════════════════════════

function renderTokens(tokens) {
  const wrap = document.getElementById("tokens-wrap");
  const tbody = document.getElementById("token-tbody");
  const empty = document.getElementById("tokens-empty");

  tbody.innerHTML = "";
  tokens.forEach((tok, i) => {
    const cls = `tok-${tok.type.replace(/[^A-Z0-9]/g, "")}`;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color:var(--text-muted)">${i + 1}</td>
      <td><span class="tok-type ${cls}">${esc(tok.type)}</span></td>
      <td style="color:var(--text-primary);font-weight:500">${esc(String(tok.value))}</td>
      <td>${tok.line ?? "—"}</td>
      <td>${tok.col ?? "—"}</td>
    `;
    tbody.appendChild(tr);
  });

  empty.classList.add("hidden");
  wrap.classList.remove("hidden");
}

// ═══════════════════════════════════════════════════════════════════════════════
//  AST RENDERER
// ═══════════════════════════════════════════════════════════════════════════════

function renderAST(ast) {
  const wrap = document.getElementById("ast-wrap");
  const root = document.getElementById("ast-tree");
  const empty = document.getElementById("ast-empty");

  root.innerHTML = "";
  root.appendChild(buildTreeNode(ast));

  empty.classList.add("hidden");
  wrap.classList.remove("hidden");

  // Search filter
  document.getElementById("ast-search").addEventListener("input", function () {
    filterTree(root, this.value.trim().toLowerCase());
  });
}

function buildTreeNode(obj, key) {
  if (obj === null || obj === undefined) {
    return makeLeaf(key, "null", "var(--text-muted)");
  }
  if (typeof obj !== "object") {
    return makeLeaf(key, obj);
  }

  const div = document.createElement("div");
  div.className = "tree-node";

  const header = document.createElement("div");
  header.className = "tree-node-header";

  const toggle = document.createElement("span");
  toggle.className = "tree-toggle";
  toggle.textContent = "▶";

  const typeSpan = document.createElement("span");
  typeSpan.className = "tree-node-type";
  typeSpan.textContent = obj._node || (key || "Object");

  header.appendChild(toggle);
  header.appendChild(typeSpan);

  // Show key name value inline if small
  if (key && key !== "_node") {
    const keySpan = document.createElement("span");
    keySpan.className = "tree-node-val";
    keySpan.style.fontSize = "10px";
    keySpan.style.color = "var(--text-muted)";
    keySpan.textContent = ` · ${key}`;
    header.appendChild(keySpan);
  }

  if (obj.name || obj.value !== undefined) {
    const valSpan = document.createElement("span");
    valSpan.className = "tree-node-val";
    valSpan.textContent = `  ${JSON.stringify(obj.name ?? obj.value)}`;
    header.appendChild(valSpan);
  }

  const children = document.createElement("div");
  children.className = "tree-children";

  for (const [k, v] of Object.entries(obj)) {
    if (k === "_node") continue;
    if (typeof v === "object" && v !== null) {
      if (Array.isArray(v)) {
        const arrNode = document.createElement("div");
        arrNode.className = "tree-node";
        const arrHeader = document.createElement("div");
        arrHeader.className = "tree-node-header";
        const arrToggle = document.createElement("span");
        arrToggle.className = "tree-toggle";
        arrToggle.textContent = "▶";
        const arrLabel = document.createElement("span");
        arrLabel.className = "tree-leaf-key";
        arrLabel.textContent = `${k} [${v.length}]`;
        arrHeader.appendChild(arrToggle);
        arrHeader.appendChild(arrLabel);
        const arrChildren = document.createElement("div");
        arrChildren.className = "tree-children";
        v.forEach((item, idx) => {
          if (typeof item === "object" && item !== null) {
            arrChildren.appendChild(buildTreeNode(item, `[${idx}]`));
          } else {
            arrChildren.appendChild(makeLeaf(`[${idx}]`, item));
          }
        });
        bindToggle(arrHeader, arrToggle, arrChildren);
        arrNode.appendChild(arrHeader);
        arrNode.appendChild(arrChildren);
        children.appendChild(arrNode);
      } else {
        children.appendChild(buildTreeNode(v, k));
      }
    } else {
      children.appendChild(makeLeaf(k, v));
    }
  }

  bindToggle(header, toggle, children);
  div.appendChild(header);
  div.appendChild(children);
  return div;
}

function bindToggle(header, toggle, children) {
  header.addEventListener("click", () => {
    const isOpen = children.classList.contains("open");
    children.classList.toggle("open", !isOpen);
    toggle.classList.toggle("open", !isOpen);
  });
}

function makeLeaf(key, value) {
  const div = document.createElement("div");
  div.className = "tree-node tree-leaf";
  div.style.paddingLeft = "20px";
  const kSpan = document.createElement("span");
  kSpan.className = "tree-leaf-key";
  kSpan.textContent = key !== undefined ? `${key}: ` : "";
  const vSpan = document.createElement("span");
  if (typeof value === "number") { vSpan.className = "tree-leaf-num"; }
  else if (typeof value === "boolean") { vSpan.className = "tree-leaf-bool"; }
  else if (typeof value === "string") { vSpan.className = "tree-leaf-str"; }
  else { vSpan.className = "tree-leaf"; }
  vSpan.textContent = JSON.stringify(value);
  div.appendChild(kSpan);
  div.appendChild(vSpan);
  return div;
}

function filterTree(root, query) {
  if (!query) {
    root.querySelectorAll(".tree-node").forEach(n => n.style.display = "");
    return;
  }
  root.querySelectorAll(".tree-node").forEach(node => {
    const text = node.textContent.toLowerCase();
    node.style.display = text.includes(query) ? "" : "none";
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SYMBOL TABLE RENDERER
// ═══════════════════════════════════════════════════════════════════════════════

function renderSymbols(symdata) {
  const wrap = document.getElementById("symbols-wrap");
  const scopes = document.getElementById("symbols-scopes");
  const empty = document.getElementById("symbols-empty");

  scopes.innerHTML = "";

  (symdata.scopes || []).forEach(scope => {
    const block = document.createElement("div");
    block.className = "scope-block";
    block.innerHTML = `
      <div class="scope-header">
        <span class="scope-dot"></span>
        Scope: ${esc(scope.scope_name)}
        <span style="color:var(--text-muted);font-size:10px;margin-left:auto">${scope.symbols.length} symbol${scope.symbols.length !== 1 ? "s" : ""}</span>
      </div>
    `;

    if (scope.symbols.length === 0) {
      const empty_row = document.createElement("div");
      empty_row.style.cssText = "padding:10px 14px;color:var(--text-muted);font-size:12px;";
      empty_row.textContent = "(empty scope)";
      block.appendChild(empty_row);
    } else {
      const table = document.createElement("table");
      table.className = "sym-table";
      table.innerHTML = `
        <thead><tr><th>Name</th><th>Kind</th><th>Type</th><th>Value</th></tr></thead>
        <tbody>
          ${scope.symbols.map(s => `
            <tr>
              <td style="color:var(--text-primary);font-weight:500">${esc(s.name)}</td>
              <td><span class="sym-kind">${esc(s.kind)}</span></td>
              <td><span class="sym-type">${esc(s.type)}</span></td>
              <td style="color:var(--text-muted)">${esc(s.value)}</td>
            </tr>
          `).join("")}
        </tbody>
      `;
      block.appendChild(table);
    }

    scopes.appendChild(block);
  });

  empty.classList.add("hidden");
  wrap.classList.remove("hidden");
}

// ═══════════════════════════════════════════════════════════════════════════════
//  IR RENDERER
// ═══════════════════════════════════════════════════════════════════════════════

function renderIR(irText) {
  const pre = document.getElementById("ir-code");
  const empty = document.getElementById("ir-empty");

  // Syntax-highlight TAC
  const highlighted = irText
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/(;[^\n]*)/g, '<span style="color:#868685">$1</span>')
    .replace(/\b(LABEL|GOTO|IF|PARAM|CALL|RETURN|NOP)\b/g, '<span style="color:#163300;font-weight:700">$1</span>')
    .replace(/\b(BUY|SELL|STOP_LOSS|TAKE_PROFIT|ENTRY|EXIT)\b/g, '<span style="color:#054d28;font-weight:700">$1</span>')
    .replace(/\b(\d+(\.\d+)?)\b/g, '<span style="color:#0b4c72">$1</span>')
    .replace(/(t\d+)/g, '<span style="color:#6a6c6a">$1</span>');

  pre.innerHTML = highlighted;
  empty.classList.add("hidden");
  pre.classList.remove("hidden");
}

// ═══════════════════════════════════════════════════════════════════════════════
//  OPTIMIZER RENDERER (PHASE 3)
// ═══════════════════════════════════════════════════════════════════════════════

function renderOptimizer(data) {
  const wrap = document.getElementById("optimizer-wrap");
  const empty = document.getElementById("optimizer-empty");
  if (!wrap || !empty) return;

  const opt = data.optimization || {};
  const rawIrPre = document.getElementById("opt-raw-ir");
  const optIrPre = document.getElementById("opt-optimized-ir");
  const metricsGrid = document.getElementById("opt-metrics-grid");
  const logList = document.getElementById("opt-log-list");

  if (rawIrPre) rawIrPre.innerHTML = highlightTAC(data.ir || "; No Raw TAC");
  if (optIrPre) optIrPre.innerHTML = highlightTAC(data.optimized_ir || data.ir || "; No Optimized TAC");

  const cards = [
    { label: "Initial Quads", value: opt.initial_quad_count || 0 },
    { label: "Optimized Quads", value: opt.optimized_quad_count || 0 },
    { label: "Pruned Instructions", value: opt.instructions_eliminated || 0, cls: (opt.instructions_eliminated > 0 ? "pos" : "") },
    { label: "Code Size Reduction", value: `${(opt.reduction_pct || 0).toFixed(1)}%`, cls: (opt.reduction_pct > 0 ? "pos" : "") },
    { label: "Constant Folds", value: opt.constant_folds || 0 },
    { label: "CSE Deduplications", value: opt.cse_eliminations || 0 },
  ];

  if (metricsGrid) {
    metricsGrid.innerHTML = cards.map(c => `
      <div class="stat-card ${c.cls === "pos" ? "positive" : ""}">
        <div class="stat-label">${esc(c.label)}</div>
        <div class="stat-value ${c.cls || ""}">${esc(String(c.value))}</div>
      </div>
    `).join("");
  }

  if (logList) {
    logList.innerHTML = "";
    const logs = opt.transformation_log || [];
    if (logs.length === 0) {
      logList.innerHTML = `<li style="color:var(--text-muted)">Code is already optimal; no redundant instructions found.</li>`;
    } else {
      logs.forEach(l => {
        const li = document.createElement("li");
        li.textContent = `✓ ${l}`;
        logList.appendChild(li);
      });
    }
  }

  empty.classList.add("hidden");
  wrap.classList.remove("hidden");
}

function highlightTAC(irText) {
  return esc(irText)
    .replace(/(;[^\n]*)/g, '<span style="color:#868685">$1</span>')
    .replace(/\b(LABEL|GOTO|IF|IF_FALSE|IF_TRUE|CALL|CALL_IND|ACTION|ASSIGN)\b/g, '<span style="color:#163300;font-weight:700">$1</span>')
    .replace(/\b(BUY|SELL|STOP_LOSS|TAKE_PROFIT|ENTRY|EXIT)\b/g, '<span style="color:#054d28;font-weight:700">$1</span>')
    .replace(/\b(\d+(\.\d+)?)\b/g, '<span style="color:#0b4c72">$1</span>')
    .replace(/(t\d+)/g, '<span style="color:#6a6c6a">$1</span>');
}

// ═══════════════════════════════════════════════════════════════════════════════
//  BENCHMARK RENDERER (PHASE 3)
// ═══════════════════════════════════════════════════════════════════════════════

function renderBenchmark(bench) {
  const wrap = document.getElementById("benchmark-wrap");
  const empty = document.getElementById("benchmark-empty");
  if (!wrap || !empty) return;

  const cardsGrid = document.getElementById("bench-cards-grid");
  const stagesList = document.getElementById("bench-stages-list");

  const cards = [
    { label: "Total Latency", value: `${bench.total_time_ms.toFixed(2)} ms`, sub: "End-to-End Pipeline" },
    { label: "Peak Memory", value: `${bench.peak_memory_kb.toFixed(1)} KB`, sub: "Heap Allocation" },
    { label: "Dataset Size", value: `${bench.bars_processed} bars`, sub: "Simulation History" },
    { label: "Throughput", value: `${fmt(bench.bars_per_second)}`, sub: "Bars / second" },
  ];

  if (cardsGrid) {
    cardsGrid.innerHTML = cards.map(c => `
      <div class="stat-card">
        <div class="stat-label">${esc(c.label)}</div>
        <div class="stat-value" style="color:var(--accent-purple)">${esc(String(c.value))}</div>
        ${c.sub ? `<div class="stat-sub">${esc(c.sub)}</div>` : ""}
      </div>
    `).join("");
  }

  if (stagesList) {
    const timings = bench.timings || [];
    const maxTime = Math.max(...timings.map(t => t.duration_ms), 0.001);
    stagesList.innerHTML = timings.map(t => {
      const pct = Math.min(100, (t.duration_ms / maxTime) * 100);
      return `
        <div class="bench-stage-row">
          <div class="bench-stage-header">
            <span>${esc(t.stage_name)}</span>
            <span class="bench-stage-timing">${t.duration_ms.toFixed(3)} ms (${(t.pct_of_total || 0).toFixed(1)}%)</span>
          </div>
          <div class="bench-bar-track">
            <div class="bench-bar-fill" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
    }).join("");
  }

  empty.classList.add("hidden");
  wrap.classList.remove("hidden");
}

// ═══════════════════════════════════════════════════════════════════════════════
//  REPORT RENDERER
// ═══════════════════════════════════════════════════════════════════════════════

function renderReport(report, financial) {
  const wrap = document.getElementById("report-wrap");
  const empty = document.getElementById("report-empty");
  lastTrades = report.trades || [];

  renderStatsCards(report, financial);
  renderEquityCurve(report.equity_curve || []);
  renderTradeLog(report.trades || []);

  empty.classList.add("hidden");
  wrap.classList.remove("hidden");
}

function renderStatsCards(r, f) {
  const grid = document.getElementById("stats-grid");
  const returnPositive = r.return_pct >= 0;
  const pnlPositive = r.net_profit >= 0;

  const stats = [
    { label: "Strategy", value: r.strategy_name, sub: r.ticker },
    { label: "Initial Capital", value: `$${fmt(r.initial_capital)}`, sub: "" },
    { label: "Final Equity", value: `$${fmt(r.final_equity)}`, sub: "", cls: pnlPositive ? "pos" : "neg" },
    { label: "Net Profit", value: `${pnlPositive ? "+" : ""}$${fmt(r.net_profit)}`, sub: "", cls: pnlPositive ? "pos" : "neg" },
    { label: "Total Return", value: `${returnPositive ? "+" : ""}${r.return_pct.toFixed(2)}%`, sub: "", cls: returnPositive ? "pos" : "neg" },
    { label: "Win Rate", value: `${r.win_rate_pct.toFixed(1)}%`, sub: `${r.winning_trades}W / ${r.losing_trades}L`, cls: r.win_rate_pct >= 50 ? "pos" : "neg" },
    { label: "Max Drawdown", value: `-${Math.abs(r.max_drawdown_pct).toFixed(2)}%`, sub: "", cls: "neg" },
    { label: "Total Trades", value: r.total_trades, sub: `${r.total_bars} bars simulated` },
  ];

  if (f) {
    stats.push(
      { label: "Sharpe Ratio", value: f.sharpe_ratio.toFixed(2), sub: "Annualized" },
      { label: "Sortino Ratio", value: f.sortino_ratio.toFixed(2), sub: "Downside Risk" },
      { label: "Profit Factor", value: f.profit_factor.toFixed(2), sub: "Gross Win/Loss" },
      { label: "Annualized CAGR", value: `${f.annualized_return_pct >= 0 ? "+" : ""}${f.annualized_return_pct.toFixed(2)}%`, sub: "252 Trading Days" }
    );
  }

  grid.innerHTML = stats.map(s => `
    <div class="stat-card ${s.cls === "pos" ? "positive" : s.cls === "neg" ? "negative" : ""}">
      <div class="stat-label">${esc(s.label)}</div>
      <div class="stat-value ${s.cls || ""}">${esc(String(s.value))}</div>
      ${s.sub ? `<div class="stat-sub">${esc(s.sub)}</div>` : ""}
    </div>
  `).join("");
}

function renderEquityCurve(curve) {
  const canvas = document.getElementById("equity-chart");

  // Guard: if Chart.js CDN is still loading, retry up to 2 seconds
  if (typeof Chart === "undefined") {
    let attempts = 0;
    const retry = setInterval(() => {
      attempts++;
      if (typeof Chart !== "undefined") {
        clearInterval(retry);
        _drawEquityChart(canvas, curve);
      } else if (attempts >= 20) {
        clearInterval(retry);
        canvas.style.display = "none";
        const fallback = document.createElement("pre");
        fallback.style.cssText = "color:var(--text-muted);font-size:11px;padding:12px;";
        fallback.textContent = "Chart.js unavailable (offline?). Equity snapshot:\n" +
          curve.filter((_, i) => i % Math.max(1, Math.floor(curve.length / 20)) === 0)
            .map((v, i) => `  bar ${i * Math.max(1, Math.floor(curve.length / 20))}: $${v.toFixed(2)}`).join("\n");
        canvas.parentNode.insertBefore(fallback, canvas);
      }
    }, 100);
    return;
  }

  _drawEquityChart(canvas, curve);
}

function _drawEquityChart(canvas, curve) {
  const ctx = canvas.getContext("2d");
  canvas.style.display = "";

  if (equityChart) { equityChart.destroy(); equityChart = null; }

  const labels = curve.map((_, i) => i);
  const isProfit = curve.length > 0 && curve[curve.length - 1] >= curve[0];
  const color = isProfit ? "rgba(5,77,40,1)" : "rgba(203,39,47,1)";
  const fillColor = isProfit ? "rgba(159,232,112,0.15)" : "rgba(203,39,47,0.08)";

  equityChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Portfolio Equity ($)",
        data: curve,
        borderColor: color,
        backgroundColor: fillColor,
        borderWidth: 2,
        fill: true,
        pointRadius: 0,
        tension: 0.35,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400, easing: "easeOutQuart" },
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: "index",
          intersect: false,
          callbacks: {
            label: ctx => ` $${ctx.parsed.y.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
          },
          backgroundColor: "#163300",
          titleColor: "rgba(255,255,255,0.6)",
          bodyColor: "#9fe870",
          borderColor: "rgba(159,232,112,0.3)",
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          display: true,
          ticks: { color: "#868685", maxTicksLimit: 8, font: { size: 10 } },
          grid: { color: "rgba(14,15,12,0.05)" },
        },
        y: {
          display: true,
          ticks: {
            color: "#868685",
            font: { size: 10 },
            callback: v => `$${(v / 1000).toFixed(1)}k`,
          },
          grid: { color: "rgba(14,15,12,0.05)" },
        },
      },
      interaction: { mode: "nearest", axis: "x", intersect: false },
    },
  });
}

function renderTradeLog(trades) {
  const tbody = document.getElementById("trade-tbody");
  tbody.innerHTML = "";

  if (trades.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="8" style="text-align:center;color:var(--text-muted);padding:20px">No trades executed</td>`;
    tbody.appendChild(tr);
    return;
  }

  trades.forEach(t => {
    const isBuy = t.action.startsWith("BUY");
    const pnl = t.realized_pnl;
    const pnlStr = pnl === null ? "—" : `${pnl >= 0 ? "+" : ""}$${Math.abs(pnl).toFixed(2)}`;
    const retStr = t.return_pct === null ? "—" : `${t.return_pct >= 0 ? "+" : ""}${t.return_pct.toFixed(2)}%`;
    const pnlCls = pnl === null ? "" : pnl >= 0 ? "pnl-pos" : "pnl-neg";
    const retCls = t.return_pct === null ? "" : t.return_pct >= 0 ? "pnl-pos" : "pnl-neg";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color:var(--text-muted)">${t.id}</td>
      <td>${esc(t.date)}</td>
      <td style="color:var(--accent-cyan)">${esc(t.ticker)}</td>
      <td class="${isBuy ? "action-buy" : "action-sell"}">${esc(t.action)}</td>
      <td>${t.shares}</td>
      <td>$${t.price.toFixed(2)}</td>
      <td class="${pnlCls}">${pnlStr}</td>
      <td class="${retCls}">${retStr}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ─── Download CSV ─────────────────────────────────────────────────────────────
document.getElementById("btn-download-csv").addEventListener("click", async () => {
  if (!lastTrades.length) return;
  try {
    const res = await fetch("/api/download_csv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trades: lastTrades }),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "swayalang_trades.csv";
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error("CSV download failed:", e);
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
//  EXAMPLES GALLERY
// ═══════════════════════════════════════════════════════════════════════════════

async function loadExamples() {
  try {
    const res = await fetch("/api/examples");
    const data = await res.json();
    examplesList.innerHTML = "";
    data.forEach(ex => {
      const btn = document.createElement("button");
      btn.className = "example-btn";
      btn.textContent = ex.name;
      btn.title = `Load ${ex.filename}`;
      btn.addEventListener("click", () => {
        if (monacoEditor) {
          monacoEditor.setValue(ex.source);
          monacoEditor.focus();
          setStatus(`Loaded: ${ex.filename}`);
        }
      });
      examplesList.appendChild(btn);
    });
  } catch (e) {
    examplesList.innerHTML = `<span style="color:var(--text-muted);font-size:12px;padding:8px">Could not load examples</span>`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  UI HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

function setRunning(running) {
  if (running) {
    btnRun.textContent = "⏳ Running…";
    btnRun.classList.add("btn-running");
  } else {
    btnRun.textContent = "▶ Run";
    btnRun.classList.remove("btn-running");
  }
}

function setStatus(msg) { statusLeft.textContent = msg; }

function showError(msg, stage, line) {
  errorText.textContent = msg;
  errorBar.classList.remove("hidden");

  // Highlight error line in Monaco
  if (monacoEditor && line) {
    monacoEditor.deltaDecorations([], [{
      range: new monaco.Range(line, 1, line, 1),
      options: {
        isWholeLine: true,
        className: "errorLineDecoration",
        glyphMarginClassName: "errorGlyphDecoration",
      },
    }]);
  }
}

function clearError() {
  errorBar.classList.add("hidden");
  errorText.textContent = "";
  if (monacoEditor) monacoEditor.deltaDecorations(monacoEditor.getModel()?.getAllDecorations().map(d => d.id) || [], []);
}

function showWarnings(warnings) {
  // Remove old warnings bar if any
  document.querySelectorAll(".warnings-bar").forEach(el => el.remove());
  if (!warnings.length) return;
  const bar = document.createElement("div");
  bar.className = "warnings-bar";
  bar.textContent = `⚠ ${warnings.length} warning${warnings.length > 1 ? "s" : ""}: ${warnings.join("; ")}`;
  errorBar.insertAdjacentElement("afterend", bar);
}

function clearAllPanels() {
  // Hide all content, show all empties
  const ids = ["tokens-wrap", "ast-wrap", "symbols-wrap", "ir-code", "optimizer-wrap", "report-wrap", "benchmark-wrap"];
  ids.forEach(id => document.getElementById(id)?.classList.add("hidden"));
  const empties = ["tokens-empty", "ast-empty", "symbols-empty", "ir-empty", "optimizer-empty", "report-empty", "benchmark-empty"];
  empties.forEach(id => document.getElementById(id)?.classList.remove("hidden"));

  document.getElementById("token-tbody").innerHTML = "";
  document.getElementById("ast-tree").innerHTML = "";
  document.getElementById("symbols-scopes").innerHTML = "";
  document.getElementById("ir-code").innerHTML = "";
  document.getElementById("stats-grid").innerHTML = "";
  document.getElementById("trade-tbody").innerHTML = "";
  document.querySelectorAll(".warnings-bar").forEach(el => el.remove());
}

function esc(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmt(n) {
  return Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
