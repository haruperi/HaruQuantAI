import { useState } from 'react';

/** Invoked unconditionally by the retained dispatcher to preserve draft lifetime. */
export function usePortfolioCorrelation() {
  const [period, setPeriod] = useState('Day');
  return { period, setPeriod };
}
