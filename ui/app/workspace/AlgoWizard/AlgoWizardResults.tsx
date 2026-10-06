import { useState } from "react";
import { AWModal } from "./AlgoWizardControls";
import { downloadText, type Draft } from "./algoWizardModel";
export type RunState = "idle" | "running" | "complete" | "canceled";
export function EquityChart() {
  return (
    <svg
      className="aw-equity"
      viewBox="0 0 700 240"
      role="img"
      aria-label="Mock equity curve"
    >
      <rect width="700" height="240" fill="#181818" />
      {[40, 80, 120, 160, 200].map((y) => (
        <path key={y} d={`M35 ${y}H685`} stroke="#373737" />
      ))}
      <path
        d="M35 205L65 192L95 200L125 167L155 172L185 145L215 157L245 144L275 152L305 100L335 116L365 84L395 99L425 66L455 88L485 70L515 76L545 38L575 49L605 24L635 38L685 15"
        fill="none"
        stroke="#6795cf"
        strokeWidth="2"
      />
    </svg>
  );
}
export function AlgoWizardResults({
  draft,
  status,
  onClose,
  onRun,
}: {
  draft: Draft;
  status: RunState;
  onClose: () => void;
  onRun: () => void;
}) {
  const [tab, setTab] = useState("Overview");
  const trades = Array.from({ length: 12 }, (_, i) => ({
    id: i + 1,
    date: `2026-01-${String(i + 2).padStart(2, "0")}`,
    direction: i % 2 ? "Short" : "Long",
    lots: "0.1",
    profit: i % 3 ? 42 + i * 3 : -25 - i,
  }));
  return (
    <div className="aw-results">
      <div className="aw-resource-header">
        <button className="aw-old" onClick={onClose}>
          ‹ Back to editor
        </button>
        <h2>{draft.name}</h2>
        <button
          className="aw-run"
          disabled={status === "running"}
          onClick={onRun}
        >
          Run backtest
        </button>
      </div>
      <p className="aw-demo">
        Demonstration results — fixed fixtures, no strategy execution.
      </p>
      <nav className="aw-settings-tabs">
        {[
          "Overview",
          "Equity chart",
          "List of trades",
          "Trading analysis",
          "Settings",
        ].map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </nav>
      {status !== "complete" ? (
        <p className="aw-no-result">
          {status === "running"
            ? "Running mock backtest…"
            : status === "canceled"
              ? "Mock backtest canceled."
              : "No backtest result yet"}
        </p>
      ) : (
        <>
          {tab === "Overview" && (
            <>
              <div className="aw-metrics">
                {[
                  ["Net profit", "$362"],
                  ["Number of trades", "12"],
                  ["Profit factor", "4.07"],
                  ["Winning trades", "66.67%"],
                  ["Max drawdown", "$34"],
                  ["Return / Drawdown", "10.65"],
                ].map(([label, value]) => (
                  <div key={label}>
                    <small>{label}</small>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
              <EquityChart />
            </>
          )}
          {tab === "Equity chart" && <EquityChart />}
          {tab === "List of trades" && (
            <>
              <button
                className="aw-old"
                onClick={() =>
                  downloadText(
                    `${draft.name}-mock-trades.json`,
                    JSON.stringify(trades, null, 2),
                  )
                }
              >
                Export trades
              </button>
              <table>
                <thead>
                  <tr>
                    {["#", "Date", "Direction", "Lots", "Profit"].map((t) => (
                      <th key={t}>{t}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {trades.map((t) => (
                    <tr key={t.id}>
                      <td>{t.id}</td>
                      <td>{t.date}</td>
                      <td>{t.direction}</td>
                      <td>{t.lots}</td>
                      <td className={t.profit > 0 ? "aw-positive" : "aw-error"}>
                        {t.profit}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {tab === "Trading analysis" && (
            <>
              <h3>Long / Short analysis</h3>
              <table>
                <thead>
                  <tr>
                    <th>Direction</th>
                    <th>Trades</th>
                    <th>Net profit</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Long</td>
                    <td>6</td>
                    <td>$184</td>
                  </tr>
                  <tr>
                    <td>Short</td>
                    <td>6</td>
                    <td>$178</td>
                  </tr>
                </tbody>
              </table>
            </>
          )}
          {tab === "Settings" && (
            <table>
              <tbody>
                {Object.entries(draft.settings).map(([k, v]) => (
                  <tr key={k}>
                    <td>{k}</td>
                    <td>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
export function AlgoWizardSource({
  draft,
  onClose,
}: {
  draft: Draft;
  onClose: () => void;
}) {
  const [format, setFormat] = useState("Pseudo code");
  const [copied, setCopied] = useState("");
  const code =
    format === "Prototype JSON"
      ? JSON.stringify(draft, null, 2)
      : `// UI preview only — not executable trading code\n// ${draft.name}\n\n${draft.rules.map((r) => `RULE ${r.name} (${r.trigger})\n${r.signals.map((s) => `  ${s.variable} = ${s.conditions.map((b) => b.text).join(" AND ") || "false"}`).join("\n")}\n${r.conditions.length ? `  IF ${r.conditions.map((b) => b.text).join(" AND ")}\n` : ""}${r.actions.map((b) => `  THEN ${b.text}`).join("\n")}${r.otherwise.map((b) => `\n  ELSE ${b.text}`).join("")}`).join("\n\n")}`;
  return (
    <AWModal
      wide
      title="Source code"
      onClose={onClose}
      footer={
        <>
          <span role="status">{copied}</span>
          <button
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(code);
                setCopied("Copied");
              } catch {
                setCopied(
                  "Clipboard unavailable. Select and copy the preview.",
                );
              }
            }}
          >
            Copy
          </button>
          <button
            className="aw-primary"
            onClick={() => downloadText(`${draft.name}-preview.txt`, code)}
          >
            Download
          </button>
          <button onClick={onClose}>Close</button>
        </>
      }
    >
      <label className="aw-field">
        Format
        <select value={format} onChange={(e) => setFormat(e.target.value)}>
          <option>Pseudo code</option>
          <option>Prototype JSON</option>
        </select>
      </label>
      <p className="aw-demo">
        UI preview. Platform compilation is not connected.
      </p>
      <textarea
        className="aw-source"
        aria-label="Source preview"
        value={code}
        readOnly
      />
    </AWModal>
  );
}
