import React, { useState } from 'react';

export interface FitnessCriterionItem {
  columnId: string;
  weight: number;
  maximize: boolean;
  targetValue?: number;
  sampleType: string;
}

export interface FitnessMethodStrategyResultProps {
  initialCriteria?: FitnessCriterionItem[];
  onChange?: (criteria: FitnessCriterionItem[]) => void;
}

const DEFAULT_CRITERIA: FitnessCriterionItem[] = [
  {
    columnId: 'ReturnDDRatio',
    weight: 1.0,
    maximize: true,
    sampleType: 'InSample',
  },
];

export const FitnessMethodStrategyResult: React.FC<FitnessMethodStrategyResultProps> = ({
  initialCriteria = DEFAULT_CRITERIA,
  onChange = () => {},
}) => {
  const [criteria, setCriteria] = useState<FitnessCriterionItem[]>(initialCriteria);

  const updateWeight = (index: number, weight: number) => {
    const updated = criteria.map((c, i) => (i === index ? { ...c, weight } : c));
    setCriteria(updated);
    onChange(updated);
  };

  const toggleMaximize = (index: number) => {
    const updated = criteria.map((c, i) => (i === index ? { ...c, maximize: !c.maximize } : c));
    setCriteria(updated);
    onChange(updated);
  };

  return (
    <div data-testid="fitness-method-strategy-result" className="fitness-method-container">
      <h4>Fitness Method: Strategy Result</h4>
      <table className="fitness-criteria-table">
        <thead>
          <tr>
            <th>Column ID</th>
            <th>Sample</th>
            <th>Weight</th>
            <th>Maximize</th>
          </tr>
        </thead>
        <tbody>
          {criteria.map((c, idx) => (
            <tr key={`${c.columnId}-${idx}`} data-testid={`fitness-row-${idx}`}>
              <td>{c.columnId}</td>
              <td>{c.sampleType}</td>
              <td>
                <input
                  type="number"
                  aria-label={`Weight for ${c.columnId}`}
                  value={c.weight}
                  step={0.1}
                  min={0.1}
                  onChange={e => updateWeight(idx, parseFloat(e.target.value) || 0.1)}
                />
              </td>
              <td>
                <input
                  type="checkbox"
                  aria-label={`Maximize for ${c.columnId}`}
                  checked={c.maximize}
                  onChange={() => toggleMaximize(idx)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default FitnessMethodStrategyResult;
