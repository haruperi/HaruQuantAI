import { it, expect } from 'vitest';
import { triggered } from '../../../../app/workspace/Chart/src/store/alerts';
import type { Alert } from '../../../../app/workspace/Chart/src/types';
const a: Alert = {
  id: '1',
  symbol: 'XAUUSD',
  condition: 'up',
  value: 100,
  upper: 110,
  expires: 1000,
  once: true,
  active: true,
  triggers: 0,
};
it('requires a crossing and respects expiry and disabled state', () => {
  expect(triggered(a, 99, 100, 1)).toBe(true);
  expect(triggered(a, 100, 101, 1)).toBe(false);
  expect(triggered(a, 99, 101, 1000)).toBe(false);
  expect(triggered({ ...a, active: false }, 99, 101, 1)).toBe(false);
  expect(triggered({ ...a, condition: 'down' }, 101, 100, 1)).toBe(true);
});
it('channel entries and exits rearm outside their condition', () => {
  expect(triggered({ ...a, condition: 'enter' }, 99, 105, 1)).toBe(true);
  expect(triggered({ ...a, condition: 'enter' }, 105, 106, 1)).toBe(false);
  expect(triggered({ ...a, condition: 'exit' }, 105, 111, 1)).toBe(true);
});
