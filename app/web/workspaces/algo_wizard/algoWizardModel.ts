/** Local UI documents only: these types are not an execution or SQX wire schema. */
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
