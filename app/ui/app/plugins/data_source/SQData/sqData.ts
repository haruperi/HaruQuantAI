export const timezones: string[][] = [
  ["EETUS", "(EST+07) New York Trading hours, US DST"],
  ["EET", "(UTC+02) European DST"],
  ["Etc/UCT", "(UTC) Coordinated Universal Time"],
  ["Europe/London", "(UTC) Dublin, Edinburgh, Lisbon, London"],
  ["America/New_York", "(UTC-05) New York, US & Canada, EST"],
  ["UTC", "UTC (application alias)"]
];

export function validateName(name: string, existing: string[], label = 'Symbol'): void {
  if (!name || name.length > 128 || !/^[a-zA-Z0-9_@.:$]+$/.test(name)) throw new Error(`${label} name is required (maximum 128 characters); use letters, numbers, or _ @ . : $.`);
  if (existing.some(item => item.toLowerCase() === name.toLowerCase())) throw new Error(`${label} ${name} already exists.`);
}

export type SQProvider = 'equity' | 'futures';
export type SQProfile = 'Full' | 'Starter';
export interface SQTicker { ticker: string; name: string; exchange: string; type: string; dataFrom: string; timezone: string; continuous: boolean; free: boolean }
export interface SQConfig { exchange: string; symbols: string; searchInTicker: boolean; searchInName: boolean; exact: boolean; onlyContFutures: boolean; postfix: string; barType: 'start' | 'end'; timezoneType: 0 | 1 | 2; timezoneShift: number; timezone: string }
export const providerLabel = (provider: SQProvider) => provider === 'equity' ? 'Equity Data' : 'Futures Data';
export const sourceLabel = (provider: SQProvider) => provider === 'equity' ? 'Equity' : 'Futures';
export const defaultSQConfig = (): SQConfig => ({ exchange: '', symbols: '', searchInTicker: true, searchInName: true, exact: false, onlyContFutures: true, postfix: '', barType: 'end', timezoneType: 2, timezoneShift: 5, timezone: timezones[0][0] });
// Explicit offline fixtures. HaruQuantAI obtains catalogues/entitlements from backend responses.
const equity = [
  ['AAPL', 'Apple Inc.', 'NASDAQ', 'Stock', '1980-12-12', true],
  ['MSFT', 'Microsoft Corporation', 'NASDAQ', 'Stock', '1986-03-13', true],
  ['AMZN', 'Amazon.com Inc.', 'NASDAQ', 'Stock', '1997-05-15', false],
  ['NVDA', 'NVIDIA Corporation', 'NASDAQ', 'Stock', '1999-01-22', false],
  ['GOOGL', 'Alphabet Inc.', 'NASDAQ', 'Stock', '2004-08-19', false],
  ['META', 'Meta Platforms Inc.', 'NASDAQ', 'Stock', '2012-05-18', false],
  ['TSLA', 'Tesla Inc.', 'NASDAQ', 'Stock', '2010-06-29', false],
  ['JPM', 'JPMorgan Chase & Co.', 'NYSE', 'Stock', '1980-01-02', false],
  ['KO', 'The Coca-Cola Company', 'NYSE', 'Stock', '1980-01-02', false],
  ['XOM', 'Exxon Mobil Corporation', 'NYSE', 'Stock', '1980-01-02', false],
  ['SPY', 'SPDR S&P 500 ETF Trust', 'NYSE Arca', 'ETF', '1993-01-29', true],
  ['QQQ', 'Invesco QQQ Trust', 'NASDAQ', 'ETF', '1999-03-10', false],
] as const;
const futures = [
  ['ES', 'E-mini S&P 500 continuous', 'CME', '1997-09-09', true, true],
  ['NQ', 'E-mini Nasdaq 100 continuous', 'CME', '1999-06-21', true, true],
  ['6E', 'Euro FX continuous', 'CME', '1999-01-04', true, true],
  ['YM', 'E-mini Dow continuous', 'CBOT', '2002-04-05', true, false],
  ['ZB', 'US Treasury Bond continuous', 'CBOT', '1990-01-02', true, false],
  ['CL', 'Crude Oil continuous', 'NYMEX', '1990-01-02', true, false],
  ['GC', 'Gold continuous', 'COMEX', '1990-01-02', true, false],
  ['ESZ26', 'E-mini S&P 500 December 2026', 'CME', '2025-12-19', false, false],
  ['NQZ26', 'E-mini Nasdaq 100 December 2026', 'CME', '2025-12-19', false, false],
  ['CLZ26', 'Crude Oil December 2026', 'NYMEX', '2025-12-19', false, false],
] as const;
export const sqCatalogues: Record<SQProvider, SQTicker[]> = {
  equity: equity.map(([ticker, name, exchange, type, dataFrom, free]) => ({ ticker, name, exchange, type, dataFrom, free, continuous: false, timezone: 'America/New_York' })),
  futures: futures.map(([ticker, name, exchange, dataFrom, continuous, free]) => ({ ticker, name, exchange, dataFrom, continuous, free, type: 'Futures', timezone: 'America/Chicago' })),
};
export function sqExchanges(provider: SQProvider) { return [...new Set(sqCatalogues[provider].map(row => row.exchange))]; }
export function sqSubscription(provider: SQProvider, profile: SQProfile) { return { eodSubscriptionActive: profile === 'Full', minuteSubscriptionActive: profile === 'Full', freeSymbols: sqCatalogues[provider].filter(row => row.free).map(row => row.ticker) }; }
export function sqAllowed(ticker: SQTicker, profile: SQProfile) { return profile === 'Full' || ticker.free; }
export function validateSQConfig(config: SQConfig, provider: SQProvider) {
  if (!config || !['equity', 'futures'].includes(provider) || typeof config.symbols !== 'string' || config.symbols.length > 10000 || typeof config.postfix !== 'string' || config.postfix.length > 100 || typeof config.exchange !== 'string' || (config.exchange && !sqExchanges(provider).includes(config.exchange))) throw new Error('Invalid search or exchange settings.');
  if (['searchInTicker', 'searchInName', 'exact', 'onlyContFutures'].some(key => typeof config[key as keyof SQConfig] !== 'boolean')) throw new Error('Invalid search options.');
  if (!['start', 'end'].includes(config.barType) || ![0, 1, 2].includes(config.timezoneType) || !Number.isInteger(config.timezoneShift) || config.timezoneShift < -23 || config.timezoneShift > 23 || !timezones.some(([id]) => id === config.timezone)) throw new Error('Choose a valid bar type and timezone; fixed shift must be an integer from -23 to 23 hours.');
}
export function lookupSQ(provider: SQProvider, config: SQConfig): SQTicker[] {
  validateSQConfig(config, provider);
  if (!config.searchInTicker && !config.searchInName) throw new Error('Enable Search in ticker or Search in name.');
  const terms = config.symbols.split(/[,;\r\n]+/).map(value => value.trim().toLowerCase()).filter(Boolean);
  return sqCatalogues[provider].filter(row => (!config.exchange || row.exchange === config.exchange) && (provider !== 'futures' || !config.onlyContFutures || row.continuous)
    && (!terms.length || terms.some(term => (config.searchInTicker && (config.exact ? row.ticker.toLowerCase() === term : row.ticker.toLowerCase().includes(term))) || (config.searchInName && row.name.toLowerCase().includes(term)))));
}
export interface SQDefinition { id: string; provider: SQProvider; symbol: string; underlying: string; instrument: string; source: string; broker: string; brokerName: string; category: string; timeframe: string; availableTimeframes: string[]; timezone: string; timezoneType: 0 | 1 | 2; timezoneShift: number; barType: 'start' | 'end'; from: string; to: string; bars: number; availableFrom: string }
export function planSQAdd(provider: SQProvider, config: SQConfig, tickers: string[], agreed: boolean, profile: SQProfile, existing: string[]): SQDefinition[] {
  validateSQConfig(config, provider);
  if (!agreed) throw new Error('Please read and agree to HaruQuantAI Data Usage Conditions');
  if (!tickers.length) throw new Error('No tickers selected');
  if (tickers.length > 1000 || new Set(tickers).size !== tickers.length) throw new Error('Select up to 1,000 distinct tickers.');
  const found = lookupSQ(provider, config); const names = [...existing];
  return tickers.map(ticker => {
    const row = found.find(item => item.ticker === ticker);
    if (!row || !sqAllowed(row, profile)) throw new Error(`${ticker} is not available with the current mock subscription or search.`);
    const symbol = ticker + config.postfix; validateName(symbol, names); names.push(symbol);
    const availableTimeframes = profile === 'Full' ? ['M1', 'D1'] : ['D1'];
    const timezone = config.timezoneType === 2 ? row.timezone : config.timezoneType === 1 ? config.timezone : `Exchange ${config.timezoneShift >= 0 ? '+' : ''}${config.timezoneShift}h`;
    return { id: `sq:${provider}:${symbol}`, provider, symbol, underlying: ticker, instrument: ticker, source: sourceLabel(provider), broker: '-1', brokerName: 'Default', category: row.type, timeframe: '—', availableTimeframes, timezone, timezoneType: config.timezoneType, timezoneShift: config.timezoneShift, barType: config.barType, from: '', to: '', bars: 0, availableFrom: row.dataFrom };
  });
}

