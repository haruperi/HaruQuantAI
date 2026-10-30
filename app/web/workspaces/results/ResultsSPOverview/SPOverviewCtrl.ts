import { useState } from 'react';

/** Existing traded-stock volume preview toggle. */
export function useSPOverview() {
  const [showAll, setShowAll] = useState(false);
  return { showAll, setShowAll };
}
