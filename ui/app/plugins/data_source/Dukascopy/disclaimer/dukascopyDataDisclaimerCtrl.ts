import { useCallback } from 'react';

/** Modal owns focus/Escape lifecycle; this controller unifies close actions. */
export function useDisclaimerController(onClose: () => void) {
  const close = useCallback((): void => onClose(), [onClose]);
  return { close };
}
