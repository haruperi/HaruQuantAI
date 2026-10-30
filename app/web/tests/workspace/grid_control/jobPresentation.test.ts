import { expect, test } from 'vitest';

import { GridJobPresentation } from '../../../workspaces/grid_control/jobPresentation';

test('grid labels', () => {
  expect(GridJobPresentation.kind(true)).toBe('Continuous');
  expect(GridJobPresentation.kind(false)).toBe('One time');

  expect(GridJobPresentation.state(true)).toBe('Waiting');
  expect(GridJobPresentation.state(false)).toBe('Running');

  expect(GridJobPresentation.progress(-1)).toBe('N/A');
  expect(GridJobPresentation.progress(0)).toBe('0%');
  expect(GridJobPresentation.progress(12.5)).toBe('12.5%');
  expect(GridJobPresentation.progress(-2)).toBe('-2%');
});

test('active-only refresh metadata', () => {
  expect(GridJobPresentation.can_refresh('GRIDCONTROL')).toBe(true);
  expect(GridJobPresentation.can_refresh('gridcontrol')).toBe(false);
  expect(GridJobPresentation.can_refresh('BUILDER')).toBe(false);

  expect(GridJobPresentation.interval_ms()).toBe(3000);
});
