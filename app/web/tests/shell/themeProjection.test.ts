import { test, expect } from 'vitest';
import { ThemeProjection } from '../../shell/themeProjection';

test('home theme name projection', () => {
  expect(ThemeProjection.for_home('Dark skin')).toBe('dark');
  expect(ThemeProjection.for_home('Light skin')).toBe('light');
  expect(ThemeProjection.for_home('dark skin')).toBe('light');
  expect(ThemeProjection.for_home('')).toBe('light');
});
