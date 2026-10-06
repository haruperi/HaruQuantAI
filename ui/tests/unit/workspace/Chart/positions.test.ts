import { it, expect } from 'vitest';
import {
  advancePosition,
  pnl,
  validateOrder,
} from '../../../../app/workspace/Chart/src/store/positions';
import type { Position } from '../../../../app/workspace/Chart/src/types';
const p: Position = {
  id: '1',
  symbol: 'XAUUSD',
  side: 'buy',
  type: 'limit',
  quantity: 2,
  entry: 100,
  sl: 90,
  tp: 110,
  status: 'pending',
  exit: null,
};
it('waits for limit and executes at observed price, then handles stop gap', () => {
  expect(advancePosition(p, 101)).toBe(p);
  const open = advancePosition(p, 99);
  expect(open.status).toBe('open');
  expect(open.entry).toBe(99);
  const closed = advancePosition(open, 85);
  expect(closed.status).toBe('closed');
  expect(pnl(closed, 200)).toBe(-28);
});
it('validates finite quantity and bracket direction', () => {
  expect(validateOrder(0, 100, 'buy', null, null)).not.toBe('');
  expect(validateOrder(1, 100, 'buy', 101, null)).not.toBe('');
  expect(validateOrder(1, 100, 'sell', 110, 90)).toBe('');
});
