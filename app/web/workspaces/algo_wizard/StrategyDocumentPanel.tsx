import {
  DEFAULT_HSL_STRATEGY_DOCUMENT,
  sortRulesByPriority,
  type HSLParameterSpec,
  type HSLStrategyDocument,
  type HSLVariableSpec,
  type StrategyRuntimeStatus,
  type ValidationReport,
} from "./algoWizardModel";

export interface StrategyDocumentPanelProps {
  document?: HSLStrategyDocument;
  status?: StrategyRuntimeStatus;
  revision?: number;
  validation?: ValidationReport;
  onStartStrategy?: (strategyId: string) => void;
  onStopStrategy?: (strategyId: string) => void;
  onRemoveStrategy?: (strategyId: string) => void;
  onUpdateParameter?: (key: string, spec: HSLParameterSpec) => void;
  onUpdateVariable?: (key: string, spec: HSLVariableSpec) => void;
}

const DEFAULT_VALIDATION_REPORT: ValidationReport = {
  valid: true,
  issues: [],
};

export function StrategyDocumentPanel({
  document = DEFAULT_HSL_STRATEGY_DOCUMENT,
  status = "IDLE",
  revision = 1,
  validation = DEFAULT_VALIDATION_REPORT,
  onStartStrategy,
  onStopStrategy,
  onRemoveStrategy,
}: StrategyDocumentPanelProps) {
  const { strategy } = document;
  const parameterEntries = Object.entries(strategy.parameters);
  const variableEntries = Object.entries(strategy.variables);
  const orderedRules = sortRulesByPriority(strategy.rules);

  return (
    <section
      className="strategy-document-panel"
      aria-label="HSL Strategy Document and Lifecycle"
    >
      <header className="strategy-document-header">
        <div>
          <h3>{strategy.name}</h3>
          <code>ID: {strategy.id}</code> | <span>Revision: r{revision}</span> |{" "}
          <span>Status: {status}</span>
        </div>
        <div className="strategy-lifecycle-controls">
          <button
            type="button"
            disabled={!validation.valid || status === "RUNNING"}
            onClick={() => onStartStrategy?.(strategy.id)}
          >
            Start Strategy
          </button>
          <button
            type="button"
            disabled={status !== "RUNNING"}
            onClick={() => onStopStrategy?.(strategy.id)}
          >
            Stop Strategy
          </button>
          <button type="button" onClick={() => onRemoveStrategy?.(strategy.id)}>
            Remove Strategy
          </button>
        </div>
      </header>

      <div
        className="strategy-validation-banner"
        data-valid={validation.valid ? "true" : "false"}
      >
        <strong>
          Validation Status: {validation.valid ? "VALID" : "INVALID"}
        </strong>
        {validation.issues.length > 0 && (
          <ul className="strategy-validation-issues">
            {validation.issues.map((issue, idx) => (
              <li key={`${issue.code}-${idx}`}>
                <code>{issue.code}</code> at <code>{issue.path}</code>:{" "}
                {issue.message}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="strategy-parameters-section">
        <h4>Parameters (Externally Configurable &amp; Optimizable)</h4>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Default</th>
              <th>Bounds</th>
              <th>Optimize</th>
            </tr>
          </thead>
          <tbody>
            {parameterEntries.map(([key, spec]) => (
              <tr key={key} data-parameter-key={key}>
                <td>
                  <code>{key}</code>
                </td>
                <td>{spec.type}</td>
                <td>{String(spec.default)}</td>
                <td>
                  {spec.min !== undefined && spec.max !== undefined
                    ? `[${spec.min}, ${spec.max}] (step ${spec.step ?? 1})`
                    : "Unbounded"}
                </td>
                <td>{spec.optimize ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="strategy-variables-section">
        <h4>Variables (Mutable Runtime State)</h4>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Initial Value</th>
              <th>Scope</th>
            </tr>
          </thead>
          <tbody>
            {variableEntries.map(([key, spec]) => (
              <tr key={key} data-variable-key={key}>
                <td>
                  <code>{key}</code>
                </td>
                <td>{spec.type}</td>
                <td>{String(spec.initial)}</td>
                <td>{spec.scope}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="strategy-rules-section">
        <h4>Priority-Ordered Rules ({orderedRules.length})</h4>
        <ol>
          {orderedRules.map((rule) => (
            <li key={rule.id} data-rule-id={rule.id}>
              <strong>{rule.name}</strong> <code>({rule.id})</code> — Priority:{" "}
              <span>{rule.priority}</span> | Event:{" "}
              <code>
                {typeof rule.event === "string" ? rule.event : rule.event.type}
              </code>{" "}
              | <span>{rule.enabled ? "Enabled" : "Disabled"}</span> |
              Condition: <code>{rule.when.operator ?? rule.when.type}</code> |
              Actions: <span>{rule.then.length}</span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
