import { useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent, ReactNode } from 'react';
import { useAppStore } from '../../../app/store';
import { DatabankPanel } from './DatabankPanel';

/**
 * SQX-parity three-state splitter for the shared databanks lower pane.
 *
 * Donor behavior (evidence SQX144-EV-000025..027): collapsed count bar by
 * default, chevron-only toggle, 100px expanded minimum, drag-resize of the
 * workspace pane from the pointer position, maximised state hiding the
 * workspace pane, a window resize dispatch on every change, and no state
 * persistence across loads. A toggle resets any dragged height, matching the
 * donor's observable outcome.
 */

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

// Grayscale chevron/handle glyphs drawn to the donor icon pixel shapes
// (31x11 opener in the collapsed bar; 30x9 controls in the expanded strip).
function OpenerOpenIcon() {
  return (
    <svg width="31" height="11" viewBox="0 0 31 11" aria-hidden="true">
      <polyline
        points="9.5,8.4 15.5,2.6 21.5,8.4"
        fill="none"
        stroke="#4f4f4f"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="11.6,8.4 15.5,4.3 19.4,8.4"
        fill="none"
        stroke="#d6d6d6"
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChevronIcon({ up }: { up: boolean }) {
  return (
    <svg width="30" height="9" viewBox="0 0 30 9" aria-hidden="true">
      <polyline
        points={up ? '10,7.3 15,2.4 20,7.3' : '10,2.4 15,7.3 20,2.4'}
        fill="none"
        stroke="#4f4f4f"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points={up ? '11.8,7.3 15,4 18.2,7.3' : '11.8,4 15,7.3 18.2,4'}
        fill="none"
        stroke="#d6d6d6"
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ResizerIcon() {
  return (
    <svg width="30" height="9" viewBox="0 0 30 9" aria-hidden="true">
      <rect x="10" y="2.7" width="10" height="1.5" rx="0.75" fill="#4f4f4f" />
      <rect x="10" y="5.2" width="10" height="1.5" rx="0.75" fill="#4f4f4f" />
    </svg>
  );
}

export function DatabankSplitter({ showBank, children }: { showBank: boolean; children: ReactNode }) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const dragging = useRef(false);
  const [state, setState] = useState<SplitterState>('collapsed');
  const [topHeight, setTopHeight] = useState<number | null>(null);
  const bankCount = useAppStore((s) => s.databanks.length);
  const strategyCount = useAppStore((s) => s.strategies.length);

  if (!showBank) return <>{children}</>;

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

  return (
    <div ref={rootRef} className={classes.join(' ')}>
      <div
        className="sq-splitter-top"
        style={state === 'active' && topHeight !== null ? { flexBasis: `${topHeight}px` } : undefined}
      >
        {children}
      </div>
      <div className="sqn-databanks">
        <div className="resizer-container">
          <button
            type="button"
            className="ctl maximizer"
            aria-label="Maximize databanks"
            onClick={() => apply('maximize')}
          >
            <ChevronIcon up />
          </button>
          <div
            className="ctl resizer"
            role="separator"
            aria-orientation="horizontal"
            aria-label="Resize databanks pane"
            onPointerDown={onResizerDown}
            onPointerMove={onResizerMove}
            onPointerUp={endDrag}
            onPointerCancel={endDrag}
          >
            <ResizerIcon />
          </div>
          <button
            type="button"
            className="ctl opener"
            aria-label={state === 'collapsed' ? 'Expand databanks' : 'Collapse databanks'}
            onClick={() => apply('toggle')}
          >
            {state === 'collapsed' ? <OpenerOpenIcon /> : <ChevronIcon up={false} />}
          </button>
          <button
            type="button"
            className="ctl normalizer"
            aria-label="Restore workspace"
            onClick={() => apply('restore')}
          >
            <ChevronIcon up={false} />
          </button>
        </div>
        <div className="sqn-databanks-header">
          <div>DATABANKS {bankCount}</div>
          <div>STRATEGIES: {strategyCount}</div>
        </div>
        <div className={`databanks-body${state === 'collapsed' ? ' databanks-body-hidden' : ''}`}>
          <DatabankPanel />
        </div>
      </div>
    </div>
  );
}
