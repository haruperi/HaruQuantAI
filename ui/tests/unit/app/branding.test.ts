import { describe, expect, it } from 'vitest';

import {
  DEFAULT_BROKER_NAME,
  EQUITY_SOURCE_NAME,
  FUTURES_SOURCE_NAME,
  PRODUCT_NAME,
  hasLegacyVisibleBranding,
  normalizeLegacyBranding,
  normalizeLegacyUiText,
} from '../../../app/host/branding';

describe('HaruQuantAI branding', () => {
  it('defines the current product and unprefixed data labels', () => {
    expect(PRODUCT_NAME).toBe('HaruQuantAI');
    expect(DEFAULT_BROKER_NAME).toBe('Default');
    expect(EQUITY_SOURCE_NAME).toBe('Equity');
    expect(FUTURES_SOURCE_NAME).toBe('Futures');
  });

  it('normalizes full and short legacy product branding', () => {
    expect(normalizeLegacyUiText('StrategyQuant X and SQX Business')).toBe('HaruQuantAI and Business');
    expect(normalizeLegacyUiText('SQ Equity · SQ Futures · SQ default')).toBe('Equity · Futures · Default');
    expect(normalizeLegacyUiText('SQ DataManager and SQ CDN')).toBe('HaruQuantAI Data Manager and HaruQuantAI CDN');
  });

  it('normalizes nested persisted display values without changing keys or storage identifiers', () => {
    const value = normalizeLegacyBranding({
      source: 'SQ Futures', brokerName: 'SQ default', message: 'SQ Equity dataset update',
      nested: [{ note: 'No native SQX engine' }], storageKey: 'sqx-data-manager-v1',
    });
    expect(value).toEqual({
      source: 'Futures', brokerName: 'Default', message: 'Equity dataset update',
      nested: [{ note: 'No native HaruQuantAI engine' }], storageKey: 'sqx-data-manager-v1',
    });
  });

  it('detects only user-visible legacy product forms', () => {
    expect(hasLegacyVisibleBranding('StrategyQuant CDN')).toBe(true);
    expect(hasLegacyVisibleBranding('SQ Futures data')).toBe(true);
    expect(hasLegacyVisibleBranding('HaruQuantAI Futures data')).toBe(false);
    expect(hasLegacyVisibleBranding('sqx-data-manager-v1')).toBe(false);
  });
});
