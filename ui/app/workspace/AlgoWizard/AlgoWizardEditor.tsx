import { useEffect, useState } from "react";
import { Menu, Plus, X } from "lucide-react";
import { AWConfirm, AWField } from "./AlgoWizardControls";
import { AlgoWizardBlockEditor } from "./AlgoWizardBlockEditor";
import { AlgoWizardRuleDialog } from "./AlgoWizardRuleDialogs";
import {
  block,
  uid,
  type Draft,
  type Rule,
  type Block,
} from "./algoWizardModel";
interface Destination {
  ruleId: string;
  section: "conditions" | "actions" | "otherwise";
  signalId?: string;
  blockId?: string;
  newSignalVariable?: string;
}
export function AlgoWizardEditor({
  draft,
  onChange,
}: {
  draft: Draft;
  onChange: (draft: Draft) => void;
}) {
  const [selected, setSelected] = useState(draft.rules[0]?.id);
  const [ruleMenu, setRuleMenu] = useState<string | null>(null);
  const [dialog, setDialog] = useState<Rule | "new" | null>(null);
  const [editing, setEditing] = useState<Destination | null>(null);
  const [blockMenu, setBlockMenu] = useState<string | null>(null);
  const [clipboard, setClipboard] = useState<Block | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [dragged, setDragged] = useState<string | null>(null);
  const [pickerTab, setPickerTab] = useState("Long");
  useEffect(() => {
    const dismiss = (event: PointerEvent) => {
      if (!(event.target as HTMLElement).closest(".aw-menu-anchor")) {
        setRuleMenu(null);
        setBlockMenu(null);
      }
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setRuleMenu(null);
        setBlockMenu(null);
      }
    };
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", escape);
    };
  }, []);
  const rule = draft.rules.find((r) => r.id === selected) ?? draft.rules[0];
  const updateRule = (next: Rule) =>
    onChange({
      ...draft,
      rules: draft.rules.map((r) => (r.id === next.id ? next : r)),
    });
  const getBlocks = (d: Destination) => {
    const r = draft.rules.find((r) => r.id === d.ruleId);
    return d.signalId
      ? (r?.signals.find((s) => s.id === d.signalId)?.conditions ?? [])
      : (r?.[d.section] ?? []);
  };
  const changeBlocks = (dest: Destination, blocks: Block[]) => {
    const r = draft.rules.find((r) => r.id === dest.ruleId);
    if (!r) return;
    if (dest.newSignalVariable) {
      updateRule({
        ...r,
        signals: [
          ...r.signals,
          {
            id: dest.signalId ?? uid(),
            variable: dest.newSignalVariable,
            conditions: blocks,
          },
        ],
      });
      return;
    }
    updateRule(
      dest.signalId
        ? {
            ...r,
            signals: r.signals.map((s) =>
              s.id === dest.signalId ? { ...s, conditions: blocks } : s,
            ),
          }
        : { ...r, [dest.section]: blocks },
    );
  };
  const reorder = (id: string, offset: number) => {
    const rules = [...draft.rules];
    const i = rules.findIndex((r) => r.id === id);
    const j = i + offset;
    if (j < 0 || j >= rules.length) return;
    [rules[i], rules[j]] = [rules[j], rules[i]];
    onChange({ ...draft, rules });
  };
  const list = (blocks: Block[], dest: Destination) => (
    <div className="aw-block-rows">
      {blocks.map((b, i) => (
        <div className="aw-block-row" key={b.id}>
          <button
            className="aw-expression-link"
            onClick={() => setEditing({ ...dest, blockId: b.id })}
          >
            {i > 0 && <b>AND </b>}
            {b.text}
          </button>
          <div className="aw-menu-anchor">
            <button
              aria-label={`Menu for ${b.text}`}
              onClick={() => setBlockMenu(blockMenu === b.id ? null : b.id)}
            >
              <Menu size={14} />
            </button>
            {blockMenu === b.id && (
              <div className="aw-dropdown" role="menu">
                {[
                  "Edit",
                  "Cut",
                  "Copy",
                  "Paste",
                  "Duplicate",
                  "Move up",
                  "Move down",
                  "Negate",
                  "Delete",
                ].map((action) => (
                  <button
                    role="menuitem"
                    disabled={
                      (action === "Paste" && !clipboard) ||
                      (action === "Move up" && i === 0) ||
                      (action === "Move down" && i === blocks.length - 1)
                    }
                    key={action}
                    onClick={() => {
                      setBlockMenu(null);
                      if (action === "Edit")
                        setEditing({ ...dest, blockId: b.id });
                      if (action === "Copy" || action === "Cut")
                        setClipboard({ ...b });
                      if (action === "Delete" || action === "Cut")
                        changeBlocks(
                          dest,
                          blocks.filter((x) => x.id !== b.id),
                        );
                      if (action === "Duplicate" || action === "Paste") {
                        const copy = action === "Paste" ? clipboard : b;
                        if (copy)
                          changeBlocks(dest, [
                            ...blocks.slice(0, i + 1),
                            block(copy.text),
                            ...blocks.slice(i + 1),
                          ]);
                      }
                      if (action === "Negate")
                        changeBlocks(
                          dest,
                          blocks.map((x) =>
                            x.id === b.id
                              ? {
                                  ...x,
                                  text: x.text.startsWith("NOT (")
                                    ? x.text.slice(5, -1)
                                    : `NOT (${x.text})`,
                                }
                              : x,
                          ),
                        );
                      if (action.startsWith("Move")) {
                        const next = [...blocks];
                        const j = i + (action === "Move up" ? -1 : 1);
                        [next[i], next[j]] = [next[j], next[i]];
                        changeBlocks(dest, next);
                      }
                    }}
                  >
                    {action}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
      <div className="aw-add-block">
        <button className="aw-old" onClick={() => setEditing(dest)}>
          {dest.section === "actions" || dest.section === "otherwise"
            ? "Add action(s)"
            : "Add condition(s)"}
        </button>
      </div>
    </div>
  );
  return (
    <div className="aw-editor-main">
      {draft.mode !== "Full" ? (
        <>
          {draft.mode !== "Simple" && (
            <nav className="aw-settings-tabs aw-picker-tabs">
              {(draft.mode === "Stockpicker"
                ? ["Long", "Short", "Position score"]
                : ["Long", "Short"]
              ).map((tab) => (
                <button
                  key={tab}
                  className={pickerTab === tab ? "active" : ""}
                  onClick={() => setPickerTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </nav>
          )}
          {draft.mode !== "Simple" && pickerTab === "Position score" ? (
            <div className="aw-rule-canvas">
              <h3>Position score</h3>
              <AWField
                label="Score formula"
                value={draft.settings["Position score"]}
                onChange={(v) =>
                  onChange({
                    ...draft,
                    settings: { ...draft.settings, "Position score": v },
                  })
                }
              />
              <AWField
                label="Maximum stocks"
                type="number"
                value={draft.settings["Maximum stocks"]}
                onChange={(v) =>
                  onChange({
                    ...draft,
                    settings: { ...draft.settings, "Maximum stocks": v },
                  })
                }
              />
              <AWField
                label="Sort direction"
                value={draft.settings["Score direction"] ?? "Highest first"}
                options={["Highest first", "Lowest first"]}
                onChange={(v) =>
                  onChange({
                    ...draft,
                    settings: { ...draft.settings, "Score direction": v },
                  })
                }
              />
            </div>
          ) : (
            <div className="aw-simple-panels">
              {["Buy", "Sell short"].map((title, index) => {
                if (
                  draft.mode !== "Simple" &&
                  pickerTab !== (index ? "Short" : "Long")
                )
                  return null;
                const signalRule = draft.rules.find((r) => r.kind === "Signal");
                const signal = signalRule?.signals.find(
                  (s) =>
                    s.variable ===
                    (index ? "ShortEntrySignal" : "LongEntrySignal"),
                );
                const entryRule = draft.rules.find(
                  (r) => r.name === (index ? "Short entry" : "Long entry"),
                );
                const exitName = index ? "ShortExitSignal" : "LongExitSignal";
                const exitSignal = signalRule?.signals.find(
                  (s) => s.variable === exitName,
                );
                return (
                  <section className="aw-simple-panel" key={title}>
                    <h2 style={{ background: index ? "#dd8585" : "#8edca2" }}>
                      {draft.mode === "Simple"
                        ? title
                        : index
                          ? "Sell when"
                          : "Buy when"}
                    </h2>
                    <div className="aw-simple-content">
                      <h3>Order type</h3>
                      {entryRule && (
                        <>
                          <AWField
                            label="Order"
                            value={
                              draft.settings[`${title} order`] ??
                              "Enter at Market"
                            }
                            options={[
                              "Enter at Market",
                              "Enter at Stop",
                              "Enter at Limit",
                            ]}
                            onChange={(v) =>
                              onChange({
                                ...draft,
                                settings: {
                                  ...draft.settings,
                                  [`${title} order`]: v,
                                },
                                rules: draft.rules.map((r) =>
                                  r.id === entryRule.id
                                    ? {
                                        ...r,
                                        actions: [
                                          block(
                                            `${v} (${index ? "Short" : "Long"}, ${draft.settings["Order size"]} lots)`,
                                          ),
                                        ],
                                      }
                                    : r,
                                ),
                              })
                            }
                          />
                          {list(entryRule.actions, {
                            ruleId: entryRule.id,
                            section: "actions",
                          })}
                        </>
                      )}
                      <h3>When</h3>
                      {signal &&
                        signalRule &&
                        list(signal.conditions, {
                          ruleId: signalRule.id,
                          section: "conditions",
                          signalId: signal.id,
                        })}
                      <h3>Exit methods</h3>
                      {[
                        "Stop Loss",
                        "Profit Target",
                        "Trailing Stop",
                        "Move SL to BE",
                        "Exit After Bars",
                      ].map((label) => (
                        <AWField
                          key={label}
                          label={label}
                          value={draft.settings[`${title} ${label}`] ?? "0"}
                          onChange={(v) =>
                            onChange({
                              ...draft,
                              settings: {
                                ...draft.settings,
                                [`${title} ${label}`]: v,
                              },
                            })
                          }
                        />
                      ))}
                      <h3>{index ? "Buy to cover" : "Sell to cover"}</h3>
                      {signalRule &&
                        (exitSignal ? (
                          list(exitSignal.conditions, {
                            ruleId: signalRule.id,
                            section: "conditions",
                            signalId: exitSignal.id,
                          })
                        ) : (
                          <button
                            className="aw-old"
                            onClick={() => {
                              const id = uid();
                              setEditing({
                                ruleId: signalRule.id,
                                section: "conditions",
                                signalId: id,
                                newSignalVariable: exitName,
                              });
                            }}
                          >
                            Add exit condition(s)
                          </button>
                        ))}
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </>
      ) : (
        <>
          <p className="aw-instruction">
            Define strategy rules below. Rule is usually a relation: IF some
            condition(s) are true THEN do some action(s).
          </p>
          <div className="aw-rule-tabs" role="tablist">
            {draft.rules.map((r, index) => (
              <div
                key={r.id}
                className={`aw-rule-tab ${rule?.id === r.id ? "active" : ""}`}
                draggable
                onDragStart={() => setDragged(r.id)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (dragged)
                    reorder(
                      dragged,
                      index - draft.rules.findIndex((x) => x.id === dragged),
                    );
                  setDragged(null);
                }}
              >
                <button
                  role="tab"
                  aria-selected={rule?.id === r.id}
                  onClick={() => setSelected(r.id)}
                >
                  {r.name}
                </button>
                <div className="aw-menu-anchor">
                  <button
                    aria-label={`Rule menu ${r.name}`}
                    onClick={() => setRuleMenu(ruleMenu === r.id ? null : r.id)}
                  >
                    <Menu size={12} />
                  </button>
                  {ruleMenu === r.id && (
                    <div className="aw-dropdown" role="menu">
                      {[
                        "Rename / edit rule",
                        "Duplicate rule",
                        "Move left",
                        "Move right",
                        "Delete rule",
                      ].map((action) => (
                        <button
                          role="menuitem"
                          key={action}
                          disabled={
                            (action === "Move left" && index === 0) ||
                            (action === "Move right" &&
                              index === draft.rules.length - 1)
                          }
                          onClick={() => {
                            setRuleMenu(null);
                            if (action === "Rename / edit rule") setDialog(r);
                            if (action === "Delete rule") setDeleting(r.id);
                            if (action.startsWith("Move"))
                              reorder(r.id, action === "Move left" ? -1 : 1);
                            if (action === "Duplicate rule") {
                              const copy = {
                                ...structuredClone(r),
                                id: uid(),
                                name: `${r.name} copy`,
                                signals: r.signals.map((s) => ({
                                  ...s,
                                  id: uid(),
                                  conditions: s.conditions.map((b) =>
                                    block(b.text),
                                  ),
                                })),
                                conditions: r.conditions.map((b) =>
                                  block(b.text),
                                ),
                                actions: r.actions.map((b) => block(b.text)),
                                otherwise: r.otherwise.map((b) =>
                                  block(b.text),
                                ),
                              };
                              onChange({
                                ...draft,
                                rules: [...draft.rules, copy],
                              });
                              setSelected(copy.id);
                            }
                          }}
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <button className="aw-add-rule" onClick={() => setDialog("new")}>
              <Plus size={15} /> Add rule
            </button>
          </div>
          <div className="aw-rule-canvas">
            {rule ? (
              <>
                <button className="aw-trigger" onClick={() => setDialog(rule)}>
                  RULE IS TRIGGERED {rule.trigger.toUpperCase()}
                </button>
                {rule.kind === "Signal" ||
                rule.kind === "Fuzzy Logic Signals" ? (
                  <>
                    {rule.signals.map((signal) => (
                      <section className="aw-signal" key={signal.id}>
                        <div className="aw-section-label">
                          <span>SIGNAL</span>
                          <hr />
                          <label>
                            Save to variable{" "}
                            <select
                              value={signal.variable}
                              onChange={(e) =>
                                updateRule({
                                  ...rule,
                                  signals: rule.signals.map((s) =>
                                    s.id === signal.id
                                      ? { ...s, variable: e.target.value }
                                      : s,
                                  ),
                                })
                              }
                            >
                              {[
                                ...new Set([
                                  ...draft.variables.map((v) => v.name),
                                  signal.variable,
                                ]),
                              ].map((v) => (
                                <option key={v}>{v}</option>
                              ))}
                            </select>
                          </label>
                          <button
                            aria-label={`Remove signal ${signal.variable}`}
                            onClick={() =>
                              updateRule({
                                ...rule,
                                signals: rule.signals.filter(
                                  (s) => s.id !== signal.id,
                                ),
                              })
                            }
                          >
                            <X size={14} />
                          </button>
                        </div>
                        {list(signal.conditions, {
                          ruleId: rule.id,
                          section: "conditions",
                          signalId: signal.id,
                        })}
                      </section>
                    ))}
                    <button
                      className="aw-old"
                      onClick={() =>
                        updateRule({
                          ...rule,
                          signals: [
                            ...rule.signals,
                            {
                              id: uid(),
                              variable:
                                draft.variables[0]?.name ?? "LongEntrySignal",
                              conditions: [],
                            },
                          ],
                        })
                      }
                    >
                      Add signal
                    </button>
                  </>
                ) : (
                  <>
                    {rule.kind !== "Action only" && (
                      <section className="aw-signal">
                        <div className="aw-section-label">
                          IF
                          <hr />
                        </div>
                        {list(rule.conditions, {
                          ruleId: rule.id,
                          section: "conditions",
                        })}
                      </section>
                    )}
                    <section className="aw-signal">
                      <div className="aw-section-label">
                        THEN
                        <hr />
                      </div>
                      {list(rule.actions, {
                        ruleId: rule.id,
                        section: "actions",
                      })}
                    </section>
                    {rule.kind === "If - Then - Else" && (
                      <section className="aw-signal">
                        <div className="aw-section-label">
                          ELSE
                          <hr />
                        </div>
                        {list(rule.otherwise, {
                          ruleId: rule.id,
                          section: "otherwise",
                        })}
                      </section>
                    )}
                  </>
                )}
              </>
            ) : (
              <div className="aw-empty-rule">
                No rules defined.
                <button className="aw-old" onClick={() => setDialog("new")}>
                  Add rule
                </button>
              </div>
            )}
          </div>
        </>
      )}
      {dialog && (
        <AlgoWizardRuleDialog
          rule={dialog === "new" ? undefined : dialog}
          names={draft.rules.map((r) => r.name)}
          onClose={() => setDialog(null)}
          onSave={(r) => {
            if (dialog === "new") {
              onChange({ ...draft, rules: [...draft.rules, r] });
              setSelected(r.id);
            } else updateRule(r);
            setDialog(null);
          }}
        />
      )}
      {editing && (
        <AlgoWizardBlockEditor
          action={editing.section !== "conditions"}
          initial={
            getBlocks(editing).find((b) => b.id === editing.blockId)?.text
          }
          onClose={() => setEditing(null)}
          onSave={(text) => {
            const items = getBlocks(editing);
            changeBlocks(
              editing,
              editing.blockId
                ? items.map((b) =>
                    b.id === editing.blockId ? { ...b, text } : b,
                  )
                : [...items, block(text)],
            );
            setEditing(null);
          }}
        />
      )}
      {deleting && (
        <AWConfirm
          title="Delete rule"
          message="Delete this rule and its conditions and actions? You can undo this change."
          onClose={() => setDeleting(null)}
          onConfirm={() => {
            onChange({
              ...draft,
              rules: draft.rules.filter((r) => r.id !== deleting),
            });
            setDeleting(null);
          }}
        />
      )}
    </div>
  );
}
