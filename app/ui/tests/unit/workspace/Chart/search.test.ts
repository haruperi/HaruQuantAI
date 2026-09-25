import { it, expect } from 'vitest';
import { fuzzy } from '../../../../src/workspace/Chart/src/utils/search';
import { symbols } from '../../../../src/workspace/Chart/src/feed/symbols';
it('offers more than forty instruments and fuzzy matching', () => {
  expect(symbols.length).toBeGreaterThanOrEqual(40);
  expect(fuzzy('btct', 'BTCUSDT Bitcoin')).toBe(true);
  expect(fuzzy('gold', 'Gold Spot')).toBe(true);
  expect(fuzzy('xyz', 'Gold')).toBe(false);
});
