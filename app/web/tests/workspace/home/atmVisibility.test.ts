import { test, expect } from 'vitest';
import { atmVisibility } from '../../../workspaces/home/atmVisibility';

test('hides unsupported engines', () => {
  const unsupported = [
    'Stockpicker',
    'Single-asset cloud strategy',
    'NinjaTrader8',
    'NinjaTrader',
  ];
  for (const engine of unsupported) {
    expect(atmVisibility(engine)).toEqual({
      tab: 'settings-advancedtm',
      show: false,
    });
  }
});

test('shows other engine names', () => {
  const supported = ['MetaTrader5', 'stockpicker', '', 'Stockpicker '];
  for (const engine of supported) {
    expect(atmVisibility(engine)).toEqual({
      tab: 'settings-advancedtm',
      show: true,
    });
  }
});

test('returns detached event data', () => {
  const first = atmVisibility('MetaTrader5');
  expect(first).toEqual({
    tab: 'settings-advancedtm',
    show: true,
  });

  (first as { show: boolean }).show = false;

  const second = atmVisibility('MetaTrader5');
  expect(second).toEqual({
    tab: 'settings-advancedtm',
    show: true,
  });
});
