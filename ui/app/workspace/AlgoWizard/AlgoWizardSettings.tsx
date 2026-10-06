import { useState } from "react";
import { AWField, AWModal } from "./AlgoWizardControls";
import type { Draft, Variable } from "./algoWizardModel";
const tabs = ["Data", "Trading options", "ATM", "Money management", "Advanced"];
export function AlgoWizardSettings({
  draft,
  initial,
  onSave,
  onClose,
  onRun,
}: {
  draft: Draft;
  initial: string;
  onSave: (d: Draft) => void;
  onClose: () => void;
  onRun: (d: Draft) => void;
}) {
  const [local, setLocal] = useState(() => structuredClone(draft));
  const [tab, setTab] = useState(initial);
  const [variable, setVariable] = useState<Variable | null>(null);
  const [originalName, setOriginalName] = useState<string | null>(null);
  const [error, setError] = useState("");
  const set = (key: string, value: string) =>
    setLocal((d) => ({ ...d, settings: { ...d.settings, [key]: value } }));
  const field = (key: string, options?: string[], type?: string) => (
    <AWField
      key={key}
      label={key}
      value={local.settings[key] ?? ""}
      options={options}
      type={type}
      onChange={(value) => set(key, value)}
    />
  );
  const check = (key: string) => (
    <label className="aw-check" key={key}>
      <input
        type="checkbox"
        checked={local.settings[key] === "true"}
        onChange={(e) => set(key, String(e.target.checked))}
      />
      {key}
    </label>
  );
  const removeATM = (index: number) =>
    setLocal((d) => {
      const settings = { ...d.settings };
      const count = Number(settings["ATM exits"]);
      for (let j = index + 1; j < count; j++) {
        settings[`Exit ${j} target`] = settings[`Exit ${j + 1} target`] ?? "";
        settings[`Exit ${j} size %`] = settings[`Exit ${j + 1} size %`] ?? "";
      }
      delete settings[`Exit ${count} target`];
      delete settings[`Exit ${count} size %`];
      settings["ATM exits"] = String(count - 1);
      return { ...d, settings };
    });
  const save = (run = false) => {
    if (
      !["Initial capital", "Order size"].every(
        (key) =>
          Number.isFinite(Number(local.settings[key])) &&
          Number(local.settings[key]) > 0,
      )
    ) {
      setError("Initial capital and order size must be greater than zero.");
      return;
    }
    if (local.settings["Start date"] > local.settings["End date"]) {
      setError("Start date must precede end date.");
      return;
    }
    const bindings = local.charts.map(
      (chart) =>
        `${local.settings[`chart-${chart}-symbol`] ?? local.settings.Symbol}/${local.settings[`chart-${chart}-timeframe`] ?? local.settings.Timeframe}`,
    );
    if (new Set(bindings).size !== bindings.length) {
      setError("All subcharts must have unique settings.");
      return;
    }
    onSave(local);
    if (run) onRun(local);
    onClose();
  };
  return (
    <AWModal
      wide
      title={
        ["Variables", "Strategy charts", "Explore (debug values)"].includes(
          initial,
        )
          ? initial
          : "Settings"
      }
      onClose={onClose}
      footer={
        <>
          <a
            href="https://help.algowizard.io/index.html"
            target="_blank"
            rel="noreferrer"
          >
            Help
          </a>
          <span className="aw-spacer" />
          <button onClick={onClose}>Cancel</button>
          <button className="aw-primary" onClick={() => save()}>
            Save
          </button>
          {tabs.includes(initial) && (
            <button className="aw-run" onClick={() => save(true)}>
              Run backtest
            </button>
          )}
        </>
      }
    >
      {tabs.includes(initial) && (
        <nav className="aw-settings-tabs">
          {tabs
            .filter(
              (t) =>
                !(
                  local.mode.includes("cloud") || local.mode === "Stockpicker"
                ) || t !== "ATM",
            )
            .map((t) => (
              <button
                className={tab === t ? "active" : ""}
                key={t}
                onClick={() => setTab(t)}
              >
                {t}
              </button>
            ))}
        </nav>
      )}
      {tab === "Data" && (
        <>
          <h3>Backtest data settings</h3>
          <div className="aw-form-grid">
            {field("Engine", [
              "MetaTrader4",
              "MetaTrader5",
              "TradeStation",
              "MultiCharts",
              "JForex",
              "Stockpicker",
            ])}
            {field("Symbol", [
              "AUDUSD_dukascopy",
              "EURUSD_dukascopy",
              "GBPUSD_dukascopy",
              "USDJPY_dukascopy",
              "SPY",
            ])}
            {field("Timeframe", [
              "M1",
              "M5",
              "M15",
              "M30",
              "H1",
              "H4",
              "D1",
              "W1",
            ])}
            {field("Precision", [
              "Selected timeframe only (fastest)",
              "1 minute data",
              "Real tick data",
            ])}
            {field("Start date", undefined, "date")}
            {field("End date", undefined, "date")}
            {field("Spread", undefined, "number")}
            {field("Slippage", undefined, "number")}
            {field("Commission", undefined, "number")}
          </div>
          <button className="aw-old" onClick={() => setTab("Strategy charts")}>
            Configure multiple charts
          </button>
          <p className="aw-muted">
            Local fixture symbols. Backtests use demonstration results.
          </p>
        </>
      )}
      {tab === "Trading options" && (
        <>
          <h3>Trading options</h3>
          <div className="aw-form-grid">
            {field("Trading direction", ["Both", "Long only", "Short only"])}
            {field("Maximum positions", undefined, "number")}
            {field("Maximum trades per day", undefined, "number")}
            {field("Minimum distance", undefined, "number")}
          </div>
          {[
            "Exit at end of day",
            "Exit on Friday",
            "Limit trading time",
            "Do not trade on weekends",
            "Close positions at end of range",
            "Use pending orders",
          ].map(check)}
          <div className="aw-form-grid">
            {field("Trading time from", undefined, "time")}
            {field("Trading time to", undefined, "time")}
            {field("Friday exit time", undefined, "time")}
          </div>
        </>
      )}
      {tab === "ATM" && (
        <>
          <h3>Advanced trade management</h3>
          {check("Use ATM")}
          <p>Configure additional exits for this strategy.</p>
          <div className="aw-form-grid">
            {field("ATM method", [
              "Fixed profit",
              "ATR-based",
              "Trailing stop",
              "Move SL to BE",
            ])}
            {field("Profit target", undefined, "number")}
            {field("Close percent", undefined, "number")}
            {field("Trailing activation", undefined, "number")}
            {field("Trailing distance", undefined, "number")}
          </div>
          <button
            className="aw-old"
            onClick={() =>
              set(
                "ATM exits",
                String(Number(local.settings["ATM exits"] ?? 0) + 1),
              )
            }
          >
            Add exit
          </button>
          {Array.from(
            { length: Number(local.settings["ATM exits"] ?? 0) },
            (_, i) => (
              <div className="aw-inline-fields" key={i}>
                {field(`Exit ${i + 1} target`, undefined, "number")}
                {field(`Exit ${i + 1} size %`, undefined, "number")}
                <button onClick={() => removeATM(i)}>Remove</button>
              </div>
            ),
          )}
        </>
      )}
      {tab === "Money management" && (
        <>
          <h3>Money management</h3>
          {field("Initial capital", undefined, "number")}
          {field("Money management", [
            "Fixed size",
            "Fixed amount",
            "Risk fixed % of balance",
            "Risk fixed % of equity",
            "Stocks fixed size",
          ])}
          {field("Order size", undefined, "number")}
          {local.settings["Money management"] !== "Fixed size" &&
            field("Risk / Amount", undefined, "number")}
          {field("Maximum lots", undefined, "number")}
        </>
      )}
      {tab === "Advanced" && (
        <>
          <h3>Advanced settings</h3>
          {field("Template mode", ["Off", "On"])}
          {check("Use opposite blocks for Short")}
          {check("Allow duplicate trades")}
          {field("Magic number", undefined, "number")}
          <label className="aw-expression">
            Strategy description
            <textarea
              value={local.settings.Description ?? ""}
              onChange={(e) => set("Description", e.target.value)}
            />
          </label>
        </>
      )}
      {tab === "Strategy charts" && (
        <>
          <h3>Configure multiple charts</h3>
          <table>
            <thead>
              <tr>
                <th>Chart</th>
                <th>Symbol</th>
                <th>Timeframe</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {local.charts.map((chart, i) => (
                <tr key={chart}>
                  <td>{chart}</td>
                  <td>
                    <input
                      aria-label={`Symbol for ${chart}`}
                      value={
                        local.settings[`chart-${chart}-symbol`] ??
                        local.settings.Symbol
                      }
                      onChange={(e) =>
                        set(`chart-${chart}-symbol`, e.target.value)
                      }
                    />
                  </td>
                  <td>
                    <select
                      aria-label={`Timeframe for ${chart}`}
                      value={
                        local.settings[`chart-${chart}-timeframe`] ??
                        local.settings.Timeframe
                      }
                      onChange={(e) =>
                        set(`chart-${chart}-timeframe`, e.target.value)
                      }
                    >
                      {["M1", "M5", "M15", "H1", "H4", "D1"].map((x) => (
                        <option key={x}>{x}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <button
                      disabled={i === 0}
                      onClick={() =>
                        setLocal((d) => ({
                          ...d,
                          charts: d.charts.filter((x) => x !== chart),
                        }))
                      }
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            className="aw-old"
            onClick={() =>
              setLocal((d) => ({
                ...d,
                charts: [
                  ...d.charts,
                  `Subchart ${Math.max(0, ...d.charts.map((c) => Number(c.split(" ")[1]) || 0)) + 1}`,
                ],
              }))
            }
          >
            Add chart
          </button>
          {tabs.includes(initial) && (
            <button onClick={() => setTab("Data")}>Back to Data</button>
          )}
        </>
      )}
      {tab === "Variables" && (
        <>
          <div className="aw-inline-fields">
            <button
              className="aw-old"
              onClick={() => {
                setOriginalName(null);
                setVariable({
                  name: "",
                  type: "Double",
                  value: "0",
                  configurable: false,
                });
              }}
            >
              Add variable
            </button>
            <span>{local.variables.length} variables</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Value</th>
                <th>Configurable</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {local.variables.map((v) => (
                <tr key={v.name}>
                  <td>
                    <button
                      className="aw-link"
                      onClick={() => {
                        setOriginalName(v.name);
                        setVariable({ ...v });
                      }}
                    >
                      {v.name}
                    </button>
                  </td>
                  <td>{v.type}</td>
                  <td>{v.value}</td>
                  <td>
                    <input
                      type="checkbox"
                      aria-label={`Configurable ${v.name}`}
                      checked={v.configurable}
                      onChange={(e) =>
                        setLocal((d) => ({
                          ...d,
                          variables: d.variables.map((x) =>
                            x.name === v.name
                              ? { ...x, configurable: e.target.checked }
                              : x,
                          ),
                        }))
                      }
                    />
                  </td>
                  <td>
                    <button
                      onClick={() => {
                        const used = local.rules.some(
                          (r) =>
                            r.signals.some((s) => s.variable === v.name) ||
                            JSON.stringify(r).includes(v.name),
                        );
                        if (used) {
                          setError(
                            "This variable is referenced by a rule. Remove its references first.",
                          );
                          return;
                        }
                        setLocal((d) => ({
                          ...d,
                          variables: d.variables.filter(
                            (x) => x.name !== v.name,
                          ),
                        }));
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      {tab === "Explore (debug values)" && (
        <>
          <h3>Explore strategy values</h3>
          <label className="aw-check">
            <input
              type="checkbox"
              checked={local.debug}
              onChange={(e) =>
                setLocal((d) => ({ ...d, debug: e.target.checked }))
              }
            />
            Enable debug values
          </label>
          {field("Debug bars", undefined, "number")}
          <p className="aw-muted">
            Values will be fixture examples; no indicator calculation is
            performed.
          </p>
          {local.debug && (
            <table>
              <tbody>
                {local.variables.map((v) => (
                  <tr key={v.name}>
                    <td>{v.name}</td>
                    <td>{v.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
      {error && (
        <p role="alert" className="aw-error">
          {error}
        </p>
      )}
      {variable && (
        <AWModal
          title={originalName ? "Edit variable" : "New variable"}
          onClose={() => setVariable(null)}
          footer={
            <>
              <button onClick={() => setVariable(null)}>Cancel</button>
              <button
                className="aw-primary"
                disabled={
                  !/^[A-Za-z_][A-Za-z0-9_]*$/.test(variable.name) ||
                  local.variables.some(
                    (v) => v.name === variable.name && v.name !== originalName,
                  )
                }
                onClick={() => {
                  let rules = local.rules;
                  if (originalName && variable.name !== originalName) {
                    const pattern = new RegExp(`\\b${originalName}\\b`, "g");
                    rules = local.rules.map((r) => ({
                      ...r,
                      signals: r.signals.map((s) => ({
                        ...s,
                        variable:
                          s.variable === originalName
                            ? variable.name
                            : s.variable,
                        conditions: s.conditions.map((b) => ({
                          ...b,
                          text: b.text.replace(pattern, variable.name),
                        })),
                      })),
                      conditions: r.conditions.map((b) => ({
                        ...b,
                        text: b.text.replace(pattern, variable.name),
                      })),
                      actions: r.actions.map((b) => ({
                        ...b,
                        text: b.text.replace(pattern, variable.name),
                      })),
                      otherwise: r.otherwise.map((b) => ({
                        ...b,
                        text: b.text.replace(pattern, variable.name),
                      })),
                    }));
                  }
                  setLocal((d) => ({
                    ...d,
                    rules,
                    variables: originalName
                      ? d.variables.map((v) =>
                          v.name === originalName ? variable : v,
                        )
                      : [...d.variables, variable],
                  }));
                  setVariable(null);
                }}
              >
                Save variable
              </button>
            </>
          }
        >
          <AWField
            label="Variable name"
            value={variable.name}
            onChange={(name) => setVariable({ ...variable, name })}
          />
          <AWField
            label="Variable type"
            value={variable.type}
            options={["Boolean", "Integer", "Double", "String"]}
            onChange={(type) => setVariable({ ...variable, type })}
          />
          <AWField
            label="Default value"
            value={variable.value}
            onChange={(value) => setVariable({ ...variable, value })}
          />
        </AWModal>
      )}
    </AWModal>
  );
}
