import type { Dispatch, SetStateAction } from 'react';

/** Attach the existing interval simulation; caller owns returned cleanup. */
export function subscribeMockLoadProgress(setProgress: Dispatch<SetStateAction<number>>): () => void {
  const timer = setInterval(() => {
    setProgress(p => {
      if (p >= 100) {
        clearInterval(timer);
        return 100;
      }
      return Math.min(100, p + 10);
    });
  }, 120);
  return () => clearInterval(timer);
}
