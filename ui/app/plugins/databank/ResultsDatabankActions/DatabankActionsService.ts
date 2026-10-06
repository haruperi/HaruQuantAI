import type { Strategy } from '../../../host/types';

/** Preserve the panel's existing selected-strategy fallback order. */
export function getCurrentDatabankStrategy(
  strategies: readonly Strategy[],
  selectedStrategyId: string | undefined,
  selectedInBank: readonly Strategy[],
): Strategy | undefined {
  return strategies.find(strategy => strategy.id === selectedStrategyId) || selectedInBank[0];
}
