import { describe, expect, it } from 'vitest';
import {
  computeDraggedHeight,
  nextSplitterState,
} from '../../../../../app/plugins/databank/Optimizer/ProjectDatabanks/DatabankSplitter';
import type { SplitterAction, SplitterState } from '../../../../../app/plugins/databank/Optimizer/ProjectDatabanks/DatabankSplitter';
import { databanks, strategies } from '../../../../../app/plugins/databank/Optimizer/fixtures';

const ALL_STATES: SplitterState[] = ['collapsed', 'active', 'maximised'];

describe('DatabankSplitter state machine (donor SQX144-EV-000025..027)', () => {
  it('starts collapsed and toggles to active and back', () => {
    expect(nextSplitterState('collapsed', 'toggle')).toBe('active');
    expect(nextSplitterState('active', 'toggle')).toBe('collapsed');
  });

  it('maximizes only from active and restores only from maximised', () => {
    expect(nextSplitterState('active', 'maximize')).toBe('maximised');
    expect(nextSplitterState('maximised', 'restore')).toBe('active');
  });

  it('leaves unreachable controls as no-ops', () => {
    // The donor cluster hides the opener/resizer/maximizer while maximised
    // and the normalizer otherwise; those actions must not change state.
    expect(nextSplitterState('collapsed', 'maximize')).toBe('collapsed');
    expect(nextSplitterState('collapsed', 'restore')).toBe('collapsed');
    expect(nextSplitterState('active', 'restore')).toBe('active');
    expect(nextSplitterState('maximised', 'maximize')).toBe('maximised');
    expect(nextSplitterState('maximised', 'toggle')).toBe('maximised');
  });

  it('covers every state/action pair without unknown states', () => {
    const actions: SplitterAction[] = ['toggle', 'maximize', 'restore'];
    for (const state of ALL_STATES) {
      for (const action of actions) {
        expect(ALL_STATES).toContain(nextSplitterState(state, action));
      }
    }
  });

  it('computes dragged height from pointer position minus splitter top', () => {
    expect(computeDraggedHeight(400, 100)).toBe(300);
    expect(computeDraggedHeight(400, 100.4)).toBe(300);
    expect(computeDraggedHeight(0, 0)).toBe(0);
  });

  it('shows fixture demo counts on the collapsed bar', () => {
    // The header reads bank count and total strategies from the fixture
    // store; pin the demo values so silent fixture drift is caught.
    expect(databanks.length).toBe(3);
    expect(strategies.length).toBe(70);
  });
});
