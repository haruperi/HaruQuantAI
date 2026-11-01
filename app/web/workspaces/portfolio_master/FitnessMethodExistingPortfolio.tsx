import { useState } from 'react';

export interface CriterionItem {
  id: string;
  metricId: 'NetProfit' | 'PctStagnation' | 'ReturnDD';
  valueType: number; // 1 = Range, 2 = Approximate
  approximateType: number; // 2
  weight: number;
  target: number;
}

export interface FitnessExistingPortfolioProps {
  criteria?: CriterionItem[];
  onChange?: (criteria: CriterionItem[]) => void;
}

const DEFAULT_CRITERIA: CriterionItem[] = [
  {
    id: '1',
    metricId: 'ReturnDD',
    valueType: 1,
    approximateType: 2,
    weight: 1.0,
    target: 0.0,
  },
  {
    id: '2',
    metricId: 'PctStagnation',
    valueType: 1,
    approximateType: 2,
    weight: 1.0,
    target: 0.0,
  },
];

export function FitnessMethodExistingPortfolio({
  criteria = DEFAULT_CRITERIA,
  onChange,
}: FitnessExistingPortfolioProps) {
  const [items, setItems] = useState<CriterionItem[]>(criteria);

  const updateItem = (index: number, patch: Partial<CriterionItem>) => {
    const updated = items.map((item, i) => {
      if (i !== index) return item;
      const next = { ...item, ...patch };
      // If valueType changed and is not approximate, reset target to 0
      if (next.valueType !== next.approximateType) {
        next.target = 0.0;
      }
      return next;
    });
    setItems(updated);
    onChange?.(updated);
  };

  const addCriterion = () => {
    const newItem: CriterionItem = {
      id: String(items.length + 1),
      metricId: 'NetProfit',
      valueType: 1,
      approximateType: 2,
      weight: 1.0,
      target: 0.0,
    };
    const updated = [...items, newItem];
    setItems(updated);
    onChange?.(updated);
  };

  const removeCriterion = (index: number) => {
    const updated = items.filter((_, i) => i !== index);
    setItems(updated);
    onChange?.(updated);
  };

  return (
    <div className="fitness-existing-portfolio">
      <h4>Ranking Criteria</h4>
      <table className="pf-table">
        <thead>
          <tr>
            <th>Ranking Criterium</th>
            <th>Type</th>
            <th>Weight</th>
            <th>Target</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => {
            const isTargetEnabled = item.valueType === item.approximateType;
            return (
              <tr key={item.id}>
                <td>
                  <select
                    aria-label={`Criterion ${item.id} metric`}
                    value={item.metricId}
                    onChange={(e) =>
                      updateItem(index, {
                        metricId: e.target.value as CriterionItem['metricId'],
                      })
                    }
                  >
                    <option value="ReturnDD">Return / Drawdown ratio</option>
                    <option value="PctStagnation">% Stagnation</option>
                    <option value="NetProfit">Net Profit (Return)</option>
                  </select>
                </td>
                <td>
                  <select
                    aria-label={`Criterion ${item.id} type`}
                    value={item.valueType}
                    onChange={(e) =>
                      updateItem(index, { valueType: Number(e.target.value) })
                    }
                  >
                    <option value={1}>Maximize / Minimize</option>
                    <option value={2}>Approximate target</option>
                  </select>
                </td>
                <td>
                  <input
                    aria-label={`Criterion ${item.id} weight`}
                    type="number"
                    min={0}
                    step={0.1}
                    value={item.weight}
                    onChange={(e) =>
                      updateItem(index, { weight: Number(e.target.value) })
                    }
                  />
                </td>
                <td>
                  <input
                    aria-label={`Criterion ${item.id} target`}
                    type="number"
                    disabled={!isTargetEnabled}
                    value={item.target}
                    onChange={(e) =>
                      updateItem(index, { target: Number(e.target.value) })
                    }
                  />
                </td>
                <td>
                  <button
                    className="sqd-btn"
                    aria-label={`Delete criterion ${item.id}`}
                    onClick={() => removeCriterion(index)}
                  >
                    ×
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <button className="sqd-btn" onClick={addCriterion}>
        Add Criterion
      </button>
    </div>
  );
}
