import React from 'react';

export interface WFFitnessCriterion {
  metric: string;
  weight: number;
  maximize: boolean;
  target_value: number;
}

export interface FitnessMethodWFResultProps {
  criteria: WFFitnessCriterion[];
  onChange?: (criteria: WFFitnessCriterion[]) => void;
  calculatedFitness?: number;
}

export function FitnessMethodWFResult({
  criteria,
  onChange,
  calculatedFitness,
}: FitnessMethodWFResultProps) {
  const updateWeight = (index: number, weight: number) => {
    if (!onChange) return;
    const next = [...criteria];
    next[index] = { ...next[index], weight };
    onChange(next);
  };

  return (
    <div className="wf-fitness-panel" data-testid="wf-fitness-panel">
      <h4>Walk-Forward Fitness Configuration</h4>
      {calculatedFitness !== undefined && (
        <div className="wf-fitness-score" data-testid="wf-fitness-score">
          Current Score: {calculatedFitness.toFixed(6)}
        </div>
      )}
      <ul className="wf-criteria-list">
        {criteria.map((c, idx) => (
          <li key={c.metric} className="wf-criterion-item">
            <span>{c.metric} (Target: {c.target_value}, {c.maximize ? 'Max' : 'Min'})</span>
            <label>
              Weight:
              <input
                type="number"
                min="0"
                step="0.1"
                value={c.weight}
                onChange={(e) => updateWeight(idx, parseFloat(e.target.value) || 0)}
                aria-label={`Weight for ${c.metric}`}
              />
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
