import { useState } from 'react';

/** Existing benchmark menu lifetime, mounted with the equity toolbar. */
export function useBenchmark() {
  const [benchOpen, setBenchOpen] = useState(false);
  return { benchOpen, setBenchOpen };
}
