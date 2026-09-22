import type { RuleNode } from '../../app/types';

export const rules: RuleNode[] = [
  { id: 'r1', depth: 0, kind: 'event', label: 'On Bar Open' }, { id: 'r2', depth: 1, kind: 'if', label: 'IF' },
  { id: 'r3', depth: 2, kind: 'condition', label: 'EMA(12) crosses above EMA(28)' }, { id: 'r4', depth: 2, kind: 'condition', label: 'ATR(14) > 0.0012' },
  { id: 'r5', depth: 1, kind: 'then', label: 'THEN' }, { id: 'r6', depth: 2, kind: 'action', label: 'Enter at Market (Long)' },
  { id: 'r7', depth: 2, kind: 'action', label: 'Set Stop Loss: 90 pips' }, { id: 'r8', depth: 2, kind: 'action', label: 'Set Profit Target: 180 pips' },
];
