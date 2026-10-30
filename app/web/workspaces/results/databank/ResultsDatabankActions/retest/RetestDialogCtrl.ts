import { useState } from 'react';

/** Preserve existing local checkbox state and demo callback sequence. */
export function useRetestDialog(onMove: (removeFromDatabank: boolean) => void, onClose: () => void) {
  const [applyConfig, setApplyConfig] = useState(false);
  const copy = () => { onMove(false); onClose(); };
  const move = () => { onMove(true); onClose(); };
  return { applyConfig, setApplyConfig, copy, move };
}