// Source: both providers add/dataUsageConditionsPopup.html.
export const sqUsageConditions = [
  "The data provided under this subscription shall not constitute a forecast of the market value of any instruments at any future point either, and is not an investment advice or recommendation in any form.",
  "The usage of data provided under this subscription is limited to HaruQuantAI platform. Data cannot be exported or extracted to be used externally.",
  "DISCLAIMER OF WARRANTY. THE DATA AND ITS UNDERLAYING DATA SYSTEM IS IN CONSTANT DEVELOPMENT AND IS PROVIDED \"AS IS\", \"AS AVAILABLE\", \"WITH ALL ITS FAULTS\", WITHOUT WARRANTY OF ANY KIND, INCLUDING WITHOUT LIMITATION AND QUALIFICATION THE WARRANTIES OF ACCURACY, FUNCTIONALITY, PERFORMANCE, MERCHANDABILITY, SYSTEM INTEGRATION, DATA ACCURACY OR FITNESS FOR ANY PARTICULAR PURPOSE AND NON-INFRINGEMENT AND ANY WARRANTIES ARISING FROM TRADE USAGE, COURSE OF DELING OR COURSE OF PERFORMANCE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE DATA IS BORNE BY YOU.",
  "LIMITATION OF LIABILITY. UNDER NO CIRCUMSTANCES AND UNDER NO LEGAL THEORY, TORT, CONTRACT, OR OTHERWISE, SHALL HaruQuantAI OR ITS SUPPLIERS OR RESELLERS BE LIABLE TO YOU OR ANY OTHER PERSON FOR ANY INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL OR PUNITIVE DAMAGES OF ANY CHARACTER INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF GOODWILL, WORK STOPPAGE, COMPUTER FAILURE OR MALFUNCTION, OR ANY AND ALL OTHER COMMERCIAL DAMAGES OR LOSSES. IN NO EVENT WILL AUTHOR BE LIABLE FOR ANY DAMAGES IN EXCESS OF AUTHOR'S LIST PRICE FOR A LICENSE TO THE SOFTWARE, EVEN IF AUTHOR SHALL HAVE BEEN INFORMED OF THE POSSIBILITY OF SUCH DAMAGES, OR FOR ANY CLAIM BY ANY OTHER PARTY. THIS LIMITATION OF LIABILITY SHALL NOT APPLY TO LIABILITY FOR DEATH OR PERSONAL INJURY TO THE EXTENT APPLICABLE LAW PROHIBITS SUCH LIMITATION. FURTHERMORE, SOME STATES DO NOT ALLOW THE EXCLUSION OR LIMITATION OF INCIDENTAL OR CONSEQUENTIAL DAMAGES, SO THIS LIMITATION AND EXCLUSION MAY NOT APPLY TO YOU."
];
