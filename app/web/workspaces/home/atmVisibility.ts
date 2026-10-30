const UNSUPPORTED_ENGINES = new Set([
  'Stockpicker',
  'Single-asset cloud strategy',
  'NinjaTrader8',
  'NinjaTrader',
]);

export function atmVisibility(engine: string): {
  tab: 'settings-advancedtm';
  show: boolean;
} {
  return {
    tab: 'settings-advancedtm',
    show: !UNSUPPORTED_ENGINES.has(engine),
  };
}
