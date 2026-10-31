import { useState } from "react";
import {
  DEFAULT_HSL_STRATEGY_DOCUMENT,
  DEFAULT_WIZARD_CONSTANTS_BUNDLE,
  DEFAULT_WIZARD_EXAMPLES,
  type HSLStrategyDocument,
  type RetesterHandoffResult,
  type WizardConstantsBundle,
  type WizardExampleSummary,
} from "./algoWizardModel";
import { CloudExportPanel } from "./CloudExportPanel";
import { StrategyDocumentPanel } from "./StrategyDocumentPanel";
import { StrategyNames } from "./strategy_names";
import { VisualBlockPanel } from "./VisualBlockPanel";
import { WizardCataloguePanel } from "./WizardCataloguePanel";

export interface WizardWorkspaceProps {
  initialDocument?: HSLStrategyDocument;
  existingStrategyNames?: readonly string[];
  examples?: readonly WizardExampleSummary[];
  constantsBundle?: WizardConstantsBundle;
  retesterHandoff?: RetesterHandoffResult | null;
  onLoadExample?: (exampleId: string) => void;
  onSaveToRetester?: (document: HSLStrategyDocument) => void;
  onRenameStrategy?: (sanitizedUniqueName: string) => void;
}

export function allocateSanitizedStrategyName(
  proposedName: string,
  existingNames: readonly string[],
): string {
  const sanitized = StrategyNames.sanitize(proposedName).trim();
  const baseName = sanitized.length > 0 ? sanitized : "New Strategy";
  return StrategyNames.unique(baseName, existingNames);
}

export function WizardWorkspace({
  initialDocument = DEFAULT_HSL_STRATEGY_DOCUMENT,
  existingStrategyNames = ["EMA Crossover Strategy"],
  examples = DEFAULT_WIZARD_EXAMPLES,
  constantsBundle = DEFAULT_WIZARD_CONSTANTS_BUNDLE,
  retesterHandoff = null,
  onLoadExample,
  onSaveToRetester,
  onRenameStrategy,
}: WizardWorkspaceProps) {
  const [document, setDocument] =
    useState<HSLStrategyDocument>(initialDocument);
  const [selectedExampleId, setSelectedExampleId] = useState<string>(
    examples[0]?.example_id ?? "ema_crossover",
  );
  const [proposedName, setProposedName] = useState<string>(
    initialDocument.strategy.name,
  );

  const previewAllocatedName = allocateSanitizedStrategyName(
    proposedName,
    existingStrategyNames,
  );

  function handleApplyRename() {
    const nextName = allocateSanitizedStrategyName(
      proposedName,
      existingStrategyNames,
    );
    setDocument({
      ...document,
      strategy: {
        ...document.strategy,
        name: nextName,
      },
    });
    onRenameStrategy?.(nextName);
  }

  return (
    <div
      className="wizard-hsl-workspace"
      aria-label="AlgoWizard HSL 1.0 Workspace"
    >
      <header className="wizard-workspace-toolbar">
        <h2>AlgoWizard HSL 1.0 Strategy Studio</h2>

        <div className="wizard-name-allocator">
          <label htmlFor="wizard-strategy-name-input">Strategy Name</label>
          <input
            id="wizard-strategy-name-input"
            type="text"
            value={proposedName}
            onChange={(event) => setProposedName(event.target.value)}
          />
          <span>
            Collision-Free Display Name: <code>{previewAllocatedName}</code>
          </span>
          <button type="button" onClick={handleApplyRename}>
            Apply Sanitized Unique Name
          </button>
        </div>

        <div className="wizard-example-loader">
          <label htmlFor="wizard-example-select">
            Built-in Examples (/AlgoWizard/examples/examples.json)
          </label>
          <select
            id="wizard-example-select"
            value={selectedExampleId}
            onChange={(event) => setSelectedExampleId(event.target.value)}
          >
            {examples.map((example) => (
              <option key={example.example_id} value={example.example_id}>
                {example.name} ({example.category})
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => onLoadExample?.(selectedExampleId)}
          >
            Load Example (/algowizard/loadExample)
          </button>
        </div>

        <div className="wizard-retester-handoff">
          <button
            type="button"
            onClick={() => onSaveToRetester?.(document)}
          >
            Send to Retester (/algowizard/saveToRetester)
          </button>
          {retesterHandoff && (
            <span data-retester-status={retesterHandoff.status}>
              Retester Ready: {retesterHandoff.strategy_id} (
              {retesterHandoff.compiled_rule_count} rules, hash{" "}
              {retesterHandoff.document_hash})
            </span>
          )}
        </div>
      </header>

      <div className="wizard-workspace-grid">
        <WizardCataloguePanel bundle={constantsBundle} />
        <StrategyDocumentPanel document={document} />
        <VisualBlockPanel />
        <CloudExportPanel document={document} />
      </div>
    </div>
  );
}
