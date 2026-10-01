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
export function validateSQConfig(config: SQConfig, provider: SQProvider) {
  if (!config || !['equity', 'futures'].includes(provider) || typeof config.symbols !== 'string' || config.symbols.length > 10000 || typeof config.postfix !== 'string' || config.postfix.length > 100 || typeof config.exchange !== 'string') throw new Error('Invalid search or exchange settings.');
  if (['searchInTicker', 'searchInName', 'exact', 'onlyContFutures'].some(key => typeof config[key as keyof SQConfig] !== 'boolean')) throw new Error('Invalid search options.');
  if (!['start', 'end'].includes(config.barType) || ![0, 1, 2].includes(config.timezoneType) || !Number.isInteger(config.timezoneShift) || config.timezoneShift < -23 || config.timezoneShift > 23 || !timezones.some(([id]) => id === config.timezone)) throw new Error('Choose a valid bar type and timezone; fixed shift must be an integer from -23 to 23 hours.');
}
export interface SQDefinition { id: string; provider: SQProvider; symbol: string; underlying: string; instrument: string; source: string; broker: string; brokerName: string; category: string; timeframe: string; availableTimeframes: string[]; timezone: string; timezoneType: 0 | 1 | 2; timezoneShift: number; barType: 'start' | 'end'; from: string; to: string; bars: number; availableFrom: string }
// Source: both providers add/dataUsageConditionsPopup.html.
export const sqUsageConditions = [
  "The data provided under this subscription shall not constitute a forecast of the market value of any instruments at any future point either, and is not an investment advice or recommendation in any form.",
  "The usage of data provided under this subscription is limited to HaruQuantAI platform. Data cannot be exported or extracted to be used externally.",
  "DISCLAIMER OF WARRANTY. THE DATA AND ITS UNDERLAYING DATA SYSTEM IS IN CONSTANT DEVELOPMENT AND IS PROVIDED \"AS IS\", \"AS AVAILABLE\", \"WITH ALL ITS FAULTS\", WITHOUT WARRANTY OF ANY KIND, INCLUDING WITHOUT LIMITATION AND QUALIFICATION THE WARRANTIES OF ACCURACY, FUNCTIONALITY, PERFORMANCE, MERCHANDABILITY, SYSTEM INTEGRATION, DATA ACCURACY OR FITNESS FOR ANY PARTICULAR PURPOSE AND NON-INFRINGEMENT AND ANY WARRANTIES ARISING FROM TRADE USAGE, COURSE OF DELING OR COURSE OF PERFORMANCE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE DATA IS BORNE BY YOU.",
  "LIMITATION OF LIABILITY. UNDER NO CIRCUMSTANCES AND UNDER NO LEGAL THEORY, TORT, CONTRACT, OR OTHERWISE, SHALL HaruQuantAI OR ITS SUPPLIERS OR RESELLERS BE LIABLE TO YOU OR ANY OTHER PERSON FOR ANY INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL OR PUNITIVE DAMAGES OF ANY CHARACTER INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF GOODWILL, WORK STOPPAGE, COMPUTER FAILURE OR MALFUNCTION, OR ANY AND ALL OTHER COMMERCIAL DAMAGES OR LOSSES. IN NO EVENT WILL AUTHOR BE LIABLE FOR ANY DAMAGES IN EXCESS OF AUTHOR'S LIST PRICE FOR A LICENSE TO THE SOFTWARE, EVEN IF AUTHOR SHALL HAVE BEEN INFORMED OF THE POSSIBILITY OF SUCH DAMAGES, OR FOR ANY CLAIM BY ANY OTHER PARTY. THIS LIMITATION OF LIABILITY SHALL NOT APPLY TO LIABILITY FOR DEATH OR PERSONAL INJURY TO THE EXTENT APPLICABLE LAW PROHIBITS SUCH LIMITATION. FURTHERMORE, SOME STATES DO NOT ALLOW THE EXCLUSION OR LIMITATION OF INCIDENTAL OR CONSEQUENTIAL DAMAGES, SO THIS LIMITATION AND EXCLUSION MAY NOT APPLY TO YOU."
];
