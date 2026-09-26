import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { AlgoWizardToolbar } from "./AlgoWizardToolbar";
import { AlgoWizardHome } from "./AlgoWizardHome";
import { NewStrategyModal } from "./NewStrategyModal";
import { AlgoWizardEditor } from "./AlgoWizardEditor";
import { AlgoWizardSettings } from "./AlgoWizardSettings";
import { AlgoWizardResources, type Resource } from "./AlgoWizardResources";
import {
  AlgoWizardResults,
  AlgoWizardSource,
  EquityChart,
  type RunState,
} from "./AlgoWizardResults";
import { AlgoWizardAI } from "./AlgoWizardAI";
import { AWModal, AWField } from "./AlgoWizardControls";
import { exampleDraft, examples } from "./algoWizardFixtures";
import {
  canSimplify,
  decodeDraft,
  dirty,
  downloadText,
  encodeDraft,
  makeDraft,
  revise,
  startHistory,
  travel,
  uid,
  uniqueName,
  type Draft,
  type History,
} from "./algoWizardModel";
import "./AlgoWizard.css";

export function AlgoWizardWorkspace() {
  const [histories, setHistories] = useState<History[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [view, setView] = useState("editor");
  const [modal, setModal] = useState<string | null>(null);
  const [settings, setSettings] = useState<string | null>(null);
  const [recent, setRecent] = useState<Draft[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [ai, setAI] = useState(false);
  const [runs, setRuns] = useState<Record<string, RunState>>({});
  const [results, setResults] = useState<Record<string, Draft>>({});
  const [closeId, setCloseId] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");
  const [staged, setStaged] = useState<string[]>([]);
  const file = useRef<HTMLInputElement>(null);
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const history = histories.find((h) => h.present.id === selected);
  const draft = history?.present;
  const status = draft ? (runs[draft.id] ?? "idle") : "idle";
  const update = (next: Draft) =>
    setHistories((items) =>
      items.map((h) => (h.present.id === next.id ? revise(h, next) : h)),
    );
  const undoRedo = (direction: "undo" | "redo") =>
    setHistories((items) =>
      items.map((h) => (h.present.id === selected ? travel(h, direction) : h)),
    );
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.closest(
          "input,textarea,select,[contenteditable=true],[role=dialog]",
        )
      )
        return;
      if (
        (e.ctrlKey || e.metaKey) &&
        ["z", "y"].includes(e.key.toLowerCase())
      ) {
        e.preventDefault();
        setHistories((items) =>
          items.map((h) =>
            h.present.id === selected
              ? travel(
                  h,
                  e.key.toLowerCase() === "y" || e.shiftKey ? "redo" : "undo",
                )
              : h,
          ),
        );
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [selected]);
  useEffect(
    () => () => {
      Object.values(timers.current).forEach(clearTimeout);
    },
    [],
  );
  const open = (d: Draft) => {
    const next = {
      ...d,
      id: uid(),
      name: uniqueName(
        d.name,
        histories.map((h) => h.present.name),
      ),
    };
    setHistories((items) => [...items, startHistory(next)]);
    setSelected(next.id);
    setView("editor");
    setModal(null);
    setError("");
  };
  const remember = (d: Draft) =>
    setRecent((items) =>
      [structuredClone(d), ...items.filter((x) => x.name !== d.name)].slice(
        0,
        10,
      ),
    );
  const save = (d: Draft, name = d.name) => {
    downloadText(
      `${name.replace(/[^a-zA-Z0-9_. -]/g, "_")}.aw.json`,
      encodeDraft(d),
    );
    remember(d);
    setHistories((items) =>
      items.map((h) =>
        h.present.id === d.id ? { ...h, saved: JSON.stringify(d) } : h,
      ),
    );
  };
  const close = (id: string) => {
    clearTimeout(timers.current[id]);
    delete timers.current[id];
    const remaining = histories.filter((h) => h.present.id !== id);
    setHistories(remaining);
    if (selected === id) setSelected(remaining.at(-1)?.present.id ?? null);
    setCloseId(null);
    setView("editor");
  };
  const run = (d: Draft) => {
    clearTimeout(timers.current[d.id]);
    setResults((r) => ({ ...r, [d.id]: structuredClone(d) }));
    setRuns((r) => ({ ...r, [d.id]: "running" }));
    timers.current[d.id] = setTimeout(() => {
      setRuns((r) => ({ ...r, [d.id]: "complete" }));
      delete timers.current[d.id];
    }, 1100);
  };
  const stage = (d: Draft) => {
    setStaged((items) => [...new Set([...items, d.name])]);
    setHistories((items) =>
      items.map((h) =>
        h.present.id === d.id
          ? { ...h, saved: JSON.stringify(d), origin: "retester" }
          : h,
      ),
    );
  };
  const action = (a: string) => {
    if (a === "new") setModal("new");
    else if (a === "load") file.current?.click();
    else if (a === "undo" || a === "redo") undoRedo(a);
    else if (a === "examples") setModal("examples");
    else if (a === "ai") setAI(!ai);
    else if (a === "results") setView("results");
    else if (a === "save" && draft) save(draft);
    else if (a === "save-as" && draft) {
      setFileName(draft.name);
      setModal("save-as");
    } else if (a === "save-changes" && draft) {
      stage(draft);
      setModal("staged");
    } else setModal(a);
  };
  return (
    <section className="aw-workspace" aria-label="AlgoWizard workspace">
      <AlgoWizardToolbar
        active={!!draft}
        canUndo={!!history?.past.length}
        canRedo={!!history?.future.length}
        saveChanges={
          !!history && history.origin === "retester" && dirty(history)
        }
        recent={recent}
        onAction={action}
        onRecent={open}
      />
      <input
        ref={file}
        hidden
        type="file"
        accept=".json"
        onChange={async (e) => {
          const f = e.target.files?.[0];
          e.target.value = "";
          if (!f) return;
          if (f.size > 2_000_000) {
            setError("Strategy file exceeds the 2 MB prototype limit.");
            return;
          }
          try {
            const d = decodeDraft(await f.text());
            remember(d);
            open(d);
          } catch (err) {
            setError(
              err instanceof Error
                ? err.message
                : "Could not read strategy file.",
            );
          }
        }}
      />
      {error && (
        <div className="aw-error-bar" role="alert">
          {error}
          <button aria-label="Dismiss error" onClick={() => setError("")}>
            ×
          </button>
        </div>
      )}
      <div className="aw-workspace-body">
        <div className="aw-primary-area">
          {["Random groups", "Custom blocks"].includes(view) ? (
            <AlgoWizardResources
              kind={view}
              resources={resources}
              onChange={setResources}
              onClose={() => setView("editor")}
              onKind={setView}
            />
          ) : view === "results" && draft ? (
            <AlgoWizardResults
              draft={results[draft.id] ?? draft}
              status={status}
              onClose={() => setView("editor")}
              onRun={() => run(draft)}
            />
          ) : !draft ? (
            <AlgoWizardHome
              onNew={() => setModal("new")}
              onLoad={() => file.current?.click()}
              onResource={setView}
              onExample={(i) => open(exampleDraft(i))}
            />
          ) : (
            <div className="aw-loaded">
              <aside className="aw-strategies">
                <div className="aw-strategy-list">
                  {histories.map((h) => (
                    <div
                      key={h.present.id}
                      className={`aw-strategy-item ${h.present.id === selected ? "active" : ""}`}
                    >
                      <button onClick={() => setSelected(h.present.id)}>
                        {h.present.name}
                        {dirty(h) ? " *" : ""}
                      </button>
                      <button
                        aria-label={`Close strategy ${h.present.name}`}
                        onClick={() =>
                          dirty(h)
                            ? setCloseId(h.present.id)
                            : close(h.present.id)
                        }
                      >
                        <X size={15} />
                      </button>
                    </div>
                  ))}
                </div>
                <div className="aw-side-resources">
                  <button onClick={() => setView("Random groups")}>
                    Random groups
                  </button>
                  <button onClick={() => setView("Custom blocks")}>
                    Custom blocks
                  </button>
                </div>
              </aside>
              <div className="aw-working">
                <div className="aw-strategy-bar">
                  <button
                    className="aw-strategy-title"
                    title="Rename strategy"
                    onClick={() => {
                      setFileName(draft.name);
                      setModal("rename");
                    }}
                  >
                    {draft.name}
                  </button>
                  <button
                    className="aw-run"
                    onClick={() => {
                      if (status === "running") {
                        clearTimeout(timers.current[draft.id]);
                        delete timers.current[draft.id];
                        setRuns((r) => ({ ...r, [draft.id]: "canceled" }));
                      } else run(draft);
                    }}
                  >
                    {status === "running" ? "Stop backtest" : "Run backtest"}
                  </button>
                  <button
                    className="aw-old"
                    onClick={() => setSettings("Data")}
                  >
                    Settings
                  </button>
                </div>
                <div className="aw-editor-columns">
                  <AlgoWizardEditor
                    key={draft.id}
                    draft={draft}
                    onChange={update}
                  />
                  <aside className="aw-right-panel">
                    <div className="aw-summary">
                      <div>
                        <span>Money management</span>
                        <button onClick={() => setSettings("Money management")}>
                          {draft.settings["Money management"]},{" "}
                          {draft.settings["Order size"]} lots
                        </button>
                      </div>
                      <div>
                        <span>Strategy charts</span>
                        <button onClick={() => setSettings("Strategy charts")}>
                          {draft.charts.length === 1
                            ? "Single chart strategy"
                            : `${draft.charts.length} charts`}
                        </button>
                      </div>
                      <div>
                        <span>Trading options</span>
                        <button onClick={() => setSettings("Trading options")}>
                          Configure...
                        </button>
                      </div>
                      <div>
                        <span>Variables</span>
                        <button onClick={() => setSettings("Variables")}>
                          {draft.variables.length} /{" "}
                          {draft.variables.filter((v) => v.configurable).length}{" "}
                          configurable
                        </button>
                      </div>
                      <div>
                        <span>Explore (debug values)</span>
                        <button
                          onClick={() => setSettings("Explore (debug values)")}
                        >
                          {draft.debug
                            ? "On, fixture values"
                            : "Off, no values"}
                        </button>
                      </div>
                      <div>
                        <span>Editor</span>
                        <div className="aw-mode-buttons">
                          {(["Full", "Simple"] as const).map((mode) => (
                            <button
                              className={draft.mode === mode ? "active" : ""}
                              key={mode}
                              onClick={() => {
                                if (mode === "Simple" && !canSimplify(draft))
                                  setModal("incompatible");
                                else
                                  update({
                                    ...draft,
                                    mode,
                                    rules: draft.rules.length
                                      ? draft.rules
                                      : makeDraft(draft.name, mode, true).rules,
                                  });
                              }}
                            >
                              {mode}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                    <p className="aw-preview-title">Backtest result preview</p>
                    <div className="aw-preview">
                      <div className="aw-preview-info">
                        Data: {draft.settings.Symbol} /{" "}
                        {draft.settings.Timeframe},{" "}
                        {draft.settings["Start date"].replaceAll("-", ".")} -{" "}
                        {draft.settings["End date"].replaceAll("-", ".")}
                        <br />
                        Engine: {draft.settings.Engine}
                        <br />
                        Precision: {draft.settings.Precision}
                      </div>
                      {status === "complete" ? (
                        <>
                          <p className="aw-demo">Mock results · fixture data</p>
                          <EquityChart />
                          <button
                            className="aw-link"
                            onClick={() => setView("results")}
                          >
                            Open backtest results
                          </button>
                        </>
                      ) : (
                        <p className="aw-no-result">
                          {status === "running"
                            ? "Running mock backtest…"
                            : status === "canceled"
                              ? "Mock backtest canceled"
                              : "No backtest result yet"}
                        </p>
                      )}
                    </div>
                  </aside>
                </div>
              </div>
            </div>
          )}
        </div>
        {ai && (
          <AlgoWizardAI
            onClose={() => setAI(false)}
            onCreate={() => open(exampleDraft(0))}
          />
        )}
      </div>
      {modal === "new" && (
        <NewStrategyModal
          onClose={() => setModal(null)}
          onCreate={(name, mode, template) =>
            open(makeDraft(name, mode, template))
          }
        />
      )}
      {modal === "examples" && (
        <AWModal wide title="Examples" onClose={() => setModal(null)}>
          <div className="aw-example-picker">
            {examples.map((e, i) => (
              <button key={e.name} onClick={() => open(exampleDraft(i))}>
                <strong>{e.name}</strong>
                <span>{e.description}</span>
              </button>
            ))}
          </div>
        </AWModal>
      )}
      {modal === "source" && draft && (
        <AlgoWizardSource draft={draft} onClose={() => setModal(null)} />
      )}
      {settings && draft && (
        <AlgoWizardSettings
          draft={draft}
          initial={settings}
          onSave={update}
          onRun={run}
          onClose={() => setSettings(null)}
        />
      )}
      {(modal === "save-as" || modal === "rename") && draft && (
        <AWModal
          title={modal === "rename" ? "Rename strategy" : "Save to file as..."}
          onClose={() => setModal(null)}
          footer={
            <>
              <button onClick={() => setModal(null)}>Cancel</button>
              <button
                className="aw-primary"
                disabled={
                  !fileName.trim() ||
                  (modal === "rename" &&
                    histories.some(
                      (h) =>
                        h.present.id !== draft.id &&
                        h.present.name === fileName.trim(),
                    ))
                }
                onClick={() => {
                  if (modal === "rename")
                    update({ ...draft, name: fileName.trim() });
                  else save(draft, fileName.trim());
                  setModal(null);
                }}
              >
                Save
              </button>
            </>
          }
        >
          <AWField label="Name" value={fileName} onChange={setFileName} />
          {modal === "save-as" && (
            <p className="aw-demo">
              Downloads a prototype .aw.json document, not an SQX archive.
            </p>
          )}
        </AWModal>
      )}
      {modal === "retester" && draft && (
        <AWModal
          title="Save to Retester"
          onClose={() => setModal(null)}
          footer={
            <>
              <button onClick={() => setModal(null)}>Cancel</button>
              <button
                className="aw-primary"
                onClick={() => {
                  stage(draft);
                  setModal("staged");
                }}
              >
                Save
              </button>
            </>
          }
        >
          <p>
            Strategy: <b>{draft.name}</b>
          </p>
          <p className="aw-demo">
            Local demonstration: stage this draft in the session's Retester
            list. No backend or Retester workspace is modified.
          </p>
        </AWModal>
      )}
      {modal === "staged" && (
        <AWModal
          title="Retester staging · local demo"
          onClose={() => setModal(null)}
        >
          <p>Staged strategy drafts:</p>
          <ul>
            {staged.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </AWModal>
      )}
      {modal === "incompatible" && (
        <AWModal
          title="Cannot switch to Simple Editor"
          onClose={() => setModal(null)}
        >
          <p>
            This strategy contains rules that the Simple Editor cannot
            represent. Keep the Full Editor to preserve them.
          </p>
        </AWModal>
      )}
      {closeId && (
        <AWModal
          title="Save strategy?"
          onClose={() => setCloseId(null)}
          footer={
            <>
              <button onClick={() => setCloseId(null)}>Cancel</button>
              <button className="aw-primary" onClick={() => close(closeId)}>
                Don't save
              </button>
              <button
                className="aw-primary"
                onClick={() => {
                  const d = histories.find(
                    (h) => h.present.id === closeId,
                  )?.present;
                  if (d) save(d);
                  close(closeId);
                }}
              >
                Save to file
              </button>
            </>
          }
        >
          <p>Strategy was changed. Any unsaved changes will be lost.</p>
          <p>Do you want to save it?</p>
        </AWModal>
      )}
    </section>
  );
}
