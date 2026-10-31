import { useState } from "react";
import {
  DEFAULT_WIZARD_CONSTANTS_BUNDLE,
  filterCatalogueBlocks,
  type HSLBlockCatalogueEntry,
  type HSLNodeFamily,
  type WizardConstantsBundle,
} from "./algoWizardModel";

export interface WizardCataloguePanelProps {
  bundle?: WizardConstantsBundle;
  initialFamily?: HSLNodeFamily | "ALL";
  initialQuery?: string;
  onSelectBlock?: (entry: HSLBlockCatalogueEntry) => void;
}

const NODE_FAMILIES: readonly (HSLNodeFamily | "ALL")[] = [
  "ALL",
  "VALUE",
  "EXPRESSION",
  "CONDITION",
  "ACTION",
  "RULE",
];

export function WizardCataloguePanel({
  bundle = DEFAULT_WIZARD_CONSTANTS_BUNDLE,
  initialFamily = "ALL",
  initialQuery = "",
  onSelectBlock,
}: WizardCataloguePanelProps) {
  const [selectedFamily, setSelectedFamily] = useState<HSLNodeFamily | "ALL">(
    initialFamily,
  );
  const [searchQuery, setSearchQuery] = useState<string>(initialQuery);

  const visibleBlocks = filterCatalogueBlocks(
    bundle.blocks,
    selectedFamily,
    searchQuery,
  );

  return (
    <section
      className="wizard-catalogue-panel"
      aria-label="HSL Block Catalogue and Wizard Constants"
    >
      <header className="wizard-catalogue-header">
        <h3>HSL 1.0 Block Catalogue (BlockRegistry)</h3>
        <span>Schema v{bundle.schema_version}</span>
      </header>

      <div className="wizard-catalogue-controls">
        <input
          type="search"
          aria-label="Search HSL blocks"
          placeholder="Search semantic ID, block label, or category..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
        />
        <div
          className="wizard-catalogue-families"
          role="tablist"
          aria-label="HSL AST Node Families"
        >
          {NODE_FAMILIES.map((family) => (
            <button
              key={family}
              type="button"
              role="tab"
              aria-selected={selectedFamily === family}
              onClick={() => setSelectedFamily(family)}
            >
              {family}
            </button>
          ))}
        </div>
      </div>

      <div className="wizard-catalogue-block-list">
        <h4>Blocks ({visibleBlocks.length})</h4>
        <ul>
          {visibleBlocks.map((entry) => (
            <li key={entry.semantic_id} data-semantic-id={entry.semantic_id}>
              <div>
                <strong>{entry.label}</strong>{" "}
                <code>{entry.semantic_id}</code>{" "}
                <span>[{entry.family}]</span>{" "}
                <span>({entry.category})</span>{" "}
                <span>→ {entry.return_type}</span>
              </div>
              <div>
                <small>Registry ID: {entry.registry_block_id}</small>
                {entry.allowed_children.length > 0 && (
                  <small>
                    {" "}
                    | Children: {entry.allowed_children.join(", ")}
                  </small>
                )}
              </div>
              {entry.parameters.length > 0 && (
                <ul className="wizard-block-parameters">
                  {entry.parameters.map((param) => (
                    <li key={param.key}>
                      <code>{param.key}</code> ({param.value_type}): default=
                      {String(param.default_value)}
                      {param.min_value !== undefined &&
                        param.min_value !== null &&
                        `, min=${param.min_value}`}
                      {param.max_value !== undefined &&
                        param.max_value !== null &&
                        `, max=${param.max_value}`}
                    </li>
                  ))}
                </ul>
              )}
              {onSelectBlock && (
                <button
                  type="button"
                  onClick={() => onSelectBlock(entry)}
                >
                  Insert {entry.semantic_id}
                </button>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div className="wizard-constants-summary">
        <div className="wizard-constants-group">
          <h4>Timeframes</h4>
          <ul>
            {bundle.timeframes.map((tf) => (
              <li key={tf.key}>
                <code>{tf.key}</code> — {tf.label}
              </li>
            ))}
          </ul>
        </div>

        <div className="wizard-constants-group">
          <h4>Backtest Precisions</h4>
          <ul>
            {bundle.precisions.map((precision) => (
              <li key={precision.key}>
                <code>{precision.key}</code> — {precision.label}
              </li>
            ))}
          </ul>
        </div>

        <div className="wizard-constants-group">
          <h4>Commission Methods</h4>
          <ul>
            {bundle.commission_methods.map((method) => (
              <li key={method.method_id}>
                <code>{method.method_id}</code> — {method.label} (
                {method.default_value} {method.unit})
              </li>
            ))}
          </ul>
        </div>

        <div className="wizard-constants-group">
          <h4>Lifecycle Events</h4>
          <ul>
            {bundle.lifecycle_events.map((evt) => (
              <li key={evt.key}>
                <code>{evt.key}</code> — {evt.label}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
