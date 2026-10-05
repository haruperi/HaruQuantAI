export const PRODUCT_NAME = 'HaruQuantAI';
export const DEFAULT_BROKER_NAME = 'Default';
export const EQUITY_SOURCE_NAME = 'Equity';
export const FUTURES_SOURCE_NAME = 'Futures';

const legacyVisibleBranding = /StrategyQuant|\bSQX\b|\bSQ (?:Equity|Futures|default|DataManager|Data Manager|CDN|Data)\b/;

export function normalizeLegacyUiText(value: string): string {
  return value
    .replaceAll('SQX Business', 'Business')
    .replaceAll('SQX for Business', `${PRODUCT_NAME} for Business`)
    .replaceAll('SQ DataManager', `${PRODUCT_NAME} Data Manager`)
    .replaceAll('SQ Data Manager', `${PRODUCT_NAME} Data Manager`)
    .replaceAll('SQ default', DEFAULT_BROKER_NAME)
    .replaceAll('SQ Equity', EQUITY_SOURCE_NAME)
    .replaceAll('SQ Futures', FUTURES_SOURCE_NAME)
    .replaceAll('SQ CDN', `${PRODUCT_NAME} CDN`)
    .replaceAll('SQ Data', `${PRODUCT_NAME} Data`)
    .replaceAll('StrategyQuant X', PRODUCT_NAME)
    .replaceAll('StrategyQuant', PRODUCT_NAME)
    .replace(/\bSQX\b/g, PRODUCT_NAME);
}

export function normalizeLegacyBranding<T>(value: T): T {
  if (typeof value === 'string') return normalizeLegacyUiText(value) as T;
  if (Array.isArray(value)) return value.map(item => normalizeLegacyBranding(item)) as T;
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalizeLegacyBranding(item)])) as T;
  }
  return value;
}

export function hasLegacyVisibleBranding(value: string): boolean {
  return legacyVisibleBranding.test(value);
}
