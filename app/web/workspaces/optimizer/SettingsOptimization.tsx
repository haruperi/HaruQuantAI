import React from 'react';

export interface OptimizableParameter {
  name: string;
  param_type: 'INT' | 'FLOAT' | 'BOOL' | 'SHIFT' | 'PERIOD';
  original_value: number | boolean;
  enabled: boolean;
  start: number;
  stop: number;
  step: number;
}

export interface OptimizationSettingsProps {
  strategyId?: string;
  optimizationType: 'SIMPLE' | 'GENETIC' | 'WALK_FORWARD' | 'WALK_FORWARD_MATRIX' | 'SYS_PARAM_PERMUTATION' | 'SEQUENTIAL';
  maxTests: number;
  periodType: 'percent' | 'days' | 'bars';
  parameters: OptimizableParameter[];
  onChange?: (parameters: OptimizableParameter[]) => void;
}

export function SettingsOptimization({
  strategyId,
  optimizationType,
  maxTests,
  periodType,
  parameters,
  onChange,
}: OptimizationSettingsProps) {
  const toggleParameter = (index: number) => {
    if (!onChange) return;
    const next = [...parameters];
    next[index] = { ...next[index], enabled: !next[index].enabled };
    onChange(next);
  };

  return (
    <div className="settings-optimization-panel" data-testid="settings-optimization">
      <h3>Optimization Settings: {optimizationType}</h3>
      <p>Strategy: {strategyId || 'None'} | Max Tests: {maxTests} | Period: {periodType}</p>
      <table className="optimization-parameters-table">
        <thead>
          <tr>
            <th>Enabled</th>
            <th>Name</th>
            <th>Type</th>
            <th>Original</th>
            <th>Start</th>
            <th>Stop</th>
            <th>Step</th>
          </tr>
        </thead>
        <tbody>
          {parameters.map((p, idx) => (
            <tr key={p.name}>
              <td>
                <input
                  type="checkbox"
                  checked={p.enabled}
                  onChange={() => toggleParameter(idx)}
                  aria-label={`Toggle ${p.name}`}
                />
              </td>
              <td>{p.name}</td>
              <td>{p.param_type}</td>
              <td>{String(p.original_value)}</td>
              <td>{p.start}</td>
              <td>{p.stop}</td>
              <td>{p.step}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
