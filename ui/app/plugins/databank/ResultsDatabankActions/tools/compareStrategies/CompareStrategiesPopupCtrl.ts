import { useState, useMemo } from 'react';
import type { Strategy } from '../../../../../host/types';

/** Preserve the independent comparison dialog's mounted draft state. */
export function useCompareStrategiesPopup(strategies: Strategy[], initialStrategyId1?: string, initialStrategyId2?: string) {
  const [strategyId1, setStrategyId1] = useState<string>(
    initialStrategyId1 || strategies[0]?.id || ''
  );
  const [strategyId2, setStrategyId2] = useState<string>(
    initialStrategyId2 || strategies[1]?.id || strategies[0]?.id || ''
  );
  const [expandedSections, setExpandedSections] = useState({
    kpi: true,
    equity: true,
    params: true,
  });

  const s1 = useMemo(
    () => strategies.find(s => s.id === strategyId1) || strategies[0],
    [strategies, strategyId1]
  );
  const s2 = useMemo(
    () => strategies.find(s => s.id === strategyId2) || strategies[1] || strategies[0],
    [strategies, strategyId2]
  );

  const toggleAll = (expand: boolean) => {
    setExpandedSections({
      kpi: expand,
      equity: expand,
      params: expand,
    });
  };

  return { strategyId1, setStrategyId1, strategyId2, setStrategyId2, expandedSections, setExpandedSections, s1, s2, toggleAll };
}
