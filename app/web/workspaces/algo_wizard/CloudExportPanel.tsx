import { useState } from "react";
import {
  DEFAULT_EXPORT_TARGETS,
  DEFAULT_HSL_STRATEGY_DOCUMENT,
  type CloudImportSource,
  type ExportStrategyResult,
  type ExportTargetDescriptor,
  type ExportTargetPlatform,
  type HSLStrategyDocument,
} from "./algoWizardModel";

export interface CloudExportPanelProps {
  document?: HSLStrategyDocument;
  targets?: readonly ExportTargetDescriptor[];
  initialImportSource?: CloudImportSource;
  initialPlatform?: ExportTargetPlatform;
  exportPreview?: ExportStrategyResult;
  onImportStrategy?: (source: CloudImportSource) => void;
  onExportStrategy?: (platform: ExportTargetPlatform) => void;
  onCopyCode?: (content: string) => void;
  onDownloadCode?: (filename: string, content: string) => void;
}

const IMPORT_SOURCES: readonly {
  source: CloudImportSource;
  label: string;
}[] = [
  { source: "editor", label: "Active HSL Editor" },
  { source: "file", label: "Workspace Strategy File" },
  { source: "databank", label: "Strategy Databank" },
  { source: "backtest_id", label: "Wizard Backtest Run ID" },
];

const DEFAULT_EXPORT_PREVIEW: ExportStrategyResult = {
  strategy_id: DEFAULT_HSL_STRATEGY_DOCUMENT.strategy.id,
  target_platform: "python",
  filename: "hsl_ema_crossover_v1.py",
  content:
    "# Generated from Canonical HSL 1.0 Strategy AST\nclass EMACrossoverStrategy:\n    pass\n",
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
};

export function CloudExportPanel({
  document = DEFAULT_HSL_STRATEGY_DOCUMENT,
  targets = DEFAULT_EXPORT_TARGETS,
  initialImportSource = "editor",
  initialPlatform = "python",
  exportPreview = DEFAULT_EXPORT_PREVIEW,
  onImportStrategy,
  onExportStrategy,
  onCopyCode,
  onDownloadCode,
}: CloudExportPanelProps) {
  const [importSource, setImportSource] =
    useState<CloudImportSource>(initialImportSource);
  const [targetPlatform, setTargetPlatform] =
    useState<ExportTargetPlatform>(initialPlatform);

  return (
    <section
      className="cloud-export-panel"
      aria-label="AlgoCloud Import and Multi-Target Strategy Export"
    >
      <header className="cloud-export-header">
        <h3>Cloud Strategy Import &amp; Multi-Target Code Export</h3>
        <span>Strategy: {document.strategy.name}</span>
      </header>

      <div className="cloud-import-picker">
        <h4>Import Source (/algocloud/import)</h4>
        <div role="radiogroup" aria-label="Cloud Import Source">
          {IMPORT_SOURCES.map((item) => (
            <label key={item.source}>
              <input
                type="radio"
                name="cloud-import-source"
                value={item.source}
                checked={importSource === item.source}
                onChange={() => setImportSource(item.source)}
              />
              {item.label} (<code>{item.source}</code>)
            </label>
          ))}
        </div>
        <button
          type="button"
          onClick={() => onImportStrategy?.(importSource)}
        >
          Import Strategy from {importSource}
        </button>
      </div>

      <div className="cloud-export-targets">
        <h4>Target Export Platforms (/algocloud/export)</h4>
        <ul>
          {targets.map((target) => (
            <li key={target.platform} data-export-platform={target.platform}>
              <label>
                <input
                  type="radio"
                  name="cloud-export-platform"
                  value={target.platform}
                  checked={targetPlatform === target.platform}
                  onChange={() => setTargetPlatform(target.platform)}
                />
                <strong>{target.label}</strong>{" "}
                <code>({target.platform})</code> —{" "}
                <code>{target.extension}</code>: {target.description}
              </label>
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => onExportStrategy?.(targetPlatform)}
        >
          Generate {targetPlatform} Export
        </button>
      </div>

      <div className="cloud-export-preview">
        <h4>
          Generated Code Preview: <code>{exportPreview.filename}</code> (
          {exportPreview.target_platform})
        </h4>
        <div>
          <small>SHA-256: {exportPreview.sha256}</small>
        </div>
        <pre>
          <code>{exportPreview.content}</code>
        </pre>
        <div className="cloud-export-actions">
          <button
            type="button"
            onClick={() => onCopyCode?.(exportPreview.content)}
          >
            Copy Code
          </button>
          <button
            type="button"
            onClick={() =>
              onDownloadCode?.(exportPreview.filename, exportPreview.content)
            }
          >
            Download {exportPreview.filename}
          </button>
        </div>
      </div>
    </section>
  );
}
