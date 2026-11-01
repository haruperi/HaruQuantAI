import React from 'react';

export interface SequentialOptStepData {
  param_name: string;
  original_value: number;
  best_value: number;
  tested_values: number[];
  metric_values: number[];
}

export interface ResultsSequentialOptimizationProps {
  strategyId: string;
  fitnessMetric: string;
  originalMetric: number;
  optimizedMetric: number;
  steps: SequentialOptStepData[];
  onApplyParams?: (params: Record<string, number>) => void;
}

export function ResultsSequentialOptimization({
  strategyId,
  fitnessMetric,
  originalMetric,
  optimizedMetric,
  steps,
  onApplyParams,
}: ResultsSequentialOptimizationProps) {
  const handleApply = () => {
    if (!onApplyParams) return;
    const bestMap: Record<string, number> = {};
    for (const step of steps) {
      bestMap[step.param_name] = step.best_value;
    }
    onApplyParams(bestMap);
  };

  return (
    <div className="results-sequential-optimization" data-testid="results-sequential-optimization">
      <div className="seq-opt-header">
        <h3>Sequential Optimization: {strategyId}</h3>
        <p>
          Metric: {fitnessMetric} | Baseline: {originalMetric.toFixed(2)} | Optimized:{' '}
          {optimizedMetric.toFixed(2)}
        </p>
        {onApplyParams && (
          <button className="sqd-btn" onClick={handleApply} aria-label="Apply Best Parameters">
            Apply Best Parameters
          </button>
        )}
      </div>

      <div className="seq-steps-list">
        {steps.map((s) => (
          <div key={s.param_name} className="seq-step-card">
            <h4>{s.param_name}</h4>
            <p>
              Original: {s.original_value} -&gt; Best: <strong>{s.best_value}</strong>
            </p>
            <div className="step-values-summary">
              <span>Tested: {s.tested_values.length} values</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
