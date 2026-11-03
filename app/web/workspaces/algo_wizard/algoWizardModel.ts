/** Local editor view models and canonical HSL transport contracts. */
export type EditorMode =
  "Simple" | "Full" | "Stockpicker" | "Single-asset cloud";
export type RuleKind =
  | "Signal"
  | "Fuzzy Logic Signals"
  | "If - Then"
  | "If - Then - Else"
  | "Action only";
export interface Block {
  id: string;
  text: string;
}
export interface Signal {
  id: string;
  variable: string;
  conditions: Block[];
}
export interface Rule {
  id: string;
  name: string;
  kind: RuleKind;
  trigger: string;
  signals: Signal[];
  conditions: Block[];
  actions: Block[];
  otherwise: Block[];
}
export interface Variable {
  name: string;
  value: string;
  type: string;
  configurable: boolean;
}
export interface Draft {
  id: string;
  name: string;
  mode: EditorMode;
  rules: Rule[];
  variables: Variable[];
  settings: Record<string, string>;
  charts: string[];
  debug: boolean;
}
export interface History {
  present: Draft;
  past: Draft[];
  future: Draft[];
  saved: string;
  origin: "local" | "retester";
}
export const uid = () => crypto.randomUUID();
export const block = (text: string): Block => ({ id: uid(), text });
export const makeRule = (name: string, kind: RuleKind = "If - Then"): Rule => ({
  id: uid(),
  name,
  kind,
  trigger: "On Bar Open",
  signals: [],
  conditions: [],
  actions: [],
  otherwise: [],
});
export function uniqueName(name: string, existing: string[]): string {
  const base = name.trim() || "New strategy";
  let candidate = base;
  for (let i = 2; existing.includes(candidate); i++) candidate = `${base} ${i}`;
  return candidate;
}
export function makeDraft(
  name: string,
  mode: EditorMode,
  template = false,
): Draft {
  const signals = makeRule("Trading signals", "Signal");
  signals.signals = ["LongEntrySignal", "ShortEntrySignal"].map((variable) => ({
    id: uid(),
    variable,
    conditions: [],
  }));
  return {
    id: uid(),
    name,
    mode,
    rules:
      template || mode !== "Full"
        ? [signals, makeRule("Long entry"), makeRule("Short entry")]
        : [],
    variables: [
      "LongEntrySignal",
      "ShortEntrySignal",
      "LongExitSignal",
      "ShortExitSignal",
    ].map((name) => ({
      name,
      value: "false",
      type: "Boolean",
      configurable: false,
    })),
    settings: {
      Engine: "MetaTrader4",
      Symbol: "AUDUSD_dukascopy",
      Timeframe: "H1",
      "Start date": "2021-09-19",
      "End date": "2026-09-18",
      Precision: "Selected timeframe only (fastest)",
      "Initial capital": "10000",
      "Money management": "Fixed size",
      "Order size": "0.1",
      "Maximum positions": "1",
      "Trading direction": "Both",
      "Template mode": "Off",
      Slippage: "0",
      Commission: "0",
      "Stop Loss": "0",
      "Profit Target": "0",
      "Position score": "RSI(14)[1]",
      "Maximum stocks": "5",
    },
    charts: ["Main chart"],
    debug: false,
  };
}
export const startHistory = (present: Draft): History => ({
  present,
  past: [],
  future: [],
  saved: JSON.stringify(present),
  origin: "local",
});
export function revise(history: History, present: Draft): History {
  if (JSON.stringify(history.present) === JSON.stringify(present))
    return history;
  return {
    ...history,
    present,
    past: [...history.past.slice(-99), history.present],
    future: [],
  };
}
export function travel(history: History, direction: "undo" | "redo"): History {
  if (direction === "undo") {
    const present = history.past.at(-1);
    return present
      ? {
          ...history,
          present,
          past: history.past.slice(0, -1),
          future: [history.present, ...history.future],
        }
      : history;
  }
  const present = history.future[0];
  return present
    ? {
        ...history,
        present,
        past: [...history.past, history.present],
        future: history.future.slice(1),
      }
    : history;
}
export const dirty = (history: History) =>
  history.saved !== JSON.stringify(history.present);
