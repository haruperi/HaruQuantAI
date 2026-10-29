import { test, expect } from 'vitest';
import { DatabankDefaults } from '../../../workspaces/home/databankDefaults';

test('column reset values', () => {
  expect(DatabankDefaults.reset_value('text')).toBe('');
  expect(DatabankDefaults.reset_value('dateTime')).toBe('');
  expect(DatabankDefaults.reset_value('filterResult')).toBe('');

  expect(DatabankDefaults.reset_value('integer')).toBe(0);
  expect(DatabankDefaults.reset_value('decimal')).toBe(0);
  expect(DatabankDefaults.reset_value('DateTime')).toBe(0);
  expect(DatabankDefaults.reset_value('')).toBe(0);
});
