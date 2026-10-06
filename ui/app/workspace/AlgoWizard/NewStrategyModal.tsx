import { useState } from "react";
import { AWModal, AWField } from "./AlgoWizardControls";
import type { EditorMode } from "./algoWizardModel";
export function NewStrategyModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (name: string, mode: EditorMode, template: boolean) => void;
}) {
  const [name, setName] = useState("New strategy");
  const [mode, setMode] = useState<EditorMode>("Simple");
  const [template, setTemplate] = useState(false);
  const radio = (value: EditorMode, title: string, description: string) => (
    <div className="aw-radio-option">
      <label>
        <input
          type="radio"
          name="editorMode"
          checked={mode === value}
          onChange={() => setMode(value)}
        />
        <b>{title}</b>
      </label>
      <p>{description}</p>
    </div>
  );
  return (
    <AWModal
      title="New strategy"
      onClose={onClose}
      footer={
        <>
          <button onClick={onClose}>Close</button>
          <button
            className="aw-primary"
            disabled={!name.trim()}
            onClick={() => onCreate(name.trim(), mode, template)}
          >
            Select
          </button>
        </>
      }
    >
      <AWField label="Strategy name:" value={name} onChange={setName} />
      <b>Choose strategy type:</b>
      <div className="aw-radio-option">
        <label>
          <input
            type="radio"
            name="asset"
            checked={mode === "Simple" || mode === "Full"}
            onChange={() => setMode("Simple")}
          />
          <b>
            Single-asset strategy (MetaTrader 4/5, Tradestation, MultiCharts,
            JForex)
          </b>
        </label>
        <p>
          This is a standard algo strategy that trades on one chart (with
          possibility of subcharts)
        </p>
      </div>
      <div className="aw-editor-choice">
        Choose editor type:
        {radio("Simple", "Simple Editor", "Simplified editor for easy start")}
        {radio(
          "Full",
          "Full Editor",
          "Full editor allowing creation of complex rules",
        )}
        <label className="aw-template-switch">
          <input
            type="checkbox"
            role="switch"
            checked={template}
            onChange={(e) => {
              setTemplate(e.target.checked);
              setMode("Full");
            }}
          />
          Create basic strategy template
        </label>
      </div>
      {radio(
        "Stockpicker",
        "Stockpicker strategy (cloud)",
        "Stockpicker strategy trades on all symbols in a group of stocks and picks the top symbols according to the defined position score",
      )}
      {radio(
        "Single-asset cloud",
        "Single-asset cloud strategy (cloud)",
        "Same cloud algo strategy as Stockpicker, but trades on a single asset / stock",
      )}
    </AWModal>
  );
}
