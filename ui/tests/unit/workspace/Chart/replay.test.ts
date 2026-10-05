import { it, expect } from 'vitest';
import { replayStep } from '../../../../app/workspace/Chart/src/store/replay';
it('clamps replay at history boundaries', () => {
  expect(replayStep(0, -1, 10)).toBe(0);
  expect(replayStep(9, 1, 10)).toBe(9);
  expect(replayStep(4, 1, 10)).toBe(5);
});
