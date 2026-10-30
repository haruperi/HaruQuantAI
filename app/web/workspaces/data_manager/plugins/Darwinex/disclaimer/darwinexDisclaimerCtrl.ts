import { useCallback } from 'react';
/** Preserve the supplied owner close lifecycle for exported disclaimer composition. */
export function useDarwinexDisclaimer(onClose: () => void): () => void {
  return useCallback(() => onClose(), [onClose]);
}
