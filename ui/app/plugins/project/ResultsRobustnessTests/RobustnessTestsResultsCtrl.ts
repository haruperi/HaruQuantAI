import { useState } from 'react';

/** Invoked unconditionally by the retained dispatcher; no analysis is executed. */
export function useRobustnessTestsResults() {
  const [method, setMethod] = useState('Randomize trades order');
  return { method, setMethod };
}