export const canSimplify = (draft: Draft) =>
  draft.rules.length === 0 ||
  (draft.rules.length === 3 &&
    new Set(draft.rules.map((r) => r.name)).size === 3 &&
    draft.rules.every(
      (r) =>
        ["Trading signals", "Long entry", "Short entry"].includes(r.name) &&
        r.trigger === "On Bar Open" &&
        r.kind === (r.name === "Trading signals" ? "Signal" : "If - Then"),
    ) &&
    draft.rules
      .find((r) => r.kind === "Signal")
      ?.signals.every((s) =>
        [
          "LongEntrySignal",
          "ShortEntrySignal",
          "LongExitSignal",
          "ShortExitSignal",
        ].includes(s.variable),
      ));
export const encodeDraft = (draft: Draft) =>
  JSON.stringify(
    { format: "haruquantai.algowizard.ui", version: 1, draft },
    null,
    2,
  );
export function decodeDraft(text: string): Draft {
  const fail = () => {
    throw new Error(
      "Invalid prototype strategy. Select a HaruQuantAI AlgoWizard UI JSON file (version 1). SQX archives are not supported.",
    );
  };
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    return fail();
  }
  const obj = (v: unknown): v is Record<string, unknown> =>
    !!v && typeof v === "object" && !Array.isArray(v);
  const str = (v: unknown): v is string => typeof v === "string";
  const blocks = (v: unknown) =>
    Array.isArray(v) && v.every((b) => obj(b) && str(b.id) && str(b.text));
  if (
    !obj(data) ||
    data.format !== "haruquantai.algowizard.ui" ||
    data.version !== 1 ||
    !obj(data.draft)
  )
    return fail();
  const d = data.draft;
  if (
    !str(d.name) ||
    !str(d.id) ||
    !["Simple", "Full", "Stockpicker", "Single-asset cloud"].includes(
      String(d.mode),
    ) ||
    !Array.isArray(d.rules) ||
    !Array.isArray(d.variables) ||
    !obj(d.settings) ||
    !Object.values(d.settings).every(str) ||
    !Array.isArray(d.charts) ||
    !d.charts.every(str) ||
    typeof d.debug !== "boolean"
  )
    return fail();
  if (
    !d.rules.every(
      (r) =>
        obj(r) &&
        str(r.id) &&
        str(r.name) &&
        str(r.trigger) &&
        [
          "Signal",
          "Fuzzy Logic Signals",
          "If - Then",
          "If - Then - Else",
          "Action only",
        ].includes(String(r.kind)) &&
        blocks(r.conditions) &&
        blocks(r.actions) &&
        blocks(r.otherwise) &&
        Array.isArray(r.signals) &&
        r.signals.every(
          (s) => obj(s) && str(s.id) && str(s.variable) && blocks(s.conditions),
        ),
    )
  )
    return fail();
  if (
    !d.variables.every(
      (v) =>
        obj(v) &&
        str(v.name) &&
        /^[A-Za-z_][A-Za-z0-9_]*$/.test(v.name) &&
        str(v.value) &&
        str(v.type) &&
        typeof v.configurable === "boolean",
    )
  )
    return fail();
  if (
    ![
      "Engine",
      "Symbol",
      "Timeframe",
      "Start date",
      "End date",
      "Precision",
      "Initial capital",
      "Order size",
      "Money management",
    ].every((key) => obj(d.settings) && str(d.settings[key]))
  )
    return fail();
  const draft = d as unknown as Draft;
  const ids = draft.rules.flatMap((r) => [
    r.id,
    ...r.signals.flatMap((s) => [s.id, ...s.conditions.map((b) => b.id)]),
    ...[...r.conditions, ...r.actions, ...r.otherwise].map((b) => b.id),
  ]);
  if (new Set(ids).size !== ids.length) return fail();
  return { ...draft, id: uid() };
}
export function downloadText(name: string, text: string) {
  const url = URL.createObjectURL(
    new Blob([text], { type: "application/json" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ============================================================================
// HSL 1.0 Canonical AST, Catalogue, Lifecycle, Visual Block & Cloud Contracts
// ============================================================================

export type HSLNodeFamily =
  "VALUE" | "EXPRESSION" | "CONDITION" | "ACTION" | "RULE";

export type HSLLifecycleEventType =
  | "on_start"
  | "on_stop"
  | "on_timer"
  | "on_tick"
  | "on_bar_open"
  | "on_bar_close"
  | "on_order_submitted"
  | "on_order_filled"
  | "on_order_cancelled"
  | "on_order_rejected"
  | "on_position_opened"
  | "on_position_closed"
  | "on_session_open"
  | "on_session_close";

export interface HSLParameterSpec {
  type: "int" | "float" | "bool" | "str";
  default: number | boolean | string;
  min?: number;
  max?: number;
  step?: number;
  optimize: boolean;
  description: string;
}

export interface HSLVariableSpec {
  type: "int" | "float" | "bool" | "str";
  initial: number | boolean | string;
  scope: "strategy" | "session";
}

export interface HSLEvaluationContext {
  symbol: string;
  timeframe: string;
  shift: number;
}

export type HSLComparisonOperator =
  | "greater_than"
  | "greater_or_equal"
  | "less_than"
  | "less_or_equal"
  | "equal"
  | "not_equal"
  | "crosses_above"
  | "crosses_below";

export interface HSLOperandNode {
  type:
    | "value"
    | "parameter"
    | "variable"
    | "price"
    | "indicator"
    | "math"
    | "function"
    | "position_attr";
  value?: number | boolean | string;
  name?: string;
  field?: string;
  output?: string;
  inputs?: Record<string, HSLOperandNode>;
  left?: HSLOperandNode;
  right?: HSLOperandNode;
  args?: HSLOperandNode[];
  operator?: string;
  params?: Record<string, unknown>;
  context?: HSLEvaluationContext;
}

export interface HSLConditionNode {
  type: "logical" | "not" | "comparison" | "state" | "temporal";
  operator?: "and" | "or" | HSLComparisonOperator;
  conditions?: HSLConditionNode[];
  condition?: HSLConditionNode;
  left?: HSLOperandNode;
  right?: HSLOperandNode;
  state?: string;
  bars?: number;
}

export interface HSLActionNode {
  type: "action";
  action:
    | "enter_market"
    | "enter_stop"
    | "enter_limit"
    | "exit_position"
    | "modify_stop_loss"
    | "modify_take_profit"
    | "cancel_orders"
    | "set_variable"
    | "emit_alert";
  side?: "long" | "short";
  target_side?: "long" | "short" | "any";
  quantity_pct?: number;
  entry_price?: HSLOperandNode;
  expiration_bars?: number;
  magic_number?: number;
  level?: "info" | "warning" | "error";
  name?: string;
  message?: string;
  value?: HSLOperandNode;
}

export interface HSLRuleNode {
  id: string;
  name: string;
  priority: number;
  enabled: boolean;
  event:
    | HSLLifecycleEventType
    | { type: HSLLifecycleEventType; symbol?: string; timeframe?: string };
  when: HSLConditionNode;
  then: HSLActionNode[];
  else_then: HSLActionNode[];
}

export interface HSLStrategyPayload {
  id: string;
  name: string;
  description: string;
  enabled?: boolean;
  metadata?: Record<string, unknown>;
  money_management?: Record<string, unknown>;
  risk_management?: Record<string, unknown>;
  trade_management?: Record<string, unknown>;
  trading_options?: Record<string, unknown>;
  universe: {
    symbols: string[];
  };
  timeframe: {
    primary: string;
    additional: string[];
  };
  parameters: Record<string, HSLParameterSpec>;
  variables: Record<string, HSLVariableSpec>;
  rules: HSLRuleNode[];
}

export interface HSLStrategyDocument {
  schema_version: "1.0.0";
  strategy: HSLStrategyPayload;
}

export interface CatalogueOptionItem {
  key: string;
  label: string;
  description: string;
}

export interface CommissionMethodDescriptor {
  method_id: string;
  label: string;
  unit: string;
  default_value: number;
}

export interface HSLBlockParameterMeta {
  key: string;
  label: string;
  value_type: string;
  required: boolean;
  default_value: number | boolean | string | null;
  min_value?: number | null;
  max_value?: number | null;
  step?: number | null;
}

export interface HSLBlockCatalogueEntry {
  semantic_id: string;
  registry_block_id: string;
  family: HSLNodeFamily;
  category: string;
  label: string;
  return_type: string;
  parameters: HSLBlockParameterMeta[];
  allowed_children: string[];
}

export interface WizardConstantsBundle {
  schema_version: string;
  timeframes: CatalogueOptionItem[];
  precisions: CatalogueOptionItem[];
  lifecycle_events: CatalogueOptionItem[];
  commission_methods: CommissionMethodDescriptor[];
  blocks: HSLBlockCatalogueEntry[];
}

export interface ValidationIssue {
  code: string;
  message: string;
  path: string;
  node_id?: string | null;
}

export interface ValidationReport {
  valid: boolean;
  issues: ValidationIssue[];
}

export type StrategyRuntimeStatus = "IDLE" | "RUNNING" | "STOPPED" | "ERROR";

export interface ManagedStrategyRecord {
  strategy_id: string;
  name: string;
  status: StrategyRuntimeStatus;
  revision: number;
  document_hash: string;
  document: HSLStrategyDocument;
  validation: ValidationReport;
  updated_at: string;
}

export interface CustomBlockDefinition {
  block_id: string;
  name: string;
  category: "condition" | "expression" | "action";
  description: string;
  parameters: Record<string, HSLParameterSpec>;
  condition?: HSLConditionNode | null;
  expression?: HSLOperandNode | null;
  action?: HSLActionNode | null;
}

export interface BlockGroupDefinition {
  group_id: string;
  name: string;
  description: string;
  block_ids: string[];
}

export interface ResourceCheckResult {
  ready: boolean;
  missing_symbols: string[];
  missing_timeframes: string[];
  missing_blocks: string[];
}

export interface WizardTradeLogEntry {
  bar_index: number;
  timestamp: string;
  action: string;
  side: string;
  price: number;
  quantity: number;
}

export interface WizardBacktestResult {
  run_id: string;
  strategy_id: string;
  status: "COMPLETED" | "STOPPED" | "ERROR";
  bars_processed: number;
  orders_submitted: number;
  ending_position: number;
  net_pnl: number;
  ending_equity: number;
  trade_log: WizardTradeLogEntry[];
}

export interface WizardExampleSummary {
  example_id: string;
  name: string;
  category: string;
  description: string;
  tags: string[];
}

export interface WizardExamplePayload {
  summary: WizardExampleSummary;
  document: HSLStrategyDocument;
}

export interface RetesterHandoffResult {
  strategy_id: string;
  name: string;
  document_hash: string;
  hsl_document: HSLStrategyDocument;
  compiled_rule_count: number;
  status: "READY";
}

export type CloudImportSource = "editor" | "file" | "databank" | "backtest_id";

export type ExportTargetPlatform =
  | "python"
  | "mql4"
  | "mql5"
  | "easylanguage"
  | "ninjatrader"
  | "jforex"
  | "pseudo_code"
  | "hsl_json";

export interface ExportTargetDescriptor {
  supported_for_hsl?: boolean;
  platform: ExportTargetPlatform;
  label: string;
  extension: string;
  description: string;
}

export interface CloudImportResult {
  source: CloudImportSource;
  document: HSLStrategyDocument;
  validation: ValidationReport;
}

export interface ExportStrategyResult {
  strategy_id: string;
  target_platform: ExportTargetPlatform;
  filename: string;
  content: string;
  sha256: string;
}

const COMPARISON_NEGATION_MAP: Record<
  HSLComparisonOperator,
  HSLComparisonOperator
> = {
  greater_than: "less_or_equal",
  greater_or_equal: "less_than",
  less_than: "greater_or_equal",
  less_or_equal: "greater_than",
  equal: "not_equal",
  not_equal: "equal",
  crosses_above: "crosses_below",
  crosses_below: "crosses_above",
};

export function filterCatalogueBlocks(
  blocks: readonly HSLBlockCatalogueEntry[],
  family: HSLNodeFamily | "ALL",
  query: string,
): HSLBlockCatalogueEntry[] {
  const normalizedQuery = query.trim().toLowerCase();
  return blocks.filter((entry) => {
    if (family !== "ALL" && entry.family !== family) {
      return false;
    }
    if (!normalizedQuery) {
      return true;
    }
    return (
      entry.semantic_id.toLowerCase().includes(normalizedQuery) ||
      entry.label.toLowerCase().includes(normalizedQuery) ||
      entry.category.toLowerCase().includes(normalizedQuery) ||
      entry.registry_block_id.toLowerCase().includes(normalizedQuery)
    );
  });
}

export function sortRulesByPriority(
  rules: readonly HSLRuleNode[],
): HSLRuleNode[] {
  return [...rules].sort((left, right) => {
    if (left.priority !== right.priority) {
      return left.priority - right.priority;
    }
    return left.id.localeCompare(right.id);
  });
}

export function negateHSLCondition(
  condition: HSLConditionNode,
  distributeLogical = false,
): HSLConditionNode {
  if (condition.type === "not" && condition.condition) {
    return condition.condition;
  }
  if (
    condition.type === "comparison" &&
    condition.operator &&
    condition.operator in COMPARISON_NEGATION_MAP
  ) {
    const inverted =
      COMPARISON_NEGATION_MAP[condition.operator as HSLComparisonOperator];
    return {
      ...condition,
      operator: inverted,
    };
  }
  if (
    distributeLogical &&
    condition.type === "logical" &&
    condition.conditions &&
    (condition.operator === "and" || condition.operator === "or")
  ) {
    return {
      type: "logical",
      operator: condition.operator === "and" ? "or" : "and",
      conditions: condition.conditions.map((item) =>
        negateHSLCondition(item, true),
      ),
    };
  }
  return {
    type: "not",
    condition,
  };
}

export const DEFAULT_WIZARD_CONSTANTS_BUNDLE: WizardConstantsBundle = {
  schema_version: "1.0.0",
  timeframes: [
    { key: "M1", label: "1 Minute", description: "1-minute bars" },
    { key: "M15", label: "15 Minutes", description: "15-minute bars" },
    { key: "H1", label: "1 Hour", description: "Hourly bars" },
    { key: "D1", label: "Daily", description: "Daily bars" },
  ],
  precisions: [
    {
      key: "selected_tf_only",
      label: "Selected Timeframe Only",
      description: "Fastest bar-open / bar-close simulation",
    },
    {
      key: "m1_tick_simulation",
      label: "1 Minute Data Tick Simulation",
      description: "Intraday M1 bar interpolation",
    },
    {
      key: "real_tick",
      label: "Real Tick",
      description: "Exact historical tick feed",
    },
  ],
  lifecycle_events: [
    {
      key: "on_bar_open",
      label: "On Bar Open",
      description: "Triggered at bar open",
    },
    {
      key: "on_bar_close",
      label: "On Bar Close",
      description: "Triggered at bar close",
    },
    {
      key: "on_tick",
      label: "On Tick",
      description: "Triggered on every market tick",
    },
  ],
  commission_methods: [
    {
      method_id: "percentage",
      label: "Percentage Based",
      unit: "%",
      default_value: 0.01,
    },
    {
      method_id: "fixed_per_lot",
      label: "Size Based",
      unit: "USD/lot",
      default_value: 7.0,
    },
  ],
  blocks: [
    {
      semantic_id: "market.close",
      registry_block_id: "close",
      family: "VALUE",
      category: "market",
      label: "Market Close",
      return_type: "float",
      parameters: [],
      allowed_children: [],
    },
    {
      semantic_id: "indicator.rsi",
      registry_block_id: "rsi",
      family: "EXPRESSION",
      category: "indicator",
      label: "Relative Strength Index (RSI)",
      return_type: "float",
      parameters: [
        {
          key: "period",
          label: "Period",
          value_type: "int",
          required: true,
          default_value: 14,
          min_value: 2,
          max_value: 200,
          step: 1,
        },
      ],
      allowed_children: ["VALUE"],
    },
    {
      semantic_id: "comparison.crosses_above",
      registry_block_id: "cross_over",
      family: "CONDITION",
      category: "comparison",
      label: "Crosses Above",
      return_type: "bool",
      parameters: [],
      allowed_children: ["VALUE", "EXPRESSION"],
    },
    {
      semantic_id: "order.enter_market",
      registry_block_id: "buy",
      family: "ACTION",
      category: "order",
      label: "Enter At Market",
      return_type: "action",
      parameters: [],
      allowed_children: ["VALUE", "EXPRESSION"],
    },
    {
      semantic_id: "rule.if_then",
      registry_block_id: "if_then",
      family: "RULE",
      category: "rule",
      label: "If-Then Rule",
      return_type: "rule",
      parameters: [],
      allowed_children: ["CONDITION", "ACTION"],
    },
  ],
};

export const DEFAULT_HSL_STRATEGY_DOCUMENT: HSLStrategyDocument = {
  schema_version: "1.0.0",
  strategy: {
    id: "hsl_ema_crossover_v1",
    name: "EMA Crossover Strategy",
    description: "Canonical HSL 1.0 EMA crossover with RSI filter",
    universe: {
      symbols: ["EURUSD"],
    },
    timeframe: {
      primary: "H1",
      additional: ["D1"],
    },
    parameters: {
      fast_period: {
        type: "int",
        default: 12,
        min: 2,
        max: 100,
        step: 1,
        optimize: true,
        description: "Fast EMA period",
      },
      slow_period: {
        type: "int",
        default: 26,
        min: 5,
        max: 200,
        step: 1,
        optimize: true,
        description: "Slow EMA period",
      },
    },
    variables: {
      entry_count: {
        type: "int",
        initial: 0,
        scope: "strategy",
      },
      session_active: {
        type: "bool",
        initial: true,
        scope: "session",
      },
    },
    rules: [
      {
        id: "rule_long_entry",
        name: "Long Entry on Fast EMA Crosses Above Slow EMA",
        priority: 10,
        enabled: true,
        event: "on_bar_open",
        when: {
          type: "comparison",
          operator: "crosses_above",
          left: {
            type: "indicator",
            name: "indicator.ema",
            params: { period: { type: "parameter", name: "fast_period" } },
            context: {
              symbol: "$current_symbol",
              timeframe: "$current_timeframe",
              shift: 1,
            },
          },
          right: {
            type: "indicator",
            name: "indicator.ema",
            params: { period: { type: "parameter", name: "slow_period" } },
            context: {
              symbol: "$current_symbol",
              timeframe: "$current_timeframe",
              shift: 1,
            },
          },
        },
        then: [{ type: "action", action: "enter_market", side: "long" }],
        else_then: [],
      },
      {
        id: "rule_short_exit",
        name: "Exit Position on Opposite Signal",
        priority: 20,
        enabled: true,
        event: "on_bar_close",
        when: {
          type: "comparison",
          operator: "greater_than",
          left: {
            type: "indicator",
            name: "indicator.rsi",
            params: { period: { type: "value", value: 14 } },
            context: {
              symbol: "$current_symbol",
              timeframe: "$current_timeframe",
              shift: 1,
            },
          },
          right: { type: "value", value: 70 },
        },
        then: [
          { type: "action", action: "exit_position", target_side: "long" },
        ],
        else_then: [],
      },
    ],
  },
};

export const DEFAULT_WIZARD_EXAMPLES: WizardExampleSummary[] = [
  {
    example_id: "ema_crossover",
    name: "EMA Crossover",
    category: "Trend Following",
    description: "Dual EMA crossover entry with ATR stop loss and take profit.",
    tags: ["ema", "trend", "crossover"],
  },
  {
    example_id: "rsi_mean_reversion",
    name: "RSI Mean Reversion",
    category: "Mean Reversion",
    description: "Oversold/overbought RSI reversal strategy.",
    tags: ["rsi", "oscillator", "mean-reversion"],
  },
  {
    example_id: "atr_breakout",
    name: "ATR Volatility Breakout",
    category: "Breakout",
    description: "Channel breakout scaled by Average True Range.",
    tags: ["atr", "breakout", "volatility"],
  },
  {
    example_id: "mtf_trend_filter",
    name: "Multi-Timeframe Trend Filter",
    category: "Multi-Timeframe",
    description: "Higher timeframe D1 EMA trend filter with H1 pullback entry.",
    tags: ["mtf", "d1", "h1"],
  },
];

export const DEFAULT_EXPORT_TARGETS: ExportTargetDescriptor[] = [
  {
    platform: "python",
    label: "HaruQuant Python",
    extension: ".py",
    description: "Native HaruQuant Python strategy module",
  },
  {
    platform: "mql4",
    label: "MetaTrader 4 (MQL4)",
    extension: ".mq4",
    description: "MetaTrader 4 Expert Advisor source code",
  },
  {
    platform: "mql5",
    label: "MetaTrader 5 (MQL5)",
    extension: ".mq5",
    description: "MetaTrader 5 Expert Advisor source code",
  },
  {
    platform: "easylanguage",
    label: "TradeStation EasyLanguage",
    extension: ".eld",
    description: "TradeStation / MultiCharts EasyLanguage strategy",
  },
  {
    platform: "ninjatrader",
    label: "NinjaTrader 8 (C#)",
    extension: ".cs",
    description: "NinjaScript C# strategy class",
  },
  {
    platform: "jforex",
    label: "Dukascopy JForex (Java)",
    extension: ".java",
    description: "JForex IStrategy Java implementation",
  },
  {
    platform: "pseudo_code",
    label: "Human-Readable PseudoCode",
    extension: ".txt",
    description: "Structured English specification of strategy rules",
  },
  {
    platform: "hsl_json",
    label: "Canonical HSL 1.0 JSON",
    extension: ".json",
    description: "Deterministic HSL 1.0 JSON strategy document",
  },
];

interface WireConstantsBundle {
  revision: string;
  timeframes: Array<{ code: string; label: string; description: string }>;
  lifecycle_events: Array<{ code: string; label: string; description: string }>;
  commission_methods: Array<{
    method_id: string;
    name: string;
    unit: string;
    default_value: number;
  }>;
  blocks: Array<{
    semantic_id: string;
    registry_id: string;
    name: string;
    family: HSLNodeFamily;
    category: string;
    return_type: string;
    required_inputs: string[];
    parameters: Array<{
      name: string;
      param_type: string;
      required: boolean;
      default: number | boolean | string | null;
      min_value?: number | null;
      max_value?: number | null;
    }>;
  }>;
}

export interface AlgoWizardApiClientOptions {
  fetchFn?: typeof fetch;
  baseUrl?: string;
}

export function createAlgoWizardApiClient(
  options: AlgoWizardApiClientOptions = {},
) {
  const fetchFn = options.fetchFn ?? fetch;
  const baseUrl = (options.baseUrl ?? "").replace(/\/$/, "");

  async function postJson<T>(path: string, body: unknown): Promise<T> {
    const response = await fetchFn(`${baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = (await response.json()) as {
      data?: T;
      error?: { message?: string };
      message?: string;
    };
    if (!response.ok || payload.data === undefined) {
      throw new Error(
        payload.error?.message ??
          payload.message ??
          `Request failed (${response.status})`,
      );
    }
    return payload.data;
  }

  async function getJson<T>(path: string): Promise<T> {
    const response = await fetchFn(`${baseUrl}${path}`, {
      method: "GET",
    });
    const payload = (await response.json()) as {
      data?: T;
      error?: { message?: string };
      message?: string;
    };
    if (!response.ok || payload.data === undefined) {
      throw new Error(
        payload.error?.message ??
          payload.message ??
          `Request failed (${response.status})`,
      );
    }
    return payload.data;
  }

  return {
    getConstantsBundle(requestId = "req-constants-all") {
      return postJson<WireConstantsBundle>("/constants/getAll", {
        request_id: requestId,
      }).then((bundle): WizardConstantsBundle => ({
        schema_version: "1.0.0",
        timeframes: bundle.timeframes.map((option) => ({
          ...option,
          key: option.code,
        })),
        lifecycle_events: bundle.lifecycle_events.map((option) => ({
          ...option,
          key: option.code,
        })),
        precisions: [
          {
            key: "OHLC",
            label: "OHLC bars",
            description: "Historical bar execution",
          },
        ],
        commission_methods: bundle.commission_methods.map((method) => ({
          ...method,
          label: method.name,
        })),
        blocks: bundle.blocks.map((block) => ({
          ...block,
          registry_block_id: block.registry_id,
          label: block.name,
          allowed_children: [],
          parameters: block.parameters.map((parameter) => ({
            ...parameter,
            key: parameter.name,
            label: parameter.name,
            value_type: parameter.param_type,
            default_value: parameter.default,
          })),
        })),
      }));
    },
    listExamples() {
      return getJson<WizardExampleSummary[]>(
        "/AlgoWizard/examples/examples.json",
      );
    },
    loadExample(exampleId: string, requestId = "req-load-example") {
      return postJson<WizardExamplePayload>("/algowizard/loadExample", {
        request_id: requestId,
        example_id: exampleId,
      });
    },
    saveToRetester(
      document: HSLStrategyDocument,
      requestId = "req-save-retester",
    ) {
      return postJson<RetesterHandoffResult>("/algowizard/saveToRetester", {
        request_id: requestId,
        document,
      });
    },
    startStrategy(strategyId: string, requestId = "req-strategy-start") {
      return postJson<ManagedStrategyRecord>("/strategy/start", {
        request_id: requestId,
        strategy_id: strategyId,
      });
    },
    stopStrategy(strategyId: string, requestId = "req-strategy-stop") {
      return postJson<ManagedStrategyRecord>("/strategy/stop", {
        request_id: requestId,
        strategy_id: strategyId,
      });
    },
    removeStrategy(strategyId: string, requestId = "req-strategy-remove") {
      return postJson<{ strategy_id: string; removed: boolean }>(
        "/strategy/remove",
        {
          request_id: requestId,
          strategy_id: strategyId,
        },
      );
    },
    importCloudStrategy(
      request: {
        source: CloudImportSource;
        document?: HSLStrategyDocument;
        file_id?: string;
        databank_name?: string;
        strategy_name?: string;
        backtest_id?: string;
      },
      requestId = "req-cloud-import",
    ) {
      return postJson<CloudImportResult>("/algocloud/import", {
        request_id: requestId,
        ...request,
      });
    },
    exportCloudStrategy(
      document: HSLStrategyDocument,
      targetPlatform: ExportTargetPlatform,
      requestId = "req-cloud-export",
    ) {
      return postJson<ExportStrategyResult>("/algocloud/export", {
        request_id: requestId,
        document,
        target_platform: targetPlatform,
      });
    },
  };
}
