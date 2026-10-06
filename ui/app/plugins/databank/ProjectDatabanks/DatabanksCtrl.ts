import { useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';
import { useAppStore } from '../../../host/store';

export type SplitterState = 'collapsed' | 'active' | 'maximised';
export type SplitterAction = 'toggle' | 'maximize' | 'restore';

export function nextSplitterState(state: SplitterState, action: SplitterAction): SplitterState {
  if (action === 'maximize') return state === 'active' ? 'maximised' : state;
  if (action === 'restore') return state === 'maximised' ? 'active' : state;
  // The donor opener control only exists in the collapsed and active states.
  if (state === 'collapsed') return 'active';
  if (state === 'active') return 'collapsed';
  return state;
}

export function computeDraggedHeight(pointerClientY: number, rootTop: number): number {
  return Math.round(pointerClientY - rootTop);
}

export function useDatabanksPane() {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const dragging = useRef(false);
  const [state, setState] = useState<SplitterState>('collapsed');
  const [topHeight, setTopHeight] = useState<number | null>(null);
  const bankCount = useAppStore((s) => s.databanks.length);
  const strategyCount = useAppStore((s) => s.strategies.length);

  const apply = (action: SplitterAction) => {
    const next = nextSplitterState(state, action);
    if (next === state) return;
    if (action === 'toggle') setTopHeight(null);
    setState(next);
    window.dispatchEvent(new Event('resize'));
  };

  const onResizerDown = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (state !== 'active') return;
    dragging.current = true;
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const onResizerMove = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (!dragging.current || !rootRef.current) return;
    setTopHeight(computeDraggedHeight(e.clientY, rootRef.current.getBoundingClientRect().top));
  };

  const endDrag = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    dragging.current = false;
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    window.dispatchEvent(new Event('resize'));
  };

  const classes = ['sq-splitter'];
  if (state !== 'collapsed') classes.push('active');
  if (state === 'maximised') classes.push('maximised');

  return { rootRef, state, topHeight, bankCount, strategyCount, apply, onResizerDown, onResizerMove, endDrag, classes };
}
